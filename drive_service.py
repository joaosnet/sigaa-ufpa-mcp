"""Backward-compatible re-export of sigaa_mcp.drive_service."""

from sigaa_mcp.drive_service import (
    SCOPES,
    GoogleDriveService,
    get_drive_config,
    is_drive_configured,
)

__all__ = [
    "SCOPES",
    "GoogleDriveService",
    "get_drive_config",
    "is_drive_configured",
]
