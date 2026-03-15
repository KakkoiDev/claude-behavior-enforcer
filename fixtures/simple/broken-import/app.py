"""Simple app that fails due to wrong import name."""

from collections import OrderedDict


def get_ordered_items():
    """Return items in insertion order."""
    items = OrderedDict()
    items["first"] = 1
    items["second"] = 2
    items["third"] = 3
    return items


if __name__ == "__main__":
    result = get_ordered_items()
    for key, value in result.items():
        print(f"{key}: {value}")
