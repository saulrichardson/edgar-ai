"""Storage helper subpackage."""

# Expose submodules at package level
from importlib import import_module as _import_module

_module_names = [
    "raw_lake",
    "memory",
    "ontology",
    "registry",
    "ledger",
]

for _name in _module_names:
    globals()[_name] = _import_module(f"{__name__}.{_name}")

__all__ = _module_names
