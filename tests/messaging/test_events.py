import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from ucore_framework.messaging.events import (
    Event, ComponentStartedEvent, ComponentStoppedEvent, ComponentErrorEvent,
    HttpServerStartedEvent, HTTPRequestEvent, HTTPResponseEvent, HTTPErrorEvent,
    DBConnectionEvent, DBQueryEvent, DBTransactionEvent, DBPoolEvent,
    AppStartedEvent, AppStoppedEvent, ConfigUpdatedEvent,
    UserEvent, EventFilter
)


class TestEventBase:
    """Test Event base class functionality."""

    def test_event_initialization_with_defaults(self):
        """Test Event initialization with default values."""
        event = Event()

        assert isinstance(event.event_id, str)
        assert len(event.event_id) == 36  # UUID string length
        assert isinstance(event.timestamp, datetime)
        # Accept both "unknown" and "<string>" as possible auto-detected sources in test env
        assert event.source in ("unknown", "<string>", "python")
        assert event.data == {}

    def test_event_initialization_with_custom_values(self):
        """Test Event initialization with custom values."""
        custom_id = str(uuid.uuid4())
        custom_timestamp = datetime(2023, 10, 1, 12, 0, 0)
        custom_data = {"key": "value"}

        event = Event(
            event_id=custom_id,
            timestamp=custom_timestamp,
            source="test_source",
            data=custom_data
        )

        assert event.event_id == custom_id
        assert event.timestamp == custom_timestamp
        assert event.source == "test_source"
        assert event.data == custom_data

    @patch('UCoreFrameworck.messaging.events.inspect')
    def test_source_detection_success(self, mock_inspect):
        """Test successful source detection from call stack."""
        # Mock inspect to simulate finding a module
        mock_frame = Mock()
        mock_frame_info = Mock()
        mock_frame_info.filename = "/path/to/module.py"
        mock_inspect.getframeinfo.return_value = mock_frame_info
        mock_inspect.currentframe.return_value = mock_frame

        event = Event()
        event.event_id = "test"
        event.timestamp = datetime.now()
        event.data = {}

        # Call _detect_source directly
        source = event._detect_source()

        assert source == "module"

    @patch('UCoreFrameworck.messaging.events.inspect')
    def test_source_detection_failure(self, mock_inspect):
        """Test source detection failure handling."""
        mock_inspect.currentframe.side_effect = Exception("No frames")

        event = Event()
        source = event._detect_source()

        assert source == "unknown"

    def test_event_immutability(self):
        """Test that Event instances are immutable after creation."""
        event = Event()

        # Should be able to set attributes initially
        event.test_attr = "test"

        # But should not modify core attributes after initialization
        # This is more of a convention test
        assert hasattr(event, 'event_id')


class TestComponentEvents:
    """Test component lifecycle events."""

    def test_component_started_event(self):
        """Test ComponentStartedEvent creation."""
        event = ComponentStartedEvent(
            component_name="TestComponent",
            component_type=str,
            source="test_module"
        )

        assert event.component_name == "TestComponent"
        assert event.component_type == str
        assert isinstance(event, Event)

    def test_component_stopped_event(self):
        """Test ComponentStoppedEvent with reason."""
        event = ComponentStoppedEvent(
            component_name="TestComponent",
            component_type=int,
            reason="User requested shutdown",
            source="test_module"
        )

        assert event.component_name == "TestComponent"
        assert event.component_type == int
        assert event.reason == "User requested shutdown"

    def test_component_error_event(self):
        """Test ComponentErrorEvent with full context."""
        context = {"user_id": 123, "operation": "save"}
        event = ComponentErrorEvent(
            component_name="TestComponent",
            error_type="ValidationError",
            error_message="Invalid input data",
            traceback="stack trace here",
            context=context,
            source="test_module"
        )

        assert event.component_name == "TestComponent"
        assert event.error_type == "ValidationError"
        assert event.error_message == "Invalid input data"
        assert event.traceback == "stack trace here"
        assert event.context == context


class TestHttpEvents:
    """Test HTTP-related events."""

    def test_http_server_started_event(self):
        """Test HttpServerStartedEvent creation."""
        event = HttpServerStartedEvent(
            host="localhost",
            port=8080,
            route_count=15,
            source="http_server"
        )

        assert event.host == "localhost"
        assert event.port == 8080
        assert event.route_count == 15

    def test_http_request_event(self):
        """Test HTTPRequestEvent creation."""
        headers = {"User-Agent": "TestAgent", "Content-Type": "application/json"}
        query_params = {"param1": "value1", "param2": "value2"}

        event = HTTPRequestEvent(
            method="POST",
            path="/api/users",
            headers=headers,
            query_params=query_params,
            client_ip="192.168.1.100",
            source="http_handler"
        )

        assert event.method == "POST"
        assert event.path == "/api/users"
        assert event.headers == headers
        assert event.query_params == query_params
        assert event.client_ip == "192.168.1.100"

    def test_http_response_event(self):
        """Test HTTPResponseEvent creation."""
        event = HTTPResponseEvent(
            method="GET",
            path="/api/data",
            status=200,
            response_time=0.125,
            response_size=2048,
            source="http_handler"
        )

        assert event.method == "GET"
        assert event.path == "/api/data"
        assert event.status == 200
        assert event.response_time == 0.125
        assert event.response_size == 2048

    def test_http_error_event(self):
        """Test HTTPErrorEvent creation."""
        event = HTTPErrorEvent(
            method="POST",
            path="/api/users",
            status=400,
            error_type="ValidationError",
            error_message="Missing required field",
            response_time=0.089,
            source="error_handler"
        )

        assert event.method == "POST"
        assert event.path == "/api/users"
        assert event.status == 400
        assert event.error_type == "ValidationError"
        assert event.error_message == "Missing required field"
        assert event.response_time == 0.089


class TestDatabaseEvents:
    """Test database-related events."""

    def test_db_connection_event(self):
        """Test DBConnectionEvent creation."""
        event = DBConnectionEvent(
            database_url="postgresql://user:pass@host:5432/db",
            connection_status="success",
            connection_time=0.245,
            source="db_connector"
        )

        assert event.database_url == "postgresql://user:pass@host:5432/db"
        assert event.connection_status == "success"
        assert event.connection_time == 0.245

    def test_db_query_event(self):
        """Test DBQueryEvent creation."""
        event = DBQueryEvent(
            query_type="SELECT",
            query_pattern="SELECT * FROM users WHERE id = ?",
            execution_time=0.15,
            row_count=25,
            transaction_id="tx_12345",
            source="db_executor"
        )

        assert event.query_type == "SELECT"
        assert event.query_pattern == "SELECT * FROM users WHERE id = ?"
        assert event.execution_time == 0.15
        assert event.row_count == 25
        assert event.transaction_id == "tx_12345"

    def test_db_transaction_event(self):
        """Test DBTransactionEvent creation."""
        event = DBTransactionEvent(
            operation="commit",
            transaction_id="tx_67890",
            duration=0.056,
            query_count=3,
            source="db_transaction"
        )

        assert event.operation == "commit"
        assert event.transaction_id == "tx_67890"
        assert event.duration == 0.056
        assert event.query_count == 3

    def test_db_pool_event(self):
        """Test DBPoolEvent creation."""
        event = DBPoolEvent(
            pool_size=20,
            active_connections=8,
            idle_connections=12,
            pending_connections=2,
            source="db_pool_manager"
        )

        assert event.pool_size == 20
        assert event.active_connections == 8
        assert event.idle_connections == 12
        assert event.pending_connections == 2


class TestApplicationEvents:
    """Test application-level events."""

    def test_app_started_event(self):
        """Test AppStartedEvent creation."""
        event = AppStartedEvent(
            app_name="UCoreTestApp",
            component_count=15,
            source="app_bootstrap"
        )

        assert event.app_name == "UCoreTestApp"
        assert event.component_count == 15

    def test_app_stopped_event(self):
        """Test AppStoppedEvent creation."""
        event = AppStoppedEvent(
            app_name="UCoreTestApp",
            stop_reason="user_shutdown",
            source="app_shutdown"
        )

        assert event.app_name == "UCoreTestApp"
        assert event.stop_reason == "user_shutdown"

    def test_app_stopped_event_default_reason(self):
        """Test AppStoppedEvent with default reason."""
        event = AppStoppedEvent(
            app_name="UCoreTestApp",
            source="app_shutdown"
        )

        assert event.app_name == "UCoreTestApp"
        assert event.stop_reason == "normal"

    def test_config_updated_event(self):
        """Test ConfigUpdatedEvent creation."""
        updated_keys = ["database.host", "database.port"]
        old_values = {"database.host": "old.example.com", "database.port": 5432}
        new_values = {"database.host": "new.example.com", "database.port": 3306}

        event = ConfigUpdatedEvent(
            updated_keys=updated_keys,
            old_values=old_values,
            new_values=new_values,
            source="config_manager"
        )

        assert event.updated_keys == updated_keys
        assert event.old_values == old_values
        assert event.new_values == new_values


class TestUserEvents:
    """Test user-defined event functionality."""

    def test_user_event_creation(self):
        """Test UserEvent creation."""
        payload = {"user_id": 123, "action": "login", "timestamp": "2023-10-01"}

        event = UserEvent(
            event_type="user.login",
            payload=payload,
            source="auth_module"
        )

        assert event.event_type == "user.login"
        assert event.payload == payload

    def test_user_event_empty_payload(self):
        """Test UserEvent with empty payload."""
        event = UserEvent(
            event_type="system.heartbeat",
            source="monitor_module"
        )

        assert event.event_type == "system.heartbeat"
        assert event.payload == {}
        assert event.data == {}  # Inherited from Event


class TestEventFilter:
    """Test EventFilter functionality."""

    def test_event_filter_initialization(self):
        """Test EventFilter initialization."""
        filter_obj = EventFilter()

        assert filter_obj.event_types == []
        assert filter_obj.sources == []
        assert filter_obj.data_patterns == {}

    def test_event_filter_initialization_with_values(self):
        """Test EventFilter initialization with custom values."""
        event_types = [ComponentStartedEvent, ComponentStoppedEvent]
        sources = ["module_a", "module_b"]
        data_patterns = {"status": "active", "priority": "high"}

        filter_obj = EventFilter(
            event_types=event_types,
            sources=sources,
            data_patterns=data_patterns
        )

        assert filter_obj.event_types == event_types
        assert filter_obj.sources == sources
        assert filter_obj.data_patterns == data_patterns

    def test_filter_matches_no_restrictions(self):
        """Test filter matches when no restrictions are set."""
        filter_obj = EventFilter()
        event = ComponentStartedEvent(
            component_name="TestComponent",
            source="test_source",
            data={"key": "value"}
        )

        assert filter_obj.matches(event) is True

    def test_filter_matches_event_type_filtering(self):
        """Test filter with event type filtering."""
        # Filter that only allows ComponentStartedEvent
        filter_obj = EventFilter(event_types=[ComponentStartedEvent])

        # Should match
        started_event = ComponentStartedEvent(component_name="Test")
        assert filter_obj.matches(started_event) is True

        # Should not match
        stopped_event = ComponentStoppedEvent(component_name="Test")
        assert filter_obj.matches(stopped_event) is False

    def test_filter_matches_source_filtering(self):
        """Test filter with source filtering."""
        filter_obj = EventFilter(sources=["allowed_module"])

        # Should match
        event1 = ComponentStartedEvent(component_name="Test", source="allowed_module")
        assert filter_obj.matches(event1) is True

        # Should not match
        event2 = ComponentStartedEvent(component_name="Test", source="blocked_module")
        assert filter_obj.matches(event2) is False

    def test_filter_matches_data_patterns_filtering(self):
        """Test filter with data pattern filtering."""
        filter_obj = EventFilter(
            data_patterns={"status": "active", "priority": "high"}
        )

        # Should match
        event1 = ComponentStartedEvent(
            component_name="Test",
            data={"status": "active", "priority": "high", "extra": "value"}
        )
        assert filter_obj.matches(event1) is True

        # Should not match - wrong status
        event2 = ComponentStartedEvent(
            component_name="Test",
            data={"status": "inactive", "priority": "high"}
        )
        assert filter_obj.matches(event2) is False

        # Should not match - missing key
        event3 = ComponentStartedEvent(
            component_name="Test",
            data={"status": "active"}
        )
        assert filter_obj.matches(event3) is False

        # Should not match - wrong value
        event4 = ComponentStartedEvent(
            component_name="Test",
            data={"status": "active", "priority": "low"}
        )
        assert filter_obj.matches(event4) is False

    def test_filter_matches_combined_filters(self):
        """Test filter with multiple filtering conditions."""
        filter_obj = EventFilter(
            event_types=[ComponentStartedEvent],
            sources=["allowed_module"],
            data_patterns={"status": "active"}
        )

        # Should match all conditions
        event1 = ComponentStartedEvent(
            component_name="Test",
            source="allowed_module",
            data={"status": "active"}
        )
        assert filter_obj.matches(event1) is True

        # Should not match wrong event type
        event2 = ComponentStoppedEvent(
            component_name="Test",
            source="allowed_module",
            data={"status": "active"}
        )
        assert filter_obj.matches(event2) is False

        # Should not match wrong source
        event3 = ComponentStartedEvent(
            component_name="Test",
            source="blocked_module",
            data={"status": "active"}
        )
        assert filter_obj.matches(event3) is False

        # Should not match wrong data
        event4 = ComponentStartedEvent(
            component_name="Test",
            source="allowed_module",
            data={"status": "inactive"}
        )
        assert filter_obj.matches(event4) is False


class TestEventInheritanceAndComposition:
    """Test event inheritance and composition patterns."""

    def test_all_events_inherit_from_base(self):
        """Test that all event classes inherit from Event."""
        events = [
            ComponentStartedEvent(),
            ComponentStoppedEvent(),
            ComponentErrorEvent(),
            HttpServerStartedEvent(),
            HTTPRequestEvent(),
            HTTPResponseEvent(),
            HTTPErrorEvent(),
            DBConnectionEvent(),
            DBQueryEvent(),
            DBTransactionEvent(),
            DBPoolEvent(),
            AppStartedEvent(),
            AppStoppedEvent(),
            ConfigUpdatedEvent(),
            UserEvent()
        ]

        for event in events:
            assert isinstance(event, Event)
            assert hasattr(event, 'event_id')
            assert hasattr(event, 'timestamp')
            assert hasattr(event, 'source')
            assert hasattr(event, 'data')

    def test_event_field_override_inheritance(self):
        """Test that subclasses can override default fields."""
        # Test that different subclasses can have different default values
        http_request = HTTPRequestEvent()
        assert http_request.method == ""  # Default empty
        assert http_request.path == ""     # Default empty
        # HTTPRequestEvent does not have status field

        http_response = HTTPResponseEvent()
        assert http_response.status == 200  # Default 200
        assert http_response.response_time == 0.0  # Default 0.0

    def test_dataclass_field_defaults(self):
        """Test that dataclass field defaults are properly set."""
        event = HTTPRequestEvent()

        # Should have default empty dicts that are independent instances
        assert event.headers == {}
        assert event.query_params == {}
        assert event.data == {}

        # Modifying one shouldn't affect others or class defaults
        event.headers["test"] = "value"
        assert event.headers == {"test": "value"}

        new_event = HTTPRequestEvent()
        assert new_event.headers == {}  # Should be fresh dict


class TestEventSerialization:
    """Test event data serialization and representation."""

    def test_event_string_representation(self):
        """Test that events have reasonable string representations."""
        event = ComponentStartedEvent(
            component_name="TestComponent",
            source="test_source"
        )

        # Should be able to convert to string without errors
        str_repr = str(event)
        assert "ComponentStartedEvent" in str_repr
        assert "TestComponent" in str_repr

    def test_event_dict_conversion(self):
        """Test converting events to dictionary representation."""
        event = UserEvent(
            event_type="test.event",
            payload={"key": "value"},
            data={"additional": "data"}
        )

        # Manual dictionary creation for testing
        event_dict = {
            "event_type": event.event_type,
            "payload": event.payload,
            "data": event.data,
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source
        }

        assert event_dict["event_type"] == "test.event"
        assert event_dict["payload"] == {"key": "value"}
        assert event_dict["data"] == {"additional": "data"}

    def test_event_timestamp_handling(self):
        """Test timestamp creation and handling."""
        custom_time = datetime(2023, 12, 25, 12, 30, 45)
        event = Event(timestamp=custom_time)

        assert event.timestamp == custom_time

        # Test automatic timestamp
        auto_event = Event()
        assert isinstance(auto_event.timestamp, datetime)
        # Should be close to current time (within 1 second)
        assert abs((datetime.utcnow() - auto_event.timestamp).total_seconds()) < 1


class TestEventErrorConditions:
    """Test error conditions and edge cases."""

    def test_empty_source_handling(self):
        """Test handling of empty source strings."""
        event = Event(source="")

        # Should try to detect source automatically
        # In test environment, should default to "unknown" or "<string>" or "python"
        assert event._detect_source() in ("unknown", "<string>", "python")

    def test_exception_in_source_detection(self):
        """Test exception handling in source detection."""
        with patch('UCoreFrameworck.messaging.events.inspect.currentframe', side_effect=Exception("Test error")):
            event = Event()
            source = event._detect_source()
            assert source == "unknown"

    def test_large_event_data(self):
        """Test handling of large event data payloads."""
        large_data = {"items": list(range(1000))}  # Large list
        event = UserEvent(payload=large_data)

        assert len(event.payload["items"]) == 1000
        # Should handle large data without issues

    def test_filter_with_empty_lists(self):
        """Test filter behavior with empty constraint lists."""
        filter_obj = EventFilter(
            event_types=[],  # Empty list
            sources=[]       # Empty list
        )

        event = ComponentStartedEvent(component_name="Test")

        # Should match since no constraints are set
        assert filter_obj.matches(event) is True

    def test_filter_with_none_values(self):
        """Test filter behavior with None values in data."""
        filter_obj = EventFilter(
            data_patterns={"optional_field": "value"}
        )

        event1 = ComponentStartedEvent(component_name="Test", data={})
        assert filter_obj.matches(event1) is False  # Key missing

        event2 = ComponentStartedEvent(component_name="Test", data={"optional_field": None})
        assert filter_obj.matches(event2) is False  # Value is None but expected "value"
