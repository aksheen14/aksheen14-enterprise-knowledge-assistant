from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set - check your .env file")

# path where chroma will store its data on disk
CHROMA_HOST = os.getenv("CHROMA_SERVER_HOST", "chroma.railway.internal")
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

import traceback
# Ensure your imports include whatever Document class you are using, usually:
# from langchain_core.documents import Document

def embed_and_store(chunks, document_id):
    safe_id = "".join([c for c in str(document_id) if c.isalnum() or c in "-_"]).lower()
    collection_name = f"doc_{safe_id}"
    
    # --- SANITIZE CHUNKS BEFORE ADDING ---
    cleaned_chunks = []
    for chunk in chunks:
        # 1. Skip completely empty chunks
        if not chunk.page_content or not chunk.page_content.strip():
            continue
            
        # 2. Force all metadata values to be Chroma-safe (strings, ints, floats, bools)
        safe_metadata = {}
        for key, value in chunk.metadata.items():
            if value is None:
                continue # Drop None values
            elif isinstance(value, (str, int, float, bool)):
                safe_metadata[key] = value
            else:
                # Convert complex types (lists, dicts) to strings
                safe_metadata[key] = str(value)
                
        # 3. Rebuild the chunk with safe data
        chunk.metadata = safe_metadata
        cleaned_chunks.append(chunk)
    # -------------------------------------

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        vector_store = Chroma(
            client=chroma_client,
            collection_name=collection_name,
            embedding_function=embeddings
        )
    except Exception as e:
        print("\n=== CRASH AT INIT ===")
        traceback.print_exc()
        raise e

    try:
        print(f"DEBUG 3: Adding {len(cleaned_chunks)} sanitized chunks to Chroma...")
        # Make sure you are passing the cleaned_chunks here!
        vector_store.add_documents(cleaned_chunks) 
        print("DEBUG 4: Successfully added documents!")
    except Exception as e:
        print("\n=== CRASH AT ADD_DOCUMENTS ===")
        traceback.print_exc()
        raise e

    return vector_store

def get_vector_store(document_id):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = Chroma(
        client=chroma_client,
        collection_name=f"doc_{document_id}",
        embedding_function=embeddings,
    )
    return vector_store

def answer_question(question, document_id):
    vector_store = get_vector_store(document_id)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question based on the context below.\n\nContext: {context}"),
        ("human", "{input}"),
    ])

    # LCEL chain — pipes data through each step
    chain = (
        {"context": retriever, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke(question)

    # get source documents separately
    source_chunks = retriever.invoke(question)

    return answer, source_chunks