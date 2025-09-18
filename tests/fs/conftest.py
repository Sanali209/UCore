import pytest
from unittest.mock import AsyncMock
import sys
import os

# Ensure project root is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import UCoreFrameworck.fs.models as fs_models
from bson import ObjectId

@pytest.fixture(autouse=True, scope="module")
def inject_async_mock_db():
    """Inject AsyncMock db into all fs models for async test compatibility."""
    mock_db = {}
    valid_id = ObjectId("64b7f8f8e1b2c3d4e5f6a7b8")
    # Patch insert_one, find_one, etc. for each collection
    for model in [
        fs_models.CatalogRecord,
        fs_models.FileRecord,
        fs_models.TagRecord,
        getattr(fs_models, "RelationRecord", None),
        getattr(fs_models, "WebLinkRecord", None)
    ]:
        if model is None:
            continue
        collection_mock = AsyncMock()
        # insert_one returns an object with inserted_id
        collection_mock.insert_one.return_value = AsyncMock(inserted_id=valid_id)
        # find_one returns a dict with _id if called
        collection_mock.find_one.return_value = {"_id": valid_id, "fullName": "test_catalog"}
        # update_one, delete_one, etc. can be set as needed
        mock_db[model.collection_name] = collection_mock
        model.inject_db_client(mock_db, None)
