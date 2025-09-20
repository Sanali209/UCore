import pytest
from ucore_framework.core.resource.types.file import InMemoryFileSystemProvider

@pytest.fixture
async def mem_fs():
    fs = InMemoryFileSystemProvider()
    await fs.connect()
    yield fs

@pytest.mark.asyncio
async def test_write_and_read_file(mem_fs):
    path = "/foo/bar.txt"
    content = "hello world"
    await mem_fs.write_file(path, content)
    read_content = await mem_fs.read_file(path)
    assert await mem_fs.exists(path) is True
    assert read_content == content

@pytest.mark.asyncio
async def test_create_and_list_directory(mem_fs):
    dir_path = "/foo"
    file_path = "/foo/bar.txt"
    await mem_fs.create_directory(dir_path)
    await mem_fs.write_file(file_path, "abc")
    dir_contents = await mem_fs.list_directory(dir_path)
    assert len(dir_contents) == 1
    assert dir_contents[0].name == "bar.txt"

@pytest.mark.asyncio
async def test_delete_file(mem_fs):
    path = "/foo/bar.txt"
    await mem_fs.write_file(path, "to be deleted")
    await mem_fs.delete(path)
    assert await mem_fs.exists(path) is False
