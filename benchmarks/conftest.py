from __future__ import annotations

import pytest

from .adapters import ADAPTER_REGISTRY
from .adapters.base import MemoryAdapter


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark-adapters",
        nargs="+",
        default=None,
        help="Adapters to include in benchmark tests",
    )


@pytest.fixture(params=["openmem", "bm25_only", "file"])
def adapter(request) -> MemoryAdapter:
    """Parametrized fixture that yields each available adapter."""
    adapter_name = request.param
    selected = request.config.getoption("--benchmark-adapters", default=None)
    if selected and adapter_name not in selected:
        pytest.skip(f"{adapter_name} not in selected adapters")

    adapter_cls = ADAPTER_REGISTRY.get(adapter_name)
    if adapter_cls is None:
        pytest.skip(f"Unknown adapter: {adapter_name}")

    try:
        return adapter_cls()
    except ImportError:
        pytest.skip(f"Dependencies not available for {adapter_name}")
