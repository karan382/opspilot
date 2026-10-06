from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.core.config import GOOGLE_API_KEY, QDRANT_URL


COLLECTION_NAME = "opspilot_knowledge"


def search_knowledge(query: str, limit: int = 3):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )

    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        url=QDRANT_URL,
    )

    return vector_store.similarity_search(query, k=limit)


if __name__ == "__main__":
    results = search_knowledge(
        "What are the symptoms of database connection pool exhaustion?"
    )

    for result in results:
        print(f"\nSOURCE: {result.metadata['source']}")
        print(result.page_content)