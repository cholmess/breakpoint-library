"""
Plugin management and dynamic loading for optional features (e.g., the Paid ML Tier).
"""

import importlib

def require_ml_plugin(feature_name: str) -> None:
    """
    Ensure that the ML optional dependencies are installed.
    Raises ImportError with a helpful message if they are missing.
    """
    missing = []
    
    try:
        importlib.import_module("torch")
    except ImportError:
        missing.append("torch")
        
    try:
        importlib.import_module("sentence_transformers")
    except ImportError:
        missing.append("sentence-transformers")
        
    if missing:
        raise ImportError(
            f"The feature '{feature_name}' requires the 'ml' plugin, but the following "
            f"dependencies are missing: {', '.join(missing)}.\n"
            "Please install them using: pip install breakpoint-ai[ml]"
        )
