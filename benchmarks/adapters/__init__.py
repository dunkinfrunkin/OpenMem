from .base import AdapterCapabilities, MemoryAdapter, RecallResult
from .bm25_only_adapter import BM25OnlyAdapter
from .file_adapter import FileAdapter
from .openmem_adapter import OpenMemAdapter

ADAPTER_REGISTRY: dict[str, type] = {
    "openmem": OpenMemAdapter,
    "bm25_only": BM25OnlyAdapter,
    "file": FileAdapter,
}

# Optional adapters
try:
    from .chromadb_adapter import ChromaDBAdapter

    ADAPTER_REGISTRY["chromadb"] = ChromaDBAdapter
except ImportError:
    pass

try:
    from .mem0_adapter import Mem0Adapter

    ADAPTER_REGISTRY["mem0"] = Mem0Adapter
except ImportError:
    pass

__all__ = [
    "MemoryAdapter",
    "RecallResult",
    "AdapterCapabilities",
    "OpenMemAdapter",
    "BM25OnlyAdapter",
    "FileAdapter",
    "ADAPTER_REGISTRY",
]
