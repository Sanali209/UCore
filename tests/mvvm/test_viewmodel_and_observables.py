import pytest
from unittest.mock import Mock
from ucore_framework.mvvm.base import ViewModelBase, ObservableList

def test_viewmodel_property_changed():
    vm = ViewModelBase()
    mock_handler = Mock()
    vm.add_property_changed_handler(mock_handler)
    vm.set_property("my_prop", "new_value")
    mock_handler.assert_called_once_with("my_prop", None, "new_value")

def test_observable_list_append():
    my_list = ObservableList()
    mock_handler = Mock()
    my_list.add_handler(mock_handler)
    my_list.append("new_item")
    mock_handler.assert_called_once_with('append', 'new_item')
