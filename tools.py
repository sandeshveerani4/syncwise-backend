from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from slack_tool import SlackToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
)
from slack_sdk import WebClient
from utils import get_google_credentials
from calendar_tool import CalendarToolkit
from meeting_retriever import _retrieve_or_list_meetings
from models import ApiKeys

def get_tools(api_keys:ApiKeys):
    tools=[]
    if api_keys.CALENDAR_TOKEN is not None:
        try:
            credentials = get_google_credentials(
                token=api_keys.CALENDAR_TOKEN,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )

            api_resource = build_resource_service(credentials=credentials)
            calendar_toolkit = CalendarToolkit(api_resource=api_resource)
            calendar_tools=calendar_toolkit.get_tools()
            tools.extend(calendar_tools)
        except Exception as error:
            print(error)
    
    if api_keys.JIRA_API_TOKEN is not None and api_keys.JIRA_INSTANCE_URL is not None and api_keys.JIRA_USERNAME is not None:
        try:
            jira = JiraAPIWrapper(jira_api_token=api_keys.JIRA_API_TOKEN,jira_username=api_keys.JIRA_USERNAME,jira_cloud=True,jira_instance_url=api_keys.JIRA_INSTANCE_URL)
            toolkit = JiraToolkit.from_jira_api_wrapper(jira)
            jira_tools = toolkit.get_tools()
            tools.extend(jira_tools)
        except Exception as error:
            print(error)
    
    if api_keys.GITHUB_REPOSITORY is not None:
        try:
            github = GitHubAPIWrapper(github_repository=api_keys.GITHUB_REPOSITORY)
            github_toolkit = GitHubToolkit.from_github_api_wrapper(github)
            github_tools = github_toolkit.get_tools()
            tools.extend(github_tools)
        except Exception as error:
            print(error)


    if api_keys.SLACK_USER_TOKEN is not None:
        try:
            client = WebClient(token=api_keys.SLACK_USER_TOKEN)
            slack_toolkit = SlackToolkit(client=client)
            slack_tools = slack_toolkit.get_tools()
            tools.extend(slack_tools)
        except Exception as error:
            print(error)

    try:
        tools.append(_retrieve_or_list_meetings(api_keys.user_id,api_keys.project_id))
        """ tools.append(Tool(
        name="retrieve_or_list_meetings",
        func=retrieve_or_list_meetings(api_keys.user_id,api_keys.project_id),
        description=(
            "If you give me both a `query` and a `meeting_id`, I'll return transcript snippets "
            "from that meeting.\n"
            "`query` will never be empty(even when there is `meeting_id`) → Pass the user prompt\n"
            "If you only give me a `query`, I'll interpret it as either:\n"
            "  • asking for a specific attendee → I'll list meetings with that attendee,\n"
            "  • asking for a date → I'll list meetings on that date,\n"
            "  • else → I'll list all your meetings (with IDs, titles, times and attendees).\n"
        )
    )) """
    except Exception as error:
        print(error)
    
    return tools