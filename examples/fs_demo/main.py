"""
UCore Framework Example: File System Features

Demonstrates file system abstraction, annotation, indexing, and vector DB.
"""

from UCoreFrameworck.fs.resource import FilesDBResource
from UCoreFrameworck.fs.annotation import get_annotation_job
from UCoreFrameworck.fs.indexers import get_strategy_by_extension
from UCoreFrameworck.fs.vector_db_ext import EmbeddingFusion, vectorize_file

class MockApp:
    def __init__(self):
        self.container = {}
        self.logger = type("Logger", (), {"info": print, "warning": print, "error": print, "debug": print})()

def main():
    app = MockApp()

    # File system abstraction demo
    from UCoreFrameworck.messaging.event_bus import EventBus
    class MockEventBus(EventBus):
        def __init__(self):
            pass
    files_db = FilesDBResource(config={}, event_bus=MockEventBus())
    print("FilesDBResource initialized:", files_db)

    # Annotation job demo
    job = get_annotation_job("avg_rating")
    print("Annotation job (avg_rating):", job)

    # Indexer strategy demo
    strategy = get_strategy_by_extension("jpg")
    print("Indexer strategy for .jpg:", strategy)

    # Vector DB extension demo
    fusion = EmbeddingFusion(target_dim=768)
    fusion.add_embedding("example", [0.1] * 768)
    print("EmbeddingFusion example, fused vector:", fusion.fuse())

    # Vectorize file API demo (stub)
    print("vectorize_file API demo:", vectorize_file(None))

    print("In a real app, these would be registered as components and started by the UCoreFrameworck.")

if __name__ == "__main__":
    main()
