import re


def next_version(existing_version: str | None) -> int:
    if not existing_version:
        return 1
    match = re.search(r"v(\d+)$", existing_version)
    if match:
        return int(match.group(1)) + 1
    return 1
