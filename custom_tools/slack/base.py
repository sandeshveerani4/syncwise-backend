"""Base class for Slack tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool
from pydantic import Field

from custom_tools.slack.utils import login
from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    # This is for linting and IDE typehints
    from slack_sdk import WebClient
else:
    try:
        # We do this so pydantic can resolve the types when instantiating
        from slack_sdk import WebClient
    except ImportError:
        pass


class SlackBaseTool(BaseTool):  # type: ignore[override]
    """Base class for Slack tools."""

    @classmethod
    def get_client(self,config:RunnableConfig)->WebClient:
        return WebClient(token=config['configurable'].get('__api_keys').SLACK_USER_TOKEN)
