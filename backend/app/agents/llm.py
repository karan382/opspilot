from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import GOOGLE_API_KEY
from app.models.investigation import InvestigationReport
from app.tools.logs import search_logs


llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=GOOGLE_API_KEY,
)

llm_with_tools = llm.bind_tools([search_logs])

structured_llm = llm.with_structured_output(InvestigationReport)