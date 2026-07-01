import os
import chromadb

def test_full_document_upload_integration(client):
    """
    Live Integration Test:
    Simulates a user registering, logging in, and uploading a document.
    """
    
    # 1. READ THE REAL TEST PDF
    # Get the absolute path to the dummy.pdf file located in this exact folder
    current_dir = os.path.dirname(__file__)
    pdf_path = os.path.join(current_dir, "dummy.pdf")
    
    assert os.path.exists(pdf_path), "Please place a dummy.pdf file inside the tests/ folder!"

    # 2. AUTHENTICATION BYPASS
    auth_credentials = {"email": "test@example.com", "password": "password123"} 
    
    register_response=client.post('/auth/register', json=auth_credentials)
    
    login_response = client.post('/auth/login', json=auth_credentials)

    jwt_token = login_response.get_json().get("token") 
    assert jwt_token is not None, "Login failed: No JWT token returned!"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    # 3. TRIGGER THE API ROUTE WITH THE REAL FILE
    # We must open the file in binary read mode ('rb') right when we send it
    with open(pdf_path, 'rb') as f:
        data = {
            'file': (f, 'dummy.pdf')
        }
        
        response = client.post(
            '/documents/upload', 
            data=data, 
            content_type='multipart/form-data',
            headers=headers
        )
    # 4. ASSERTIONS
    assert response.status_code == 201, f"Expected 200 but got {response.status_code}. Response: {response.data}"
    
    response_json = response.get_json()
    assert response_json is not None, "Backend did not return valid JSON"
    assert "success" in response_json.get("status", "").lower() or "success" in response_json.get("message", "").lower(), \
        f"Unexpected JSON message structure: {response_json}"

    # 5. DATABASE VERIFICATION 
    test_db_path = os.getenv("CHROMA_PATH", "./test_chroma_db")
    assert os.path.exists(test_db_path), f"Database directory wasn't created at {test_db_path}!"
    
    test_client = chromadb.PersistentClient(path=test_db_path)
    collections = [col.name for col in test_client.list_collections()]
    
    assert len(collections) > 0, "No vector collections were written into the test database!"

def test_ask_question_retrieval_and_generation(client):
    """
    Integration Test: 
    Verifies that the system can retrieve chunks and generate an answer 
    for a question based on the document uploaded in the previous test.
    """
    # 1. ARRANGE: Define the question for the doc we uploaded earlier
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
    
    query_data = {
        "question": "My name is Bob?",
        "document_id": valid_doc_id,
    }
    
    # 2. ACT: Hit the ask/query route
    response = client.post(
        '/documents/ask', 
        json=query_data, 
        headers=headers
    )

    # 3. ASSERT: Validate the response
    assert response.status_code == 200, f"Ask route failed with {response.status_code}"
    
    response_json = response.get_json()
    assert "answer" in response_json, "Response missing 'answer' key"
    assert "sources" in response_json, "Response missing 'sources' key"
    
    print(f"✅ AI Answered: {response_json['answer'][:50]}...")