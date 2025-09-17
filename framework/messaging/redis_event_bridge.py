"""
Redis Adapter Event Bus Bridge Mixins
Provides bridges between EventBus and Redis pub/sub channels/streams.
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json


class EventBusToRedisBridge:
    """
    Mixin class that enables EventBus-to-Redis forwarding.
    Provides methods to subscribe to EventBus events and forward them to Redis channels.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bridge_handlers: Dict[str, Callable] = {}
        self.event_forwarders: Dict[str, Callable] = {}

    def register_event_forwarder(self,
                                  event_type: Any,  # Can be string or event class
                                  redis_channel: str,
                                  event_filter: Optional[Callable] = None) -> None:
        """
        Register an event type to be forwarded to a Redis channel.

        Args:
            event_type: The event type class or name
            redis_channel: Redis channel name to forward to
            event_filter: Optional filter function that returns True if event should be forwarded
        """
        if not self.bridge_settings.get('eventbus_to_redis_enabled', True):
            return

        async def forwarder(event):
            """Forward EventBus event to Redis channel."""
            if event_filter and not event_filter(event):
                return

            # Create standardized message format
            message = self._create_bridge_message(event)

            try:
                # Get Redis publish function (assuming it's implemented in the mixed-in class)
                success = await self.publish(redis_channel, message)

                if success and self.app and hasattr(self.app, 'logger'):
                    self.app.logger.debug(f"Forwarded {event_type} event to Redis channel: {redis_channel}")

            except Exception as e:
                if self.app and hasattr(self.app, 'logger'):
                    self.app.logger.error(f"Failed to forward {event_type} event to Redis: {e}")

        # Store the forwarder for later subscription
        self.event_forwarders[event_type] = forwarder

        # Try to register immediately if EventBus is available
        if hasattr(self, 'app') and self.app:
            try:
                event_bus = self.app.container.get("EventBus", type("EventBus", (), {})())
                if event_bus:
                    event_bus.add_handler(event_type, forwarder)
                    self.bridge_handlers[f"forward_{event_type}"] = forwarder
            except:
                pass  # EventBus might not be ready yet

    def _create_bridge_message(self, event) -> Dict[str, Any]:
        """
        Create a standardized message format for EventBus events.

        Args:
            event: The EventBus event to convert

        Returns:
            Dictionary with standardized message format
        """
        try:
            # If event is not an object with attributes, treat as fallback
            if not hasattr(event, "__dict__") and not hasattr(event, "data"):
                return {
                    'event_type': 'unknown',
                    'error': 'Event is not a valid object',
                    'original_event': str(event),
                    'instance_id': self.bridge_settings.get('instance_id', 'unknown'),
                    'timestamp': datetime.utcnow().isoformat(),
                }

            # Extract event attributes
            event_data = {
                'event_type': event.__class__.__name__,
                'timestamp': event.timestamp.isoformat() if hasattr(event, 'timestamp') else datetime.utcnow().isoformat(),
                'source': event.source if hasattr(event, 'source') else 'unknown',
                'event_bus_source': 'ucore_framework',
                'instance_id': self.bridge_settings.get('instance_id', 'unknown'),
            }

            # Add event-specific data
            if hasattr(event, 'data') and event.data:
                event_data['data'] = event.data
            else:
                # Try to get event attributes
                event_attrs = {}
                for attr in dir(event):
                    if not attr.startswith('_') and attr not in ['__class__', '__dict__', '__weakref__', '__module__']:
                        try:
                            value = getattr(event, attr)
                            if not callable(value):
                                event_attrs[attr] = str(value)
                        except:
                            pass
                event_data['data'] = event_attrs

            return event_data

        except Exception as e:
            # Fallback message format
            return {
                'event_type': 'unknown',
                'error': f'Failed to create bridge message: {str(e)}',
                'original_event': str(event),
                'instance_id': self.bridge_settings.get('instance_id', 'unknown'),
                'timestamp': datetime.utcnow().isoformat(),
            }


class RedisToEventBusBridge:
    """
    Mixin class that enables Redis-to-EventBus forwarding.
    Provides methods to subscribe to Redis channels and forward messages to EventBus.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_listeners: Dict[str, Callable] = {}
        self.redis_channel_mappings: Dict[str, str] = {}

    def register_redis_listener(self,
                                redis_channel: str,
                                event_type_mapping: Optional[Dict[str, str]] = None) -> None:
        """
        Register a Redis channel listener that forwards messages to EventBus.

        Args:
            redis_channel: Redis channel to listen to
            event_type_mapping: Optional mapping of Redis message types to EventBus event types
        """
        if not self.bridge_settings.get('redis_to_eventbus_enabled', True):
            return

        async def listener(message):
            """Convert Redis message to EventBus event and publish."""
            try:
                # Parse the message
                if isinstance(message, str):
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        message_data = {'content': message, 'type': 'plain_text'}
                elif isinstance(message, dict):
                    message_data = message
                else:
                    message_data = {'content': str(message), 'type': 'raw'}

                # Apply event type mapping
                event_type = 'RedisMessageEvent'
                if event_type_mapping and 'type' in message_data:
                    if message_data['type'] in event_type_mapping:
                        event_type = event_type_mapping[message_data['type']]

                # Create EventBus event
                event = self._create_eventbus_event(event_type, message_data, redis_channel)

                # Publish to EventBus
                if hasattr(self, 'app') and self.app:
                    from framework.messaging.events import UserEvent  # Import here to avoid circular imports
                    user_event = UserEvent(
                        event_type=f"redis:{redis_channel}",
                        data={
                            'redis_channel': redis_channel,
                            'message': message_data,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )

                    # Get EventBus and publish
                    try:
                        event_bus = self.app.container.get("EventBus", type("EventBus", (), {})())
                        if event_bus:
                            result = event_bus.publish(user_event)
                            if asyncio.iscoroutine(result):
                                await result

                            if self.app and hasattr(self.app, 'logger'):
                                self.app.logger.debug(f"Received Redis message from {redis_channel}, created EventBus event: {user_event.event_type}")
                    except Exception as e:
                        if self.app and hasattr(self.app, 'logger'):
                            self.app.logger.error(f"Failed to forward Redis message to EventBus: {e}")

            except Exception as e:
                if self.app and hasattr(self.app, 'logger'):
                    self.app.logger.error(f"Error processing Redis message from {redis_channel}: {e}")

        self.redis_listeners[redis_channel] = listener

        # Optionally register with Redis immediately if available
        if hasattr(self, 'subscribers'):
            self.subscribers[redis_channel] = listener

    def _create_eventbus_event(self, event_type: str, data: Dict[str, Any], source_channel: str):
        """
        Create an EventBus-compatible event from Redis message data.

        Args:
            event_type: Type/class name for the event
            data: Message data from Redis
            source_channel: The Redis channel this came from

        Returns:
            EventBus event instance or dict for UserEvent
        """
        # For now, return data to be used in UserEvent
        # In future, could instantiate specific event types
        return {
            'type': event_type,
            'data': data,
            'source_channel': source_channel,
            'source': f'redis:{source_channel}'
        }


class EventBusRedisBridge(EventBusToRedisBridge, RedisToEventBusBridge):
    """
    Complete bidirectional bridge between EventBus and Redis.
    Combines both forwarding directions and provides additional utilities.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bridge_statistics = {
            'events_forwarded_eventbus_to_redis': 0,
            'messages_forwarded_redis_to_eventbus': 0,
            'errors_eventbus_to_redis': 0,
            'errors_redis_to_eventbus': 0,
        }

    def enable_bridge(self, direction: str = 'both') -> None:
        """
        Enable the bridge for specified directions.

        Args:
            direction: 'both', 'eventbus_to_redis', or 'redis_to_eventbus'
        """
        if direction in ['both', 'eventbus_to_redis']:
            self.bridge_settings['eventbus_to_redis_enabled'] = True

        if direction in ['both', 'redis_to_eventbus']:
            self.bridge_settings['redis_to_eventbus_enabled'] = True

        if hasattr(self, 'app') and self.app.logger:
            self.app.logger.info(f"Redis EventBus bridge enabled for: {direction}")

    def disable_bridge(self, direction: str = 'both') -> None:
        """
        Disable the bridge for specified directions.

        Args:
            direction: 'both', 'eventbus_to_redis', or 'redis_to_eventbus'
        """
        if direction in ['both', 'eventbus_to_redis']:
            self.bridge_settings['eventbus_to_redis_enabled'] = False

        if direction in ['both', 'redis_to_eventbus']:
            self.bridge_settings['redis_to_eventbus_enabled'] = False

        if hasattr(self, 'app') and self.app.logger:
            self.app.logger.info(f"Redis EventBus bridge disabled for: {direction}")

    def get_bridge_stats(self) -> Dict[str, int]:
        """
        Get statistics about bridge operation.

        Returns:
            Dictionary with bridge statistics
        """
        return self.bridge_statistics.copy()

    def reset_bridge_stats(self) -> None:
        """
        Reset bridge statistics counters.
        """
        for key in self.bridge_statistics:
            self.bridge_statistics[key] = 0
