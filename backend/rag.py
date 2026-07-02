from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
from operator import itemgetter
from langchain_community.retrievers.bm25 import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set - check your .env file")

chroma_path = os.getenv("CHROMA_PATH")

if chroma_path:
    # TEST MODE: Save to the local folder defined in .env.test
    print(f"🔧 RUNNING IN TEST MODE: Using local ChromaDB at {chroma_path}")
    chroma_client = chromadb.PersistentClient(path=chroma_path)
else:
    CHROMA_HOST = os.getenv("CHROMA_SERVER_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_SERVER_PORT", 8000))

    # This connects to the separate Chroma service instead of a local folder
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

collection = chroma_client.get_or_create_collection(name="your_collection_name")
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
        client=chroma_client,
        collection_name=f"doc_{document_id}",
        embedding_function=embeddings
    )
    vector_store.add_documents(chunks)
    return vector_store

def get_vector_store(document_id):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = Chroma(
        client=chroma_client,
        collection_name=f"doc_{document_id}",
        embedding_function=embeddings,
    )
    return vector_store

def answer_question(question, document_id, chat_history=None):
    if chat_history is None:
        chat_history = []

    # 1. Setup Retriever & Fetch Sources immediately
    ensemble_retriever = get_hybrid_retriever(document_id)
    source_chunks = ensemble_retriever.invoke(question)

    # 2. Setup LLM & Prompt
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question based on the context below.\n\nContext: {context}"),
        MessagesPlaceholder(variable_name="chat_history"), 
        ("human", "{input}"),
    ])

    # 3. Build LCEL Chain
    chain = (
        {
            "context": lambda x: source_chunks, 
            "input": itemgetter("input"),
            "chat_history": itemgetter("chat_history")
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    # 4. STREAM INSTEAD OF INVOKE
    # This now returns a generator that yields text chunks, rather than a single string
    answer_generator = chain.stream({
        "input" : question,
        "chat_history": chat_history
    })

    # Return both the generator and the source chunks so the route can handle them
    return answer_generator, source_chunks
    
def get_hybrid_retriever(document_id, k=4):
    vector_store = get_vector_store(document_id)
    
    # Vector Retriever
    vector_retriever = vector_store.as_retriever(search_kwargs={"k": k})
    
    # BM25 Retriever
    raw_data = vector_store.get()
    docs = [
        Document(page_content=text, metadata=meta) 
        for text, meta in zip(raw_data['documents'], raw_data['metadatas'])
    ]
    keyword_retriever = BM25Retriever.from_documents(docs)
    keyword_retriever.k = k
    
    # Ensemble
    return EnsembleRetriever(
        retrievers=[vector_retriever, keyword_retriever], 
        weights=[0.5, 0.5]
    )