import pytest
from unittest.mock import Mock
from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin
from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin

def test_provisioning_provide_visible():
    mixin = DataProvisioningMixin()
    mixin.set_provision_mode("visible")
    data = [10, 20, 30, 40]
    result = mixin.provide_data(data, visible_indices=[0, 3])
    assert result == [10, 40]

def test_transformation_pipeline():
    mixin = TransformationPipelineMixin()
    def double(data): return [i * 2 for i in data]
    def add_five(data): return [i + 5 for i in data]
    mixin.add_transformation(double)
    mixin.add_transformation(add_five)
    result = mixin.transform([1, 2, 3])
    assert result == [7, 9, 11]

def test_transformation_caching():
    mixin = TransformationPipelineMixin()
    mock_transform = Mock(side_effect=lambda data: data)
    mixin.add_transformation(mock_transform)
    mixin.transform([1, 2, 3])
    mixin.transform([1, 2, 3])
    mock_transform.assert_called_once()
