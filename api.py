import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import json
import glob
from sse_starlette.sse import EventSourceResponse

# Ensure project root is on sys.path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from pipeline.retriever import retrieve
from pipeline.prompt_builder import build_prompt
from pipeline.answerer import stream_answer
import db

DB_DIR = ROOT / "vector_db"

app = FastAPI(title="HVAC Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Models ---
class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/api/register")
def register(req: AuthRequest):
    user_id = db.create_user(req.username, req.password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"user_id": user_id, "username": req.username}

@app.post("/api/login")
def login(req: AuthRequest):
    user_id = db.verify_user(req.username, req.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"user_id": user_id, "username": req.username}

# --- Chat History Models ---
@app.get("/api/chats")
def get_chats(user_id: int):
    return {"chats": db.get_user_chats(user_id)}

@app.get("/api/chats/{chat_id}")
def get_chat_history(chat_id: str):
    return {"messages": db.get_chat_messages(chat_id)}

class ChatRequest(BaseModel):
    query: str
    user_id: int
    chat_id: Optional[str] = None
    top_k: int = 5
    chunk_type: Optional[str] = None

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # Resolve chat_id
        chat_id = req.chat_id
        if not chat_id:
            # Use the first few words as title
            title = " ".join(req.query.split()[:5]) + "..."
            chat_id = db.create_chat(req.user_id, title)
            
        # Save user message
        db.add_message(chat_id, "user", req.query)

        # Retrieve and build
        chunks = retrieve(req.query, DB_DIR, k=req.top_k, chunk_type=req.chunk_type)
        messages = build_prompt(req.query, chunks)

        async def event_generator():
            full_response = ""
            try:
                # Send chat_id first so frontend knows it
                yield {
                    "event": "meta",
                    "data": json.dumps({"chat_id": chat_id})
                }
                
                # Stream the tokens
                for token in stream_answer(messages):
                    full_response += token
                    yield {
                        "event": "token",
                        "data": json.dumps({"text": token})
                    }
                
                # Save assistant message
                db.add_message(chat_id, "assistant", full_response)
                
                # After streaming the answer, send the sources
                yield {
                    "event": "sources",
                    "data": json.dumps({"chunks": chunks})
                }
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"detail": str(e)})
                }
                
        return EventSourceResponse(event_generator())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/{image_id}")
async def get_image(image_id: str):
    images_dir = ROOT / "images"
    pattern = str(images_dir / f"{image_id}.*")
    matches = glob.glob(pattern)
    matches = [m for m in matches if not m.endswith('.json')]
    
    if not matches:
        raise HTTPException(status_code=404, detail="Image not found")
        
    return FileResponse(matches[0])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
