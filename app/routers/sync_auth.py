import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException


def verify_sync_key(
    x_sync_key: Optional[str] = Header(default=None),
) -> None:
    expected_key = os.getenv("SYNC_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Cloud synchronization is not configured.",
        )

    if not x_sync_key or not secrets.compare_digest(
        x_sync_key,
        expected_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid synchronization key.",
        )
