# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from db.database import init_db, weaviate_client # Import the client
from routers import auth, chat
from services.rag_service import create_weaviate_schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    await init_db()
    create_weaviate_schema()
    yield
    # On shutdown
    weaviate_client.close() # Key Change: Close the client connection

app = FastAPI(lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
def read_root():
    return {"Hello": "World"}