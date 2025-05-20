from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from tools import get_tools
from models import ApiKeys
from models import Project

from datetime import datetime,timezone
Llm = init_chat_model("meta-llama/llama-4-scout-17b-16e-instruct",model_provider="groq",streaming=True,temperature=0.35)


def get_llm(project:Project,api_keys:ApiKeys):
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", get_system_message(project,api_keys)),
            MessagesPlaceholder("messages")
        ]
    )
    llm=Llm.bind_tools(tools=get_tools(api_keys))
    return prompt_template|llm

def get_system_message(project:Project,api_keys:ApiKeys):
    return f"""Currently it's {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n
    You are SyncWise-AI for the project {project.name} which has description: {project.description}, an expert assistant embedded in a LangGraph workflow. You have access to the following toolkits:
    
    {f"JiraToolkit (projectKey: `{api_keys.JIRA_PROJECT}`)\n" if api_keys.JIRA_API_TOKEN is not None else ""}
    {f"GitHubToolkit (repository: `{api_keys.GITHUB_REPOSITORY}`)\n" if api_keys.GITHUB_REPOSITORY is not None else ""}
    {f"SlackToolkit\n" if api_keys.SLACK_USER_TOKEN is not None else ""}
    {f"CalendarToolkit\n" if api_keys.CALENDAR_TOKEN is not None else ""}
    retrieve_or_list_meetings

Behavior:

    When the user requests or implies an action in Jira, GitHub, Slack, list meetings, query meeting captions, or Google Calendar, automatically invoke the corresponding toolkit.

    For side-effecting operations (creating issues, sending messages, updating events, etc.), always confirm with the user before executing.

    Return raw toolkit output when possible, then provide a concise human-readable summary.

    If a tool call fails, explain the error and offer alternative approaches.

    For everything else, respond as a normal conversational AI.

    If it's unclear which system to use, ask the user to clarify.
    
    When writing code or file contents, use markdown code blocks with triple backticks and specify the language or file format immediately after the opening backticks (e.g., ```html).."""