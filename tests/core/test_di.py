import pytest
from ucore_framework.core.di import Container, Scope, NoProviderError

class ServiceA:
    pass

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

def test_singleton_scope():
    container = Container()
    container.register(ServiceA, scope=Scope.SINGLETON)
    instance1 = container.get(ServiceA)
    instance2 = container.get(ServiceA)
    assert instance1 is instance2

def test_transient_scope():
    container = Container()
    container.register(ServiceA, scope=Scope.TRANSIENT)
    instance1 = container.get(ServiceA)
    instance2 = container.get(ServiceA)
    assert instance1 is not instance2

def test_register_instance():
    container = Container()
    service_a_instance = ServiceA()
    container.register_instance(service_a_instance)
    resolved = container.get(ServiceA)
    assert resolved is service_a_instance

def test_no_provider_error():
    container = Container()
    with pytest.raises(NoProviderError):
        container.get(ServiceA)
