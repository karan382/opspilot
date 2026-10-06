from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY

COLLECTION_NAME = "opspilot_knowledge"


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

    query_vector = embeddings.embed_query(query)

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30,
    )

    service_filter = Filter(
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
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=service_filter,
        limit=limit,
    )

    return [
        {
            "source": point.payload.get("metadata", {}).get("source"),
            "service": point.payload.get("metadata", {}).get("service"),
            "chunk_index": point.payload.get("metadata", {}).get("chunk_index"),
            "content": point.payload.get("page_content", ""),
        }
        for point in results.points
    ]