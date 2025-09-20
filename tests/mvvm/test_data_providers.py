import pytest
from unittest.mock import patch
from ucore_framework.mvvm.data_provider import InMemoryProvider, FileSystemProvider

def test_in_memory_provider():
    sample_data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    provider = InMemoryProvider(sample_data)
    result = provider.get_data()
    assert result == sample_data

@patch('ucore_framework.mvvm.data_provider.os')
def test_filesystem_provider(mock_os):
    mock_os.listdir.return_value = ["file1.txt", "subdir"]
    mock_os.path.isdir.side_effect = lambda path: path.endswith("subdir")
    provider = FileSystemProvider(root_path="/fake/dir")
    result = provider.get_data()
    mock_os.listdir.assert_called_with("/fake/dir")
    assert {"name": "file1.txt", "is_dir": False} in result
    assert {"name": "subdir", "is_dir": True} in result
