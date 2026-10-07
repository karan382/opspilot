from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.core.config import GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY


KNOWLEDGE_DIR = Path("data/knowledge")
COLLECTION_NAME = "opspilot_knowledge"


def load_documents() -> list[Document]:
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.md"):
        documents.append(
            Document(
                page_content=file_path.read_text(),
                metadata={
                    "source": file_path.name,
                    "service": (
                        "recommendation-service"
                        if file_path.name in {
                            "recommendation-service-runbook.md",
                            "database-connection-pooling.md",
                        }
                        else "recommendation-cache-service"
                        if file_path.name == "redis-cache-runbook.md"
                        else "global"
                    ),
                },
            )
        )

    return documents


def ingest_documents() -> None:
    documents = load_documents()

    if not documents:
        raise RuntimeError("No knowledge documents found")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
        force_recreate=True,
    )

    print(f"Loaded {len(documents)} documents")
    print(f"Created {len(chunks)} chunks")


if __name__ == "__main__":
    ingest_documents()