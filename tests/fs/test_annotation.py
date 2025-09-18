import pytest
import asyncio
from framework.fs.annotation import AnnotationJob, register_annotation_job, get_annotation_job

class DummyAnnotationJob(AnnotationJob):
    async def run(self, file_record, annotation_data):
        file_record.annotated = True

@pytest.mark.asyncio
async def test_register_and_run_annotation_job():
    register_annotation_job("dummy", DummyAnnotationJob())
    file_record = type("FileRecord", (), {})()
    annotation_data = {"label": "test"}
    job = get_annotation_job("dummy")
    await job.run(file_record, annotation_data)
    assert hasattr(file_record, "annotated") and file_record.annotated
