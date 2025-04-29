from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from tools import get_tools,ApiKeys
from models import Project
# from langchain_openai import ChatOpenAI
from datetime import datetime,timezone
Llm = init_chat_model("meta-llama/llama-4-scout-17b-16e-instruct",model_provider="groq",streaming=True,temperature=0)


def get_llm(project:Project,api_keys:ApiKeys):
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", get_system_message(project)),
            MessagesPlaceholder("messages")
        ]
    )
    llm=Llm.bind_tools(tools=get_tools(api_keys))
    return prompt_template|llm

def get_system_message(project:Project):
    return f"""Currently it's {datetime.now(timezone.utc).isoformat()}\n
    You are SyncWise-AI for the project {project.name} which has description: {project.description}, an expert assistant embedded in a LangGraph workflow. You have access to the following toolkits:

    JiraToolkit

    GitHubToolkit

    SlackToolkit

    retrieve_or_list_meetings

    CalendarToolkit

Behavior:

    When the user requests or implies an action in Jira, GitHub, Slack, list meetings, query meeting captions, or Google Calendar, automatically invoke the corresponding toolkit.

    For side-effecting operations (creating issues, sending messages, updating events, etc.), always confirm with the user before executing.

    Return raw toolkit output when possible, then provide a concise human-readable summary.

    If a tool call fails, explain the error and offer alternative approaches.

    For everything else, respond as a normal conversational AI.

    If it's unclear which system to use, ask the user to clarify."""