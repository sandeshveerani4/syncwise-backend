from socket import fromfd
from custom_tools.jira_tool import JiraToolkit
from custom_tools.slack_tool import SlackToolkit
from custom_tools.github_tool import GitHubToolkit
from custom_tools.calendar_tool import CalendarToolkit
from custom_tools.meeting_retriever import retrieve_or_list_meetings
import os

tools=[]

try:
    calendar_toolkit = CalendarToolkit()
    calendar_tools=calendar_toolkit.get_tools()
    tools.extend(calendar_tools)
except Exception as error:
    print("Calendar Tool error: ",error)

try:
    toolkit = JiraToolkit.from_config()
    jira_tools = toolkit.get_tools()
    tools.extend(jira_tools)
except Exception as error:
    print("Jira Tool error: ",error)

try:
    with open(os.environ['GITHUB_APP_PRIVATE_FILE']) as f:
        github_toolkit = GitHubToolkit.from_file()
        github_tools = github_toolkit.get_tools()
        tools.extend(github_tools)
except Exception as error:
    print("GitHub Tool error: ",error)

try:
    slack_toolkit = SlackToolkit()
    slack_tools = slack_toolkit.get_tools()
    tools.extend(slack_tools)
except Exception as error:
    print("Slack Tool error: ",error)

try:
    tools.append(retrieve_or_list_meetings)
except Exception as error:
    print("Meetings Tool error: ",error)
