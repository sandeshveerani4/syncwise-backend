from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from tools import tools

Llm = init_chat_model("gpt-4.1-mini",model_provider="openai",streaming=True,temperature=0.4)

prompt_template = ChatPromptTemplate(
    [
        ("system", "{system_message}"),
        MessagesPlaceholder("messages")
    ]
)

with_tools=Llm.bind_tools(tools=tools)
llm=prompt_template|with_tools
