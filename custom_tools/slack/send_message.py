from typing import Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from custom_tools.slack.base import SlackBaseTool
from langchain_core.runnables import RunnableConfig

class SendMessageSchema(BaseModel):
    """Input for SendMessageTool."""

    message: str = Field(
        ...,
        description="The message to be sent.",
    )
    channel: str = Field(
        ...,
        description="The channel, private group, or IM channel to send message to.",
    )


class SlackSendMessage(SlackBaseTool):  # type: ignore[override, override]
    """Tool for sending a message in Slack."""

    name: str = "send_message"
    description: str = (
        "Use this tool to send a message with the provided message fields."
    )
    args_schema: Type[SendMessageSchema] = SendMessageSchema

    def _run(
        self,
        message: str,
        channel: str,
        config:RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            result = self.get_client(config).chat_postMessage(channel=channel, text=message)
            output = "Message sent: " + str(result)
            return output
        except Exception as e:
            return "Error creating conversation: {}".format(e)
