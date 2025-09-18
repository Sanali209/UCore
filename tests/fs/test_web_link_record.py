import pytest
import asyncio
from ucore_framework.fs.components.web_link import WebLinkRecord

@pytest.mark.asyncio
async def test_create_web_link_record():
    record = await WebLinkRecord.new_record(
        url="https://example.com",
        title="Example",
        description="A test web link",
        related_id="file1"
    )
    assert record.url == "https://example.com"
    assert record.title == "Example"
    assert record.description == "A test web link"
    assert record.related_id == "file1"
