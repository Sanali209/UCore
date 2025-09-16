"""
File System Resource
Provides file system operations with lifecycle management
"""

import os
import aiofiles
from framework.monitoring.logging import Logging
from typing import Any, Dict, Optional
from pathlib import Path

from ..resource import Resource, ResourceHealth, ResourceState
from ..exceptions import ResourceError, ResourceStateError


logger = Logging().get_logger(__name__)


class FileResource(Resource):
    """
    File system resource for managing file operations

    Provides async file operations with proper resource management,
    health monitoring, and error handling.
    """

    def __init__(
        self,
        name: str,
        base_path: str,
        config: Optional[Dict[str, Any]] = None,
        create_dirs: bool = True,
        ensure_permissions: bool = True,
    ):
        super().__init__(name, "file", config)

        self.base_path = Path(base_path).resolve()
        self.create_dirs = create_dirs
        self.ensure_permissions = ensure_permissions

        # Additional state
        self._is_writable = False
        self._is_readable = False

    async def _initialize(self) -> None:
        """Initialize file resource"""
        # Create directories if requested
        if self.create_dirs and not self.base_path.exists():
            try:
                self.base_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory {self.base_path}")
            except Exception as e:
                raise ResourceError(f"Cannot create directory {self.base_path}: {e}", self.name)

        # Check permissions
        if self.ensure_permissions:
            await self._check_permissions()

    async def _connect(self) -> None:
        """Establish file system connection"""
        # For file resources, connect means ensuring directory exists and is accessible
        if not self.base_path.exists():
            raise ResourceError(f"Directory {self.base_path} does not exist", self.name)

        if not self.base_path.is_dir():
            raise ResourceError(f"Path {self.base_path} is not a directory", self.name)

        await self._check_permissions()

    async def _disconnect(self) -> None:
        """Disconnect file resource"""
        # Nothing special needed for disconnect
        pass

    async def _health_check(self) -> ResourceHealth:
        """Perform health check"""
        try:
            if not self.base_path.exists():
                return ResourceHealth.UNHEALTHY

            # Check if we can list directory
            try:
                list(self.base_path.iterdir())
                self._is_readable = True
            except PermissionError:
                self._is_readable = False
                return ResourceHealth.UNHEALTHY

            # Check if we can write to directory
            if self.ensure_permissions:
                test_file = self.base_path / ".health_check"
                try:
                    test_file.write_text("health_check")
                    test_file.unlink()
                    self._is_writable = True
                except Exception:
                    self._is_writable = False
                    self._is_readable = False
                    return ResourceHealth.UNHEALTHY

            return ResourceHealth.HEALTHY
        except Exception as e:
            logger.warning(f"Health check failed for file resource {self.name}: {e}")
            return ResourceHealth.UNHEALTHY

    async def _cleanup(self) -> None:
        """Cleanup file resource"""
        # Nothing special needed for cleanup, directory remains
        pass

    async def _check_permissions(self) -> None:
        """Check and set file system permissions"""
        # Check if directory exists
        if not self.base_path.exists():
            self._is_readable = False
            self._is_writable = False
            return

        # Check readability
        try:
            list(self.base_path.iterdir())
            self._is_readable = True
        except PermissionError:
            self._is_readable = False

        # Check writability if enabled
        if self.ensure_permissions:
            test_file = self.base_path / ".perm_check"
            try:
                test_file.write_text("perm_check")
                test_file.unlink()
                self._is_writable = True
            except Exception:
                self._is_writable = False

    # File operations
    async def read_file(self, filename: str) -> str:
        """
        Read file content

        Args:
            filename: Relative path to file

        Returns:
            File content as string

        Raises:
            ResourceError: If file operations fail
        """
        if not self.is_connected:
            raise ResourceStateError(self.name, self.state.value, ResourceState.CONNECTED.value)

        file_path = self._resolve_path(filename)

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            raise ResourceError(f"Cannot read file {filename}: {e}", self.name)

    async def write_file(self, filename: str, content: str, create_dirs: bool = True) -> None:
        """
        Write content to file

        Args:
            filename: Relative path to file
            content: Content to write
            create_dirs: Whether to create parent directories

        Raises:
            ResourceError: If file operations fail
        """
        if not self.is_connected:
            raise ResourceStateError(self.name, self.state.value, ResourceState.CONNECTED.value)

        file_path = self._resolve_path(filename)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
        except Exception as e:
            raise ResourceError(f"Cannot write to file {filename}: {e}", self.name)

    async def file_exists(self, filename: str) -> bool:
        """
        Check if file exists

        Args:
            filename: Relative path to file

        Returns:
            True if file exists
        """
        file_path = self._resolve_path(filename)
        return file_path.exists()

    async def list_files(self, pattern: str = "*") -> list:
        """
        List files matching pattern

        Args:
            pattern: Glob pattern to match files

        Returns:
            List of file paths
        """
        if not self.is_connected:
            raise ResourceStateError(self.name, self.state.value, ResourceState.CONNECTED.value)

        files = []
        for path in self.base_path.rglob(pattern):
            if path.is_file():
                files.append(str(path.relative_to(self.base_path)))

        return files

    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file

        Args:
            filename: Relative path to file

        Returns:
            True if file was deleted
        """
        file_path = self._resolve_path(filename)

        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            raise ResourceError(f"Cannot delete file {filename}: {e}", self.name)

    def _resolve_path(self, filename: str) -> Path:
        """
        Resolve relative filename to absolute path

        Args:
            filename: Relative filename

        Returns:
            Absolute path

        Raises:
            ValueError: If path is outside base directory
        """
        path = (self.base_path / filename).resolve()

        # Security check: ensure path is within base directory
        if not path.is_relative_to(self.base_path):
            raise ValueError(f"Path {filename} is outside base directory")

        return path

    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics"""
        stats = super().get_stats()
        stats.update({
            "base_path": str(self.base_path),
            "is_readable": self._is_readable,
            "is_writable": self._is_writable,
            "directory_exists": self.base_path.exists(),
            "total_files": sum(1 for _ in self.base_path.rglob("*") if _.is_file()) if self.base_path.exists() else 0,
            "disk_usage": self._get_disk_usage() if self.base_path.exists() else 0,
        })
        return stats

    def _get_disk_usage(self) -> int:
        """Get total disk usage in bytes"""
        total_size = 0
        for path in self.base_path.rglob("*"):
            if path.is_file():
                try:
                    total_size += path.stat().st_size
                except OSError:
                    pass
        return total_size
