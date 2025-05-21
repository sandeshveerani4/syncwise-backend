from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate,MessagesPlaceholder
from tools import tools

Llm = init_chat_model("meta-llama/llama-4-scout-17b-16e-instruct",model_provider="groq",streaming=True,temperature=0.35)


prompt_template = ChatPromptTemplate(
    [
        ("system", "{system_message}"),
        MessagesPlaceholder("messages")
    ]
)

with_tools=Llm.bind_tools(tools=tools)
llm=prompt_template|with_tools
