from typing import Dict, List

from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit

from langchain_community.tools.jira.prompt import (
    JIRA_CATCH_ALL_PROMPT,
    JIRA_CONFLUENCE_PAGE_CREATE_PROMPT,
    JIRA_GET_ALL_PROJECTS_PROMPT,
    JIRA_ISSUE_CREATE_PROMPT,
    JIRA_JQL_PROMPT,
)
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_core.runnables import RunnableConfig


from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun


class JiraAction(BaseTool):
    """Tool that queries the Atlassian Jira API."""

    api_wrapper: JiraAPIWrapper = None
    mode: str
    name: str = ""
    description: str = ""

    def _run(
        self,
        instructions: str,
        config:RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Atlassian Jira API to run an operation."""
        if not config['configurable'].get('__api_keys').JIRA_API_TOKEN or not config['configurable'].get('__api_keys').JIRA_USERNAME or not config['configurable'].get('__api_keys').JIRA_INSTANCE_URL:
            raise Exception(f"Jira is not setup yet.")
        self.api_wrapper=JiraAPIWrapper(jira_api_token=config['configurable'].get('__api_keys').JIRA_API_TOKEN,jira_username=config['configurable'].get('__api_keys').JIRA_USERNAME,jira_cloud=True,jira_instance_url=config['configurable'].get('__api_keys').JIRA_INSTANCE_URL)
        return self.api_wrapper.run(self.mode, instructions)


class JiraToolkit(BaseToolkit):
    """Jira Toolkit.

    *Security Note*: This toolkit contains tools that can read and modify
        the state of a service; e.g., by creating, deleting, or updating,
        reading underlying data.

        See https://python.langchain.com/docs/security for more information.

    Parameters:
        tools: List[BaseTool]. The tools in the toolkit. Default is an empty list.
    """

    tools: List[BaseTool] = []

    @classmethod
    def from_config(cls) -> "JiraToolkit":
        """Create a JiraToolkit from a JiraAPIWrapper.

        Returns:
            JiraToolkit. The Jira toolkit.
        """

        operations: List[Dict] = [
            {
                "mode": "jql",
                "name": "jql_query",
                "description": JIRA_JQL_PROMPT,
            },
            {
                "mode": "get_projects",
                "name": "get_projects",
                "description": JIRA_GET_ALL_PROJECTS_PROMPT,
            },
            {
                "mode": "create_issue",
                "name": "create_issue",
                "description": JIRA_ISSUE_CREATE_PROMPT,
            },
            {
                "mode": "other",
                "name": "catch_all_jira_api",
                "description": JIRA_CATCH_ALL_PROMPT,
            },
            {
                "mode": "create_page",
                "name": "create_confluence_page",
                "description": JIRA_CONFLUENCE_PAGE_CREATE_PROMPT,
            },
        ]
        tools = [
            JiraAction(
                name=action["name"],
                description=action["description"],
                mode=action["mode"],
            )
            for action in operations
        ]
        return cls(tools=tools)  # type: ignore[arg-type]

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        return self.tools
