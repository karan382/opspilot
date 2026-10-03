from qdrant_client.models import FieldCondition, Filter, MatchValue

from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from app.core.config import GOOGLE_API_KEY


COLLECTION_NAME = "opspilot_knowledge"
QDRANT_URL = "http://localhost:6333"


@tool
def search_knowledge(
    query: str,
    service: str,
    limit: int = 3,
) -> list[dict]:
    """Search OpsPilot documentation relevant to the current incident.

    Use the exact affected service name. Service-specific documentation and
    global incident-response guidance are eligible results.
    """

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )

    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        url=QDRANT_URL,
    )

    results = vector_store.similarity_search(
        query,
        k=limit,
        filter=Filter(
            should=[
                FieldCondition(
                    key="metadata.service",
                    match=MatchValue(value=service),
                ),
                FieldCondition(
                    key="metadata.service",
                    match=MatchValue(value="global"),
                ),
            ]
        ),
    )

    return [
        {
            "source": result.metadata.get("source"),
            "content": result.page_content,
        }
        for result in results
    ]