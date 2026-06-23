from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set - check your .env file")

# path where chroma will store its data on disk
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_store")



def load_and_chunk(file_path):
    loader = PyPDFLoader(file_path=file_path) #docloader
    pages = loader.load()
    #textsplitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(pages)  # then split the pages into chunks

    return chunks 

def embed_and_store(chunks, document_id):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = Chroma(
        collection_name=str(document_id),
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH  # Where to save data locally, remove if not necessary
    )
    vector_store.add_documents(chunks)
    return vector_store

def get_vector_store(document_id):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = Chroma(
        collection_name=str(document_id),
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH  # Where to save data locally, remove if not necessary
    )
    return vector_store
def answer_question(question, document_id):
    vector_store = get_vector_store(document_id)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )
    qa = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=retriever, 
        return_source_documents=True
    )
    result = qa.invoke({"query": question})
    answer = result["result"]
    sources = result["source_documents"]
    
    return answer, sources


