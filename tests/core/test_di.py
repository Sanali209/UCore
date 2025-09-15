# tests/test_di.py
import unittest
import sys

from framework.core.di import Container, Scope, CircularDependencyError, NoProviderError

class ServiceA:
    pass

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

class ServiceC:
    def __init__(self, service_d: 'ServiceD'):
        self.service_d = service_d

class ServiceD:
    def __init__(self, service_c: ServiceC):
        self.service_c = service_c

class TestDIContainer(unittest.TestCase):

    def setUp(self):
        self.container = Container()

    def test_register_and_get_transient(self):
        """Tests that transient dependencies are new instances each time."""
        self.container.register(ServiceA, scope=Scope.TRANSIENT)
        instance1 = self.container.get(ServiceA)
        instance2 = self.container.get(ServiceA)
        self.assertIsInstance(instance1, ServiceA)
        self.assertIsNot(instance1, instance2)

    def test_register_and_get_singleton(self):
        """Tests that singleton dependencies are the same instance each time."""
        self.container.register(ServiceA, scope=Scope.SINGLETON)
        instance1 = self.container.get(ServiceA)
        instance2 = self.container.get(ServiceA)
        self.assertIsInstance(instance1, ServiceA)
        self.assertIs(instance1, instance2)

    def test_dependency_injection(self):
        """Tests that the container can inject dependencies into constructors."""
        self.container.register(ServiceA, scope=Scope.SINGLETON)
        self.container.register(ServiceB, scope=Scope.TRANSIENT)
        
        b_instance = self.container.get(ServiceB)
        a_instance = self.container.get(ServiceA)
        
        self.assertIsInstance(b_instance, ServiceB)
        self.assertIsInstance(b_instance.service_a, ServiceA)
        self.assertIs(b_instance.service_a, a_instance)

    def test_get_unregistered_dependency_raises_error(self):
        """Tests that requesting an unregistered dependency raises NoProviderError."""
        with self.assertRaises(NoProviderError):
            self.container.get(ServiceA)

    def test_circular_dependency_raises_error(self):
        """Tests that a circular dependency raises CircularDependencyError."""
        self.container.register(ServiceC)
        self.container.register(ServiceD)
        
        with self.assertRaises(CircularDependencyError):
            self.container.get(ServiceC)

    def test_register_instance(self):
        """Tests that a pre-existing instance can be registered as a singleton."""
        instance_a = ServiceA()
        self.container.register_instance(instance_a)
        
        resolved_instance = self.container.get(ServiceA)
        self.assertIs(instance_a, resolved_instance)

    def test_register_instance_with_dependency_type(self):
        """Tests registering an instance with an explicit dependency type."""
        class ServiceAImpl(ServiceA):
            pass
        
        instance_a = ServiceAImpl()
        self.container.register_instance(instance_a, dependency=ServiceA)
        
        resolved_instance = self.container.get(ServiceA)
        self.assertIs(instance_a, resolved_instance)

if __name__ == '__main__':
    unittest.main()
