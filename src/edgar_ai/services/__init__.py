"""Service subpackage exports for convenience import paths."""

from .intake import run as intake_run  # noqa: F401

from importlib import import_module as _import_module

# Re-export all service modules so tests can import them easily.
_service_names = [
    "intake",
    "goal_setter",
    "discoverer",
    "schema_synth",
    "prompt_builder",
    "extractor",
    "critic",
    "tutor",
    "breaker",
    "governor",
    "explainer",
]

for _name in _service_names:
    globals()[_name] = _import_module(f"{__name__}.{_name}")

__all__ = _service_names
