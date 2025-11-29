"""Filesystem backends used by the pre-show workflow."""

from __future__ import annotations

from deepagents.backends import FilesystemBackend
from deepagents.backends.protocol import EditResult

__all__ = ["SafeFilesystemBackend"]


class SafeFilesystemBackend(FilesystemBackend):
    """Filesystem backend that disables high-risk edit operations outright."""

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(
            error=(
                "`edit_file` is disabled for this workflow to prevent memory exhaustion. "
                "Use `write_file(path, new_content)` to overwrite artifacts instead."
            )
        )
