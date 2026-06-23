import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

import backend.rag as rag


def test_load_and_chunk_returns_chunks(monkeypatch):
    fake_loader = MagicMock()
    fake_loader.load.return_value = ["page1", "page2"]
    monkeypatch.setattr(rag, "PyPDFLoader", MagicMock(return_value=fake_loader))

    fake_splitter = MagicMock()
    fake_splitter.split_documents.return_value = ["chunk1", "chunk2"]
    monkeypatch.setattr(rag, "RecursiveCharacterTextSplitter", MagicMock(return_value=fake_splitter))

    chunks = rag.load_and_chunk("dummy.pdf")

    rag.PyPDFLoader.assert_called_once_with(file_path="dummy.pdf")
    rag.RecursiveCharacterTextSplitter.assert_called_once_with(chunk_size=500, chunk_overlap=50)
    fake_splitter.split_documents.assert_called_once_with(["page1", "page2"])
    assert chunks == ["chunk1", "chunk2"]


def test_embed_and_store_persists_chunks(monkeypatch):
    embeddings_instance = MagicMock()
    monkeypatch.setattr(rag, "OpenAIEmbeddings", MagicMock(return_value=embeddings_instance))

    vector_store_mock = MagicMock()
    monkeypatch.setattr(rag, "Chroma", MagicMock(return_value=vector_store_mock))

    chunks = ["chunkA", "chunkB"]
    vector_store = rag.embed_and_store(chunks, document_id=99)

    rag.OpenAIEmbeddings.assert_called_once_with(model="text-embedding-3-large")
    rag.Chroma.assert_called_once_with(
        collection_name="doc_99",
        embedding_function=embeddings_instance,
        persist_directory=rag.CHROMA_PATH,
    )
    vector_store_mock.add_documents.assert_called_once_with(chunks)
    assert vector_store is vector_store_mock


def test_get_vector_store_uses_correct_collection_name(monkeypatch):
    embeddings_instance = MagicMock()
    monkeypatch.setattr(rag, "OpenAIEmbeddings", MagicMock(return_value=embeddings_instance))

    vector_store_mock = MagicMock()
    monkeypatch.setattr(rag, "Chroma", MagicMock(return_value=vector_store_mock))

    vector_store = rag.get_vector_store(document_id=42)

    rag.OpenAIEmbeddings.assert_called_once_with(model="text-embedding-3-large")
    rag.Chroma.assert_called_once_with(
        collection_name="doc_42",
        embedding_function=embeddings_instance,
        persist_directory=rag.CHROMA_PATH,
    )
    assert vector_store is vector_store_mock


class SimpleChain:
    def __init__(self, answer):
        self.answer = answer

    def __or__(self, other):
        return self

    def __ror__(self, other):
        return self

    def invoke(self, *args, **kwargs):
        return self.answer


def test_answer_question_returns_answer_and_sources(monkeypatch):
    source_doc = MagicMock(page_content="Hello world", metadata={"page": 3})

    retriever = MagicMock()
    retriever.invoke.return_value = [source_doc]

    vector_store = MagicMock()
    vector_store.as_retriever.return_value = retriever

    monkeypatch.setattr(rag, "get_vector_store", MagicMock(return_value=vector_store))
    monkeypatch.setattr(rag, "ChatPromptTemplate", MagicMock(from_messages=classmethod(lambda cls, messages: SimpleChain("mock-answer"))))
    monkeypatch.setattr(rag, "RunnablePassthrough", MagicMock(return_value=MagicMock()))
    monkeypatch.setattr(rag, "ChatOpenAI", MagicMock(return_value=SimpleChain("ignored")))
    monkeypatch.setattr(rag, "StrOutputParser", MagicMock(return_value=SimpleChain("ignored")))

    answer, sources = rag.answer_question("What is the answer?", document_id=123)

    assert answer == "mock-answer"
    assert sources == [source_doc]
    retriever.invoke.assert_called_once_with("What is the answer?")


def test_answer_question_uses_retriever_search_kwargs(monkeypatch):
    retriever = MagicMock()
    retriever.invoke.return_value = []

    vector_store = MagicMock()
    vector_store.as_retriever.return_value = retriever

    monkeypatch.setattr(rag, "get_vector_store", MagicMock(return_value=vector_store))
    monkeypatch.setattr(rag, "ChatPromptTemplate", MagicMock(from_messages=classmethod(lambda cls, messages: SimpleChain("ignored"))))
    monkeypatch.setattr(rag, "RunnablePassthrough", MagicMock(return_value=MagicMock()))
    monkeypatch.setattr(rag, "ChatOpenAI", MagicMock(return_value=SimpleChain("ignored")))
    monkeypatch.setattr(rag, "StrOutputParser", MagicMock(return_value=SimpleChain("ignored")))

    rag.answer_question("Test question", document_id=22)

    vector_store.as_retriever.assert_called_once_with(search_kwargs={"k": 4})
