import pytest
import asyncio
from UCoreFrameworck.fs.indexers import Indexer, FileTypeStrategy, register_strategy, get_strategy_by_extension

class DummyIndexer(Indexer):
    async def process(self, file_record, file_path):
        file_record.processed = True

@pytest.mark.asyncio
async def test_register_and_run_indexer():
    strategy = FileTypeStrategy("dummy", [DummyIndexer()])
    register_strategy("dummy", strategy)
    file_record = type("FileRecord", (), {})()
    file_path = "test.dummy"
    strat = get_strategy_by_extension("dummy")
    await strat.process(file_record, file_path)
    assert hasattr(file_record, "processed") and file_record.processed
