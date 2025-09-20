"""
File System Abstraction Layer for UCore Framework.

This module provides:
- Abstract base classes for file system providers
- Concrete implementations for local and in-memory file systems
- Data structures for file info and statistics
- The main FileSystem service for provider management and delegation

Classes:
    FileType: Enum for file system entry types.
    AccessMode: Enum for file access modes.
    FileInfo: Dataclass for file metadata.
    FileSystemStats: Dataclass for file system statistics.
    FileSystemProvider: Abstract base class for file system providers.
    LocalFileSystemProvider: Local disk implementation.
    InMemoryFileSystemProvider: In-memory/testing implementation.
    FileSystem: Main service for provider management and delegation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncIterator, Iterator
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from enum import Enum
import os
import shutil
import asyncio
import aiofiles
import aiofiles.os
from datetime import datetime
from loguru import logger
import tempfile
import io


class FileType(Enum):
    """Types of file system entries."""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    UNKNOWN = "unknown"


class AccessMode(Enum):
    """File access modes."""
    READ = "r"
    WRITE = "w"
    APPEND = "a"
    READ_WRITE = "r+"
    WRITE_TRUNCATE = "w+"
    APPEND_READ = "a+"


@dataclass
class FileInfo:
    """Information about a file system entry."""
    path: str
    name: str
    size: int = 0
    file_type: FileType = FileType.UNKNOWN
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    accessed_time: Optional[datetime] = None
    permissions: Optional[str] = None
    owner: Optional[str] = None
    group: Optional[str] = None
    is_hidden: bool = False
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileSystemStats:
    """Statistics about a file system."""
    total_space: int = 0
    free_space: int = 0
    used_space: int = 0
    file_count: int = 0
    directory_count: int = 0


class FileSystemProvider(ABC):
    """
    Abstract base class for file system providers.
    
    Defines the interface that all file system implementations must follow.
    """
    
    def __init__(self, name: str, root_path: Optional[str] = None):
        self.name = name
        self.root_path = root_path
        self._is_connected = False
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the file system."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the file system."""
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if a path exists."""
        pass
    
    @abstractmethod
    async def get_info(self, path: str) -> FileInfo:
        """Get information about a file or directory."""
        pass
    
    @abstractmethod
    async def list_directory(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List contents of a directory."""
        pass
    
    @abstractmethod
    async def create_directory(self, path: str, parents: bool = False) -> None:
        """Create a directory."""
        pass
    
    @abstractmethod
    async def delete(self, path: str, recursive: bool = False) -> None:
        """Delete a file or directory."""
        pass
    
    @abstractmethod
    async def copy(self, source: str, destination: str) -> None:
        """Copy a file or directory."""
        pass
    
    @abstractmethod
    async def move(self, source: str, destination: str) -> None:
        """Move/rename a file or directory."""
        pass
    
    @abstractmethod
    async def read_file(self, path: str, encoding: Optional[str] = None) -> Union[str, bytes]:
        """Read the contents of a file."""
        pass
    
    @abstractmethod
    async def write_file(self, path: str, content: Union[str, bytes], 
                        encoding: Optional[str] = None, append: bool = False) -> None:
        """Write content to a file."""
        pass
    
    @abstractmethod
    async def open_file(self, path: str, mode: AccessMode = AccessMode.READ) -> Any:
        """Open a file for reading/writing."""
        pass
    
    @abstractmethod
    async def get_stats(self, path: Optional[str] = None) -> FileSystemStats:
        """Get file system statistics."""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if the provider is connected."""
        return self._is_connected


class LocalFileSystemProvider(FileSystemProvider):
    """
    Local file system provider that works with the local disk.
    """
    
    def __init__(self, root_path: Optional[str] = None):
        super().__init__("local", root_path)
        self.root_path = Path(root_path) if root_path else Path.cwd()
    
    async def connect(self) -> None:
        """Connect to the local file system."""
        if not self.root_path.exists():
            raise FileNotFoundError(f"Root path does not exist: {self.root_path}")
        self._is_connected = True
        logger.info(f"Connected to local file system at {self.root_path}")
    
    async def disconnect(self) -> None:
        """Disconnect from the local file system."""
        self._is_connected = False
        logger.info("Disconnected from local file system")
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the root path."""
        if Path(path).is_absolute():
            return Path(path)
        return self.root_path / path
    
    async def exists(self, path: str) -> bool:
        """Check if a path exists."""
        resolved_path = self._resolve_path(path)
        return await aiofiles.os.path.exists(str(resolved_path))
    
    async def get_info(self, path: str) -> FileInfo:
        """Get information about a file or directory."""
        resolved_path = self._resolve_path(path)
        
        if not await self.exists(str(resolved_path)):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        stat = await aiofiles.os.stat(str(resolved_path))
        
        # Determine file type
        if resolved_path.is_file():
            file_type = FileType.FILE
        elif resolved_path.is_dir():
            file_type = FileType.DIRECTORY
        elif resolved_path.is_symlink():
            file_type = FileType.SYMLINK
        else:
            file_type = FileType.UNKNOWN
        
        return FileInfo(
            path=str(resolved_path),
            name=resolved_path.name,
            size=stat.st_size,
            file_type=file_type,
            created_time=datetime.fromtimestamp(stat.st_ctime),
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            accessed_time=datetime.fromtimestamp(stat.st_atime),
            permissions=oct(stat.st_mode)[-3:],
            is_hidden=resolved_path.name.startswith('.')
        )
    
    async def list_directory(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List contents of a directory."""
        resolved_path = self._resolve_path(path)
        
        if not await aiofiles.os.path.isdir(str(resolved_path)):
            raise NotADirectoryError(f"Path is not a directory: {path}")
        
        results = []
        
        if recursive:
            for root, dirs, files in os.walk(str(resolved_path)):
                # Add directories
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        info = await self.get_info(str(dir_path))
                        results.append(info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for directory {dir_path}: {e}")
                
                # Add files
                for file_name in files:
                    file_path = Path(root) / file_name
                    try:
                        info = await self.get_info(str(file_path))
                        results.append(info)
                    except Exception as e:
                        logger.warning(f"Failed to get info for file {file_path}: {e}")
        else:
            for entry in resolved_path.iterdir():
                try:
                    info = await self.get_info(str(entry))
                    results.append(info)
                except Exception as e:
                    logger.warning(f"Failed to get info for {entry}: {e}")
        
        return results
    
    async def create_directory(self, path: str, parents: bool = False) -> None:
        """Create a directory."""
        resolved_path = self._resolve_path(path)
        
        try:
            if parents:
                await aiofiles.os.makedirs(str(resolved_path), exist_ok=True)
            else:
                await aiofiles.os.mkdir(str(resolved_path))
        except Exception as e:
            raise OSError(f"Failed to create directory {path}: {e}")
    
    async def delete(self, path: str, recursive: bool = False) -> None:
        """Delete a file or directory."""
        resolved_path = self._resolve_path(path)
        
        if not await self.exists(str(resolved_path)):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        try:
            if resolved_path.is_file():
                await aiofiles.os.remove(str(resolved_path))
            elif resolved_path.is_dir():
                if recursive:
                    await asyncio.get_event_loop().run_in_executor(
                        None, shutil.rmtree, str(resolved_path)
                    )
                else:
                    await aiofiles.os.rmdir(str(resolved_path))
        except Exception as e:
            raise OSError(f"Failed to delete {path}: {e}")
    
    async def copy(self, source: str, destination: str) -> None:
        """Copy a file or directory."""
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        if not await self.exists(str(source_path)):
            raise FileNotFoundError(f"Source path does not exist: {source}")
        
        try:
            if source_path.is_file():
                await asyncio.get_event_loop().run_in_executor(
                    None, shutil.copy2, str(source_path), str(dest_path)
                )
            elif source_path.is_dir():
                await asyncio.get_event_loop().run_in_executor(
                    None, shutil.copytree, str(source_path), str(dest_path)
                )
        except Exception as e:
            raise OSError(f"Failed to copy {source} to {destination}: {e}")
    
    async def move(self, source: str, destination: str) -> None:
        """Move/rename a file or directory."""
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        if not await self.exists(str(source_path)):
            raise FileNotFoundError(f"Source path does not exist: {source}")
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.move, str(source_path), str(dest_path)
            )
        except Exception as e:
            raise OSError(f"Failed to move {source} to {destination}: {e}")
    
    async def read_file(self, path: str, encoding: Optional[str] = None) -> Union[str, bytes]:
        """Read the contents of a file."""
        resolved_path = self._resolve_path(path)
        
        if not await self.exists(str(resolved_path)):
            raise FileNotFoundError(f"File does not exist: {path}")
        
        try:
            if encoding:
                async with aiofiles.open(str(resolved_path), 'r', encoding=encoding) as f:
                    return await f.read()
            else:
                async with aiofiles.open(str(resolved_path), 'rb') as f:
                    return await f.read()
        except Exception as e:
            raise OSError(f"Failed to read file {path}: {e}")
    
    async def write_file(self, path: str, content: Union[str, bytes], 
                        encoding: Optional[str] = None, append: bool = False) -> None:
        """Write content to a file."""
        resolved_path = self._resolve_path(path)
        
        # Create parent directories if needed
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if isinstance(content, bytes):
                mode = 'ab' if append else 'wb'
                async with aiofiles.open(str(resolved_path), mode) as f:
                    await f.write(content)
            else:
                mode = 'a' if append else 'w'
                async with aiofiles.open(str(resolved_path), mode, encoding=encoding or 'utf-8') as f:
                    await f.write(content)
        except Exception as e:
            raise OSError(f"Failed to write file {path}: {e}")
    
    async def open_file(self, path: str, mode: AccessMode = AccessMode.READ):
        """Open a file for reading/writing."""
        resolved_path = self._resolve_path(path)
        
        # Create parent directories for write modes
        if mode in [AccessMode.WRITE, AccessMode.WRITE_TRUNCATE, AccessMode.APPEND, AccessMode.APPEND_READ]:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        return aiofiles.open(str(resolved_path), mode.value)
    
    async def get_stats(self, path: Optional[str] = None) -> FileSystemStats:
        """Get file system statistics."""
        target_path = self._resolve_path(path) if path else self.root_path
        
        try:
            # Platform-specific disk space calculation
            import platform
            
            if platform.system() == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(target_path)),
                    ctypes.pointer(free_bytes),
                    ctypes.pointer(total_bytes),
                    None
                )
                total_space = total_bytes.value
                free_space = free_bytes.value
                used_space = total_space - free_space
            else:
                # Unix-like systems
                import os as regular_os
                stat = regular_os.statvfs(str(target_path))
                total_space = stat.f_frsize * stat.f_blocks
                free_space = stat.f_frsize * stat.f_available
                used_space = total_space - free_space
            
            # Count files and directories (non-recursive for performance)
            file_count = 0
            directory_count = 0
            
            if target_path.is_dir():
                for entry in target_path.iterdir():
                    if entry.is_file():
                        file_count += 1
                    elif entry.is_dir():
                        directory_count += 1
            
            return FileSystemStats(
                total_space=total_space,
                free_space=free_space,
                used_space=used_space,
                file_count=file_count,
                directory_count=directory_count
            )
        except Exception as e:
            logger.warning(f"Failed to get file system stats: {e}")
            return FileSystemStats()


class InMemoryFileSystemProvider(FileSystemProvider):
    """
    In-memory file system provider for testing and temporary storage.
    """
    
    def __init__(self, name: str = "memory"):
        super().__init__(name)
        self._files: Dict[str, Union[str, bytes]] = {}
        self._directories: set = {"/"}
        self._metadata: Dict[str, FileInfo] = {}
    
    async def connect(self) -> None:
        """Connect to the in-memory file system."""
        self._is_connected = True
        logger.info("Connected to in-memory file system")
    
    async def disconnect(self) -> None:
        """Disconnect and clear the in-memory file system."""
        self._files.clear()
        self._directories.clear()
        self._metadata.clear()
        self._is_connected = False
        logger.info("Disconnected from in-memory file system")
    
    def _normalize_path(self, path: str) -> str:
        """Normalize a path for consistent storage."""
        return str(PurePath(path).as_posix())
    
    async def exists(self, path: str) -> bool:
        """Check if a path exists."""
        normalized = self._normalize_path(path)
        return normalized in self._files or normalized in self._directories
    
    async def get_info(self, path: str) -> FileInfo:
        """Get information about a file or directory."""
        normalized = self._normalize_path(path)
        
        if normalized not in self._files and normalized not in self._directories:
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if normalized in self._metadata:
            return self._metadata[normalized]
        
        # Create basic info
        file_type = FileType.FILE if normalized in self._files else FileType.DIRECTORY
        size = len(self._files.get(normalized, b"")) if file_type == FileType.FILE else 0
        
        info = FileInfo(
            path=normalized,
            name=PurePath(normalized).name,
            size=size,
            file_type=file_type,
            created_time=datetime.now(),
            modified_time=datetime.now(),
            accessed_time=datetime.now()
        )
        
        self._metadata[normalized] = info
        return info
    
    async def list_directory(self, path: str, recursive: bool = False) -> List[FileInfo]:
        """List contents of a directory."""
        normalized = self._normalize_path(path)
        
        if normalized not in self._directories:
            raise NotADirectoryError(f"Path is not a directory: {path}")
        
        results = []
        prefix = normalized.rstrip('/') + '/'
        
        # Find direct children
        children = set()
        
        # Check files
        for file_path in self._files:
            if file_path.startswith(prefix):
                relative = file_path[len(prefix):]
                if '/' not in relative or recursive:
                    children.add(file_path)
        
        # Check directories
        for dir_path in self._directories:
            if dir_path.startswith(prefix) and dir_path != normalized:
                relative = dir_path[len(prefix):]
                if '/' not in relative.rstrip('/') or recursive:
                    children.add(dir_path)
        
        # Get info for each child
        for child in children:
            try:
                info = await self.get_info(child)
                results.append(info)
            except Exception as e:
                logger.warning(f"Failed to get info for {child}: {e}")
        
        return results
    
    async def create_directory(self, path: str, parents: bool = False) -> None:
        """Create a directory."""
        normalized = self._normalize_path(path)
        
        if parents:
            # Create all parent directories
            parts = PurePath(normalized).parts
            for i in range(1, len(parts) + 1):
                parent_path = str(PurePath(*parts[:i]))
                if parent_path not in self._directories:
                    self._directories.add(parent_path)
        else:
            # Check parent exists
            parent = str(PurePath(normalized).parent)
            if parent != normalized and parent not in self._directories:
                raise FileNotFoundError(f"Parent directory does not exist: {parent}")
            self._directories.add(normalized)
    
    async def delete(self, path: str, recursive: bool = False) -> None:
        """Delete a file or directory."""
        normalized = self._normalize_path(path)
        
        if not await self.exists(normalized):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if normalized in self._files:
            del self._files[normalized]
            if normalized in self._metadata:
                del self._metadata[normalized]
        elif normalized in self._directories:
            # Check if directory is empty (unless recursive)
            if not recursive:
                children = await self.list_directory(normalized)
                if children:
                    raise OSError(f"Directory not empty: {path}")
            
            # Remove directory and contents
            to_remove = []
            for file_path in self._files:
                if file_path.startswith(normalized + '/'):
                    to_remove.append(file_path)
            
            for file_path in to_remove:
                del self._files[file_path]
                if file_path in self._metadata:
                    del self._metadata[file_path]
            
            dirs_to_remove = []
            for dir_path in self._directories:
                if dir_path.startswith(normalized + '/') or dir_path == normalized:
                    dirs_to_remove.append(dir_path)
            
            for dir_path in dirs_to_remove:
                self._directories.discard(dir_path)
                if dir_path in self._metadata:
                    del self._metadata[dir_path]
    
    async def copy(self, source: str, destination: str) -> None:
        """Copy a file or directory."""
        source_normalized = self._normalize_path(source)
        dest_normalized = self._normalize_path(destination)
        
        if not await self.exists(source_normalized):
            raise FileNotFoundError(f"Source path does not exist: {source}")
        
        if source_normalized in self._files:
            # Copy file
            self._files[dest_normalized] = self._files[source_normalized]
            if source_normalized in self._metadata:
                info = self._metadata[source_normalized]
                self._metadata[dest_normalized] = FileInfo(
                    path=dest_normalized,
                    name=PurePath(dest_normalized).name,
                    size=info.size,
                    file_type=info.file_type,
                    created_time=datetime.now(),
                    modified_time=info.modified_time
                )
        else:
            # Copy directory (recursive)
            self._directories.add(dest_normalized)
            
            # Copy all files in the directory
            prefix = source_normalized.rstrip('/') + '/'
            dest_prefix = dest_normalized.rstrip('/') + '/'
            
            for file_path in self._files:
                if file_path.startswith(prefix):
                    relative_path = file_path[len(prefix):]
                    new_file_path = dest_prefix + relative_path
                    self._files[new_file_path] = self._files[file_path]
            
            # Copy subdirectories
            for dir_path in self._directories:
                if dir_path.startswith(prefix):
                    relative_path = dir_path[len(prefix):]
                    new_dir_path = dest_prefix + relative_path
                    self._directories.add(new_dir_path)
    
    async def move(self, source: str, destination: str) -> None:
        """Move/rename a file or directory."""
        await self.copy(source, destination)
        await self.delete(source, recursive=True)
    
    async def read_file(self, path: str, encoding: Optional[str] = None) -> Union[str, bytes]:
        """Read the contents of a file."""
        normalized = self._normalize_path(path)
        
        if normalized not in self._files:
            raise FileNotFoundError(f"File does not exist: {path}")
        
        content = self._files[normalized]
        
        if encoding and isinstance(content, bytes):
            return content.decode(encoding)
        elif not encoding and isinstance(content, str):
            return content.encode('utf-8')
        
        return content
    
    async def write_file(self, path: str, content: Union[str, bytes], 
                        encoding: Optional[str] = None, append: bool = False) -> None:
        """Write content to a file."""
        normalized = self._normalize_path(path)
        
        # Create parent directories
        parent = str(PurePath(normalized).parent)
        if parent != normalized:
            await self.create_directory(parent, parents=True)
        
        if append and normalized in self._files:
            existing = self._files[normalized]
            if isinstance(existing, str) and isinstance(content, str):
                content = existing + content
            elif isinstance(existing, bytes) and isinstance(content, bytes):
                content = existing + content
            elif isinstance(existing, str) and isinstance(content, bytes):
                content = existing + content.decode(encoding or 'utf-8')
            elif isinstance(existing, bytes) and isinstance(content, str):
                content = existing + content.encode(encoding or 'utf-8')
        
        self._files[normalized] = content
        
        # Update metadata
        size = len(content) if isinstance(content, (str, bytes)) else 0
        self._metadata[normalized] = FileInfo(
            path=normalized,
            name=PurePath(normalized).name,
            size=size,
            file_type=FileType.FILE,
            created_time=datetime.now() if normalized not in self._metadata else self._metadata[normalized].created_time,
            modified_time=datetime.now()
        )
    
    async def open_file(self, path: str, mode: AccessMode = AccessMode.READ):
        """Open a file for reading/writing (returns a file-like object)."""
        normalized = self._normalize_path(path)
        
        if mode == AccessMode.READ:
            if normalized not in self._files:
                raise FileNotFoundError(f"File does not exist: {path}")
            content = self._files[normalized]
            return io.StringIO(content) if isinstance(content, str) else io.BytesIO(content)
        else:
            # For write modes, create a StringIO/BytesIO that will update the file on close
            class InMemoryFile:
                def __init__(self, provider, file_path, mode):
                    self.provider = provider
                    self.file_path = file_path
                    self.mode = mode
                    self.buffer = io.StringIO() if 'b' not in mode.value else io.BytesIO()
                
                async def write(self, data):
                    return self.buffer.write(data)
                
                async def read(self, size=-1):
                    return self.buffer.read(size)
                
                async def close(self):
                    content = self.buffer.getvalue()
                    await self.provider.write_file(self.file_path, content)
                    self.buffer.close()
                
                async def __aenter__(self):
                    return self
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    await self.close()
            
            return InMemoryFile(self, normalized, mode)
    
    async def get_stats(self, path: Optional[str] = None) -> FileSystemStats:
        """Get file system statistics."""
        file_count = len(self._files)
        directory_count = len(self._directories)
        
        total_size = sum(len(content) if isinstance(content, (str, bytes)) else 0 
                        for content in self._files.values())
        
        return FileSystemStats(
            total_space=total_size * 10,  # Simulate available space
            free_space=total_size * 9,
            used_space=total_size,
            file_count=file_count,
            directory_count=directory_count
        )


class FileSystem:
    """
    Main file system service that delegates to the appropriate provider.
    """
    
    def __init__(self, default_provider: Optional[FileSystemProvider] = None):
        self.providers: Dict[str, FileSystemProvider] = {}
        self.default_provider = default_provider or LocalFileSystemProvider()
        self.providers[self.default_provider.name] = self.default_provider
    
    def add_provider(self, provider: FileSystemProvider) -> None:
        """Add a file system provider."""
        self.providers[provider.name] = provider
        logger.info(f"Added file system provider: {provider.name}")
    
    def remove_provider(self, name: str) -> None:
        """Remove a file system provider."""
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Removed file system provider: {name}")
    
    def get_provider(self, name: Optional[str] = None) -> FileSystemProvider:
        """Get a file system provider by name."""
        if name is None:
            return self.default_provider
        
        provider = self.providers.get(name)
        if provider is None:
            from ucore_framework.core.exceptions import ResourceError
            raise ResourceError(
                message=f"Unknown file system provider: {name}",
                code="FS_PROVIDER_UNKNOWN"
            )
        
        return provider
    
    async def exists(self, path: str, provider: Optional[str] = None) -> bool:
        """Check if a path exists."""
        fs = self.get_provider(provider)
        return await fs.exists(path)
    
    async def get_info(self, path: str, provider: Optional[str] = None) -> FileInfo:
        """Get information about a file or directory."""
        fs = self.get_provider(provider)
        return await fs.get_info(path)
    
    async def list_directory(self, path: str, recursive: bool = False, 
                           provider: Optional[str] = None) -> List[FileInfo]:
        """List contents of a directory."""
        fs = self.get_provider(provider)
        return await fs.list_directory(path, recursive)
    
    async def create_directory(self, path: str, parents: bool = False, 
                             provider: Optional[str] = None) -> None:
        """Create a directory."""
        fs = self.get_provider(provider)
        await fs.create_directory(path, parents)
    
    async def delete(self, path: str, recursive: bool = False, 
                    provider: Optional[str] = None) -> None:
        """Delete a file or directory."""
        fs = self.get_provider(provider)
        await fs.delete(path, recursive)
    
    async def copy(self, source: str, destination: str, 
                  source_provider: Optional[str] = None,
                  dest_provider: Optional[str] = None) -> None:
        """Copy a file or directory."""
        source_fs = self.get_provider(source_provider)
        dest_fs = self.get_provider(dest_provider)
        
        if source_fs == dest_fs:
            await source_fs.copy(source, destination)
        else:
            # Cross-provider copy
            await self._cross_provider_copy(source_fs, source, dest_fs, destination)
    
    async def move(self, source: str, destination: str,
                  source_provider: Optional[str] = None,
                  dest_provider: Optional[str] = None) -> None:
        """Move/rename a file or directory."""
        source_fs = self.get_provider(source_provider)
        dest_fs = self.get_provider(dest_provider)
        
        if source_fs == dest_fs:
            await source_fs.move(source, destination)
        else:
            # Cross-provider move
            await self._cross_provider_copy(source_fs, source, dest_fs, destination)
            await source_fs.delete(source, recursive=True)
    
    async def read_file(self, path: str, encoding: Optional[str] = None,
                       provider: Optional[str] = None) -> Union[str, bytes]:
        """Read the contents of a file."""
        fs = self.get_provider(provider)
        return await fs.read_file(path, encoding)
    
    async def write_file(self, path: str, content: Union[str, bytes], 
                        encoding: Optional[str] = None, append: bool = False,
                        provider: Optional[str] = None) -> None:
        """Write content to a file."""
        fs = self.get_provider(provider)
        await fs.write_file(path, content, encoding, append)
    
    async def _cross_provider_copy(self, source_fs: FileSystemProvider, source_path: str,
                                  dest_fs: FileSystemProvider, dest_path: str) -> None:
        """Copy files between different providers."""
        info = await source_fs.get_info(source_path)
        
        if info.file_type == FileType.FILE:
            content = await source_fs.read_file(source_path)
            await dest_fs.write_file(dest_path, content)
        elif info.file_type == FileType.DIRECTORY:
            await dest_fs.create_directory(dest_path, parents=True)
            children = await source_fs.list_directory(source_path)
            
            for child in children:
                child_name = Path(child.path).name
                child_source = str(Path(source_path) / child_name)
                child_dest = str(Path(dest_path) / child_name)
                await self._cross_provider_copy(source_fs, child_source, dest_fs, child_dest)


# Global file system instance
_global_filesystem: Optional[FileSystem] = None


def get_filesystem() -> FileSystem:
    """Get the global file system instance."""
    global _global_filesystem
    if _global_filesystem is None:
        _global_filesystem = FileSystem()
    return _global_filesystem


def set_default_provider(provider: FileSystemProvider) -> None:
    """Set the default file system provider."""
    fs = get_filesystem()
    fs.default_provider = provider
    fs.providers[provider.name] = provider
