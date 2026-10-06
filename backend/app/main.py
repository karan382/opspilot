from app.api.investigations import router as investigations_router
from app.api.incidents import router as incidents_router

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS

app = FastAPI(
    title="OpsPilot API",
    description="Agentic AI platform for production incident investigation",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(investigations_router)
app.include_router(incidents_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
