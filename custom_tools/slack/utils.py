"""Slack tool utils."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slack_sdk import WebClient

logger = logging.getLogger(__name__)


def login(token:str) -> WebClient:
    """Authenticate using the Slack API."""
    try:
        from slack_sdk import WebClient
    except ImportError as e:
        raise ImportError(
            "Cannot import slack_sdk. Please install the package with \
            `pip install slack_sdk`."
        ) from e
    if token is not None:
        client = WebClient(token=token)
        logger.info("slack login success")
        return client
    else:
        print("Here",token)


UTC_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
"""UTC format for datetime objects."""
