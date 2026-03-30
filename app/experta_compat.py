from __future__ import annotations

import collections
import collections.abc


_COMPAT_ATTRS = (
    "Mapping",
    "MutableMapping",
    "Sequence",
    "MutableSequence",
    "Set",
    "MutableSet",
    "Iterable",
    "Iterator",
    "Callable",
)


def patch_experta_compat() -> None:
    """Patch deprecated aliases removed from `collections` in modern Python.

    `experta` (via dependencies) still imports these names from `collections`.
    """
    for attr_name in _COMPAT_ATTRS:
        if not hasattr(collections, attr_name) and hasattr(collections.abc, attr_name):
            setattr(collections, attr_name, getattr(collections.abc, attr_name))
