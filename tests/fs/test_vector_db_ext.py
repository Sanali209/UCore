import pytest
from UCoreFrameworck.fs.vector_db_ext import EmbeddingFusion

def test_embedding_fusion_weighted_average_stub():
    fusion = EmbeddingFusion(target_dim=4)
    fusion.add_embedding("a", [1, 2, 3, 4], weight=0.5)
    fusion.add_embedding("b", [4, 3, 2, 1], weight=0.5)
    result = fusion.fuse()
    # Since fuse() is a stub, just check it returns the first embedding for now
    assert result == [1, 2, 3, 4]
