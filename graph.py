from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END,MessagesState
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from llm import get_llm,get_system_message
from tools import get_tools,ApiKeys
from typing import TypedDict

checkpointer=MemorySaver()

def call_model(state: MessagesState, config: RunnableConfig):
    response = get_llm(config['configurable'].get('project'),config['configurable'].get('api_keys')).invoke({"system_message": get_system_message(config['configurable'].get('project')), "messages": state["messages"]})
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

def get_graph(api_keys:ApiKeys):
    workflow = StateGraph(MessagesState,ConfigSchema)
    tool_node = ToolNode(get_tools(api_keys))
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")
    graph =workflow.compile(checkpointer=checkpointer)
    return graph