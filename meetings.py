import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from utils import pinecone_check_index

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])

class Item(BaseModel):
    user_id: str
    meeting_id: str
    caption: str

def add_meeting_to_db(item:Item):
    pinecone_check_index(pc)
    index = pc.Index(os.environ['PINECONE_VECTOR_NAME'])
    
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)

    doc = Document(page_content=item.caption,
        metadata={
            "user_id":item.user_id,
            "meeting_id":item.meeting_id,
            "source": "meeting"
        }
    )
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200,
    length_function=len,)
    new_chunks = text_splitter.split_documents([doc])
    vector_store.add_documents(new_chunks)