import json
import logging
from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from custom_tools.slack.base import SlackBaseTool
from langchain_core.runnables import RunnableConfig


class SlackGetMessageSchema(BaseModel):
    """Input schema for SlackGetMessages."""

    channel_id: str = Field(
        ...,
        description="The channel id, private group, or IM channel to send message to.",
    )


class SlackGetMessage(SlackBaseTool):  # type: ignore[override, override]
    """Tool that gets Slack messages."""

    name: str = "get_messages"
    description: str = "Use this tool to get messages from a channel."

    args_schema: Type[SlackGetMessageSchema] = SlackGetMessageSchema

    def _run(
        self,
        channel_id: str,
        config:RunnableConfig,
    ) -> str:
        logging.getLogger(__name__)
        try:
            result = self.get_client(config).conversations_history(channel=channel_id)
            messages = result["messages"]
            filtered_messages = [
                {key: message[key] for key in ("user", "text", "ts")}
                for message in messages
                if "user" in message and "text" in message and "ts" in message
            ]
            return json.dumps(filtered_messages, ensure_ascii=False)
        except Exception as e:
            return "Error creating conversation: {}".format(e)
