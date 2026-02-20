import pytest
from breakpoint.engine.plugins import require_ml_plugin

def test_require_ml_plugin_missing(monkeypatch):
    """Test that missing dependencies correctly raise ImportError."""
    def _mock_import(name, *args, **kwargs):
        raise ImportError(f"No module named {name}")
    
    import importlib
    monkeypatch.setattr(importlib, "import_module", _mock_import)
    
    with pytest.raises(ImportError) as exc_info:
        require_ml_plugin("semantic_similarity")
        
    err = str(exc_info.value)
    assert "requires the 'ml' plugin" in err
    assert "torch" in err
    assert "sentence-transformers" in err
