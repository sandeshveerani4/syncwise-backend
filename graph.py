from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END,MessagesState
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from llm import llm
from tools import tools
from typing import TypedDict
from datetime import datetime,timezone
from models import ApiKeys,Project

store=InMemorySaver()

def call_model(state: MessagesState,config:RunnableConfig):
    system_message=config['configurable'].get('system_message')
    response = llm.invoke({"messages": state["messages"],"system_message":system_message})
    return {"messages": [response]}

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

class ConfigSchema(TypedDict):
    thread_id: str
    api_keys: ApiKeys

workflow = StateGraph(MessagesState,ConfigSchema)
tool_node = ToolNode(tools)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")
graph =workflow.compile(store=store)

def generate_system(api_keys:ApiKeys,project:Project):
    return f"""Currently it's {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\nYou are SyncWise-AI for the project {project.name} which has description: {project.description}, an expert assistant embedded in a LangGraph workflow.
    Behavior:
        When the user requests or implies an action in Jira, GitHub, Slack, list meetings, query meeting captions, or Google Calendar, automatically invoke the corresponding toolkit.

        For side-effecting operations (creating issues, sending messages, updating events, etc.), always confirm with the user before executing.

        Return raw toolkit output when possible, then provide a concise human-readable summary.

        If a tool call fails, explain the error and offer alternative approaches.

        For everything else, respond as a normal conversational AI.

        If it's unclear which system to use, ask the user to clarify.
        
        When writing code or file contents, use markdown code blocks with triple backticks and specify the language or file format immediately after the opening backticks (e.g., ```html).
    
    Some configurations:
        Jira Project key: `{api_keys.JIRA_PROJECT}`
        GitHub Repository: `{api_keys.GITHUB_REPOSITORY}`"""