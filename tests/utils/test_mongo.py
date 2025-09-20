import pymongo
from testcontainers.mongodb import MongoDbContainer
from typing import Generator
import pytest

@pytest.fixture(scope="session")
def mongo_db_instance() -> Generator[pymongo.MongoClient, None, None]:
    """
    Pytest fixture that starts a MongoDB container for the test session.
    Yields a client connected to the container.
    """
    with MongoDbContainer("mongo:5.0") as mongo:
        client = mongo.get_connection_client()
        yield client
        client.close()

@pytest.fixture(scope="function")
def mongo_db_session(mongo_db_instance: pymongo.MongoClient) -> Generator[pymongo.database.Database, None, None]:
    """
    Pytest fixture that provides a clean database for each test function.
    It creates a new database and drops it after the test is complete.
    """
    db_name = "test_db"
    db = mongo_db_instance[db_name]
    yield db
    mongo_db_instance.drop_database(db_name)
