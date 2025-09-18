import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from loguru import logger
from tqdm import tqdm

from framework.resource.manager import ResourceManager
from framework.data.mongo_adapter import MongoDBAdapter
from framework.data.disk_cache import DiskCacheAdapter

class DummyResource:
    def __init__(self, name, resource_type="test"):
        self.name = name
        self.resource_type = resource_type
        self.started = False
        self.stopped = False
        self.health = type("Health", (), {"value": "healthy"})()

    async def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True

    def get_stats(self):
        return {"started": self.started, "stopped": self.stopped}

@pytest.mark.asyncio
class TestResourceDataIntegration:
    @pytest.fixture(scope="class")
    def resource_manager(self):
        return ResourceManager()

    @pytest.fixture(scope="class")
    def mongo_adapter(self):
        return MongoDBAdapter(app=None)

    @pytest.fixture(scope="class")
    def disk_cache_adapter(self):
        return DiskCacheAdapter(app=None)

    @pytest.mark.asyncio
    async def test_resource_manager_starts_and_stops_data_adapters(self, resource_manager, mongo_adapter, disk_cache_adapter):
        logger.info("Testing ResourceManager with data adapters")
        # Register dummy resources for simulation
        dummy1 = DummyResource("mongo")
        dummy2 = DummyResource("disk_cache")
        resource_manager.register_resource(dummy1)
        resource_manager.register_resource(dummy2)

        with tqdm(total=2, desc="Starting resources") as pbar:
            await dummy1.start()
            pbar.update(1)
            await dummy2.start()
            pbar.update(1)

        assert dummy1.started and dummy2.started, "Resources should be started"

        with tqdm(total=2, desc="Stopping resources") as pbar:
            await dummy1.stop()
            pbar.update(1)
            await dummy2.stop()
            pbar.update(1)

        assert dummy1.stopped and dummy2.stopped, "Resources should be stopped"

    @pytest.mark.asyncio
    async def test_resource_manager_reports_status(self, resource_manager):
        logger.info("Testing ResourceManager status reporting")
        stats = resource_manager.get_resource_stats()
        logger.info(f"Resource stats: {stats}")
        assert isinstance(stats, dict)
