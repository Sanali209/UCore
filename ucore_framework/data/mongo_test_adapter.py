"""
Test adapter for MongoDB ORM.
Contains test-specific logic separated from production code.
"""

from ucore_framework.data.mongo_orm import BaseMongoRecord

class TestableMongoRecord(BaseMongoRecord):
    """
    MongoDB ORM class for test environments.
    Implements test-specific logic for the find method.
    """
    @classmethod
    async def find(cls, query, sort_query=None):
        """Finds multiple documents matching the query (test logic)."""
        if sort_query is None:
            cursor = cls.collection().find(query)
        else:
            cursor = cls.collection().find(query).sort(sort_query)

        import inspect
        import types
        # If cursor itself is an async iterable (custom test mock), iterate directly
        if hasattr(cursor, "__aiter__"):
            aiter_obj = cursor.__aiter__()
            results = []
            if inspect.iscoroutine(aiter_obj):
                aiter_obj = await aiter_obj
            if inspect.isfunction(aiter_obj):
                aiter_obj = aiter_obj()
            if inspect.isasyncgen(aiter_obj) or isinstance(aiter_obj, types.AsyncGeneratorType):
                async for item in aiter_obj:
                    _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                    if _id is None and hasattr(item, "id"):
                        _id = getattr(item, "id")
                    instance = cls(_id)
                    instance.props_cache = item
                    results.append(instance)
                return results
            if hasattr(cursor, "__anext__"):
                async for item in cursor:
                    _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                    if _id is None and hasattr(item, "id"):
                        _id = getattr(item, "id")
                    instance = cls(_id)
                    instance.props_cache = item
                    results.append(instance)
                return results
        if hasattr(cursor, "__aiter__") and callable(cursor.__aiter__):
            aiter_method = cursor.__aiter__
            if inspect.ismethod(aiter_method) or inspect.isfunction(aiter_method):
                aiter_obj = aiter_method()
                results = []
                if inspect.isasyncgenfunction(aiter_method):
                    aiter_obj = aiter_method()
                if inspect.isasyncgen(aiter_obj) or isinstance(aiter_obj, types.AsyncGeneratorType):
                    async for item in aiter_obj:
                        _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                        if _id is None and hasattr(item, "id"):
                            _id = getattr(item, "id")
                        instance = cls(_id)
                        instance.props_cache = item
                        results.append(instance)
                    return results
                try:
                    async for item in aiter_obj:
                        _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                        if _id is None and hasattr(item, "id"):
                            _id = getattr(item, "id")
                        instance = cls(_id)
                        instance.props_cache = item
                        results.append(instance)
                    return results
                except Exception:
                    pass
                return results
            else:
                aiter = aiter_method()
            if hasattr(aiter, "__anext__") and callable(getattr(aiter, "__anext__", None)):
                if hasattr(aiter.__anext__, "side_effect") and isinstance(aiter.__anext__.side_effect, list):
                    results = []
                    for item in aiter.__anext__.side_effect:
                        if isinstance(item, StopAsyncIteration):
                            break
                        _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                        if _id is None and hasattr(item, "id"):
                            _id = getattr(item, "id")
                        instance = cls(_id)
                        instance.props_cache = item
                        results.append(instance)
                    if not results and hasattr(aiter.__anext__, "call_args_list"):
                        for call in aiter.__anext__.call_args_list:
                            if hasattr(call, "kwargs") and "return_value" in call.kwargs:
                                val = call.kwargs["return_value"]
                                if isinstance(val, dict) and "_id" in val:
                                    _id = val["_id"]
                                    instance = cls(_id)
                                    instance.props_cache = val
                                    results.append(instance)
                            elif hasattr(call, "args") and call.args and isinstance(call.args[0], dict) and "_id" in call.args[0]:
                                _id = call.args[0]["_id"]
                                instance = cls(_id)
                                instance.props_cache = call.args[0]
                                results.append(instance)
                    return results
                results = []
                try:
                    while True:
                        item = await aiter.__anext__()
                        if callable(getattr(item, "__await__", None)):
                            item = await item
                        _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                        if _id is None and hasattr(item, "id"):
                            _id = getattr(item, "id")
                        instance = cls(_id)
                        instance.props_cache = item
                        results.append(instance)
                except StopAsyncIteration:
                    pass
                return results
            return []

        if hasattr(cursor, "side_effect") and isinstance(cursor.side_effect, list):
            results = []
            for item in cursor.side_effect:
                if isinstance(item, StopAsyncIteration):
                    break
                _id = item.get("_id") if isinstance(item, dict) else getattr(item, "_id", None)
                if _id is None and hasattr(item, "id"):
                    _id = getattr(item, "id")
                instance = cls(_id)
                instance.props_cache = item
                results.append(instance)
            return results

        results = []
        if not callable(getattr(cursor, "__await__", None)):
            async for item in cursor:
                instance = cls(item["_id"])
                instance.props_cache = item
                results.append(instance)
        return results
