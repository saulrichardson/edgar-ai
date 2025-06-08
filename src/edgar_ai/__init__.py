"""Top-level package for edgar_ai scaffold."""

from importlib import metadata as _metadata


try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"


__all__ = [
    "__version__",
]
