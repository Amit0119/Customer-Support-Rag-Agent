from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables (e.g. GROQ_API_KEY)
load_dotenv()

from rag_engine import RAGEngine
import logging

app = FastAPI(title="GigaCorp Customer Support API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount the static frontend directory
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize RAG Engine globally
rag_engine = RAGEngine()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_query: str
    chat_history: List[Message] = []

class SourceDocument(BaseModel):
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument] = []

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def serve_index():
    return FileResponse("frontend/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert Pydantic models to dicts for RAGEngine
        formatted_history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
        
        response_data = rag_engine.get_response(
            user_query=request.user_query,
            chat_history=formatted_history
        )
        
        # Format sources to strings to send over JSON
        sources_list = []
        for doc in response_data.get("sources", []):
            sources_list.append(SourceDocument(content=doc.page_content.strip()))
            
        return ChatResponse(
            answer=response_data.get("answer", "No answer found."),
            sources=sources_list
        )
    except Exception as e:
        logging.error(f"Error processing chat request: {str(e)}")
        return ChatResponse(
            answer="I'm sorry, I encountered an internal error. Please try again later.",
            sources=[]
        )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
