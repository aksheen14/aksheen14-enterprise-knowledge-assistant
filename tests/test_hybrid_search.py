import pytest
from backend.rag import get_hybrid_retriever
import os
import chromadb
# Import your EnsembleRetriever components here

def test_hybrid_search_retrieval(client):
    # 1. Arrange: Use a document with a unique keyword AND a semantic concept
    #    E.g., "The project is called 'Part-Alpha-99' (Unique keyword). 
    #    It involves team collaboration (Semantic concept)."
    
    auth_credentials = {"email": "test@example.com", "password": "password123"}
    login_response = client.post('/auth/login', json=auth_credentials)
    jwt_token = login_response.get_json().get("token")
    headers = {"Authorization": f"Bearer {jwt_token}"}

    print("\n🔍 Fetching documents to find a valid ID...")
    get_docs_response = client.get('/documents', headers=headers)
    assert get_docs_response.status_code == 200
    
    docs = get_docs_response.get_json()
    assert len(docs) > 0, "No documents found in the database!"

    # Grab the ID of the first document returned
    valid_doc_id = str(docs[-1]['id'])
    
    retriever = get_hybrid_retriever(valid_doc_id) # Your function that returns EnsembleRetriever
    
    # 2. Act: Run the literal search
    literal_results = retriever.invoke("CSE 31")
    
    # 3. Act: Run the semantic search
    semantic_results = retriever.invoke("What are Machine Structures?")
    
    # 4. Assert
    assert any("CSE 31" in doc.page_content for doc in literal_results), "BM25 failed to find literal match"
    assert len(semantic_results) > 0, "Vector search failed to return any semantic matches"