from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END,MessagesState
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from llm import llm,system_message
from tools import tools
from typing import TypedDict
from datetime import datetime,timezone
from models import ApiKeys

store=InMemorySaver()

def call_model(state: MessagesState,config:RunnableConfig):
    project=config['configurable'].get('project')
    api_keys=config['configurable'].get('__api_keys')
    response = llm.invoke({"messages": state["messages"],"time":datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),"project_name":project.name,"project_description":project.description,"jira_project":api_keys.JIRA_PROJECT,"github_repository":api_keys.GITHUB_REPOSITORY})
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