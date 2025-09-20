import pytest
import httpx
import asyncio
import tempfile
import os
from ucore_framework.data.mongo_orm import FileRecord

@pytest.fixture(scope="session")
def test_image_path():
    # Create a temporary image file for upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(b"\xff\xd8\xff\xe0" + b"0" * 1024)  # Minimal JPEG header + data
        return f.name

@pytest.fixture(scope="session")
def app_base_url():
    # This fixture should start the UCore app in a test environment and return its base URL
    # For demonstration, assume it's already running at this address
    return "http://127.0.0.1:8888"

@pytest.mark.asyncio
async def test_full_file_upload_and_processing_workflow(app_base_url, test_image_path):
    async with httpx.AsyncClient(base_url=app_base_url) as client:
        # Upload file
        with open(test_image_path, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            resp = await client.post("/api/files", files=files)
        assert resp.status_code in (201, 202)
        file_id = resp.json().get("file_id")
        assert file_id

        # Poll for processing completion
        for _ in range(10):
            resp = await client.get(f"/api/files/{file_id}")
            data = resp.json()
            if data.get("status") == "completed":
                break
            await asyncio.sleep(1)
        else:
            pytest.fail("File processing did not complete in time")

        assert "thumbnail_url" in data or "annotations" in data

        # Database verification
        record = await FileRecord.get_by_id(file_id)
        assert record.status == "completed"
        assert hasattr(record, "thumbnail_url") or hasattr(record, "annotations")

    # Cleanup
    os.remove(test_image_path)
