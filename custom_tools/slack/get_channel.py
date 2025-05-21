import json
import logging
from typing import Any, Optional

from langchain_core.callbacks import CallbackManagerForToolRun

from custom_tools.slack.base import SlackBaseTool
from langchain_core.runnables import RunnableConfig


class SlackGetChannel(SlackBaseTool):  # type: ignore[override]
    """Tool that gets Slack channel information."""

    name: str = "get_channelid_name_dict"
    description: str = (
        "Use this tool to get channelid-name dict. There is no input to this tool"
    )

    def _run(
        self,config:RunnableConfig,*args: Any, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            logging.getLogger(__name__)

            result = self.get_client(config).conversations_list()
            channels = result["channels"]
            filtered_result = [
                {key: channel[key] for key in ("id", "name", "created", "num_members")}
                for channel in channels
                if "id" in channel
                and "name" in channel
                and "created" in channel
                and "num_members" in channel
            ]
            return json.dumps(filtered_result, ensure_ascii=False)

        except Exception as e:
            return "Error creating conversation: {}".format(e)
