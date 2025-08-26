# routers/chat.py
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Cookie, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from sqlalchemy import desc, distinct, func

# Import the OpenAI chat model class
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

from db.database import get_db_session
from models.user import Session, User
from models.file import File as FileModel
from models.chat import ChatHistory
from services.rag_service import process_and_embed_file, query_weaviate

router = APIRouter()
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatQuery(BaseModel):
    query: str
    session_id: uuid.UUID

async def get_current_user(session_token: str = Cookie(None), db: AsyncSession = Depends(get_db_session)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(select(Session).where(Session.session_token == session_token))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
MAX_PAGES_ESTIMATE = 300  # Rough estimate for reasonable processing time

@router.post("/upload")
async def upload_file(
    session_id: str = Form(...), # <-- ADD session_id from form data
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    # Check file size before processing
    file_size = 0
    if hasattr(file, 'size') and file.size:
        file_size = file.size
    else:
        # Fallback: read file to check size
        content = await file.read()
        file_size = len(content)
        # Reset file pointer
        await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB. Your file is {file_size // (1024*1024)}MB."
        )

    # Check if file is PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save the file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        if hasattr(file, 'size') and file.size:
            shutil.copyfileobj(file.file, buffer)
        else:
            buffer.write(content)

    # Create file record in PostgreSQL, now with session_id
    new_file = FileModel(
        user_id=current_user.id,
        session_id=uuid.UUID(session_id), # <-- ADD this
        filename=file.filename
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    # Process and embed the file
    try:
        # Pass file_id to link chunks in Weaviate
        chunks_created = process_and_embed_file(file_path, current_user.id, new_file.id)
    except Exception as e:
        await db.delete(new_file)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")
    finally:
        os.remove(file_path)

    return {
        "filename": file.filename,
        "file_id": new_file.id,
        "chunks_created": chunks_created,
        "file_size_mb": round(file_size / (1024*1024), 2),
        "message": f"File uploaded and processed successfully. Created {chunks_created} text chunks for analysis."
    }


# --- UPDATE THE /chat ENDPOINT ---
@router.post("/chat")
async def chat(
    chat_query: ChatQuery,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    session_id = chat_query.session_id # Use the session_id from the request

    # Save user message
    user_message = ChatHistory(user_id=user_id, session_id=session_id, role="user", message=chat_query.query)
    db.add(user_message)

    # Check if files have been uploaded *for this specific session*
    result = await db.execute(select(FileModel).where(FileModel.user_id == user_id, FileModel.session_id == session_id))
    session_has_files = result.scalars().first() is not None

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    if session_has_files:
        # RAG Mode: Query Weaviate using file_ids from the current session
        files_in_session = await db.execute(select(FileModel.id).where(FileModel.user_id == user_id, FileModel.session_id == session_id))
        file_ids = [row[0] for row in files_in_session.all()]

        context_chunks = query_weaviate(chat_query.query, user_id, file_ids) # Pass file_ids to query
        context = "\n---\n".join([chunk['content'] for chunk in context_chunks])

        template = "Answer the question based only on the following context:\n{context}\n\nQuestion: {question}"
        prompt = ChatPromptTemplate.from_template(template)
        rag_chain = ({"context": lambda x: context, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
        response_message = rag_chain.invoke(chat_query.query)
    else:
        # Normal Chat Mode
        response = llm.invoke(chat_query.query)
        response_message = response.content

    # Save assistant message
    assistant_message = ChatHistory(user_id=user_id, session_id=session_id, role="assistant", message=response_message)
    db.add(assistant_message)
    await db.commit()

    return {"response": response_message}

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id, ChatHistory.session_id == session_id)
        .order_by(ChatHistory.timestamp)
    )
    history = result.scalars().all()
    return history

@router.get("/chat/sessions")
async def get_chat_sessions(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # This query gets the most recent message for each session
    subquery = (
        select(
            ChatHistory.session_id,
            ChatHistory.message,
            ChatHistory.timestamp,
            func.row_number().over(
                partition_by=ChatHistory.session_id,
                order_by=desc(ChatHistory.timestamp)
            ).label('rn')
        )
        .where(ChatHistory.user_id == current_user.id)
        .subquery()
    )

    result = await db.execute(
        select(subquery.c.session_id, subquery.c.message, subquery.c.timestamp)
        .where(subquery.c.rn == 1)
        .order_by(desc(subquery.c.timestamp))
    )

    sessions = result.all()
    # Format the data for the frontend
    return [{"id": str(s.session_id), "title": s.message} for s in sessions]

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Delete all chat history for this session
    result = await db.execute(
        select(ChatHistory).where(
            ChatHistory.user_id == current_user.id,
            ChatHistory.session_id == session_id
        )
    )
    chat_messages = result.scalars().all()

    if not chat_messages:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete chat history
    for message in chat_messages:
        await db.delete(message)

    # Delete associated files for this session
    result = await db.execute(
        select(FileModel).where(
            FileModel.user_id == current_user.id,
            FileModel.session_id == session_id
        )
    )
    files = result.scalars().all()

    for file in files:
        await db.delete(file)

    await db.commit()

    return {"message": "Session deleted successfully"}

@router.get("/upload/limits")
async def get_upload_limits():
    """Get current upload limits and recommendations"""
    return {
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "max_pages_estimate": MAX_PAGES_ESTIMATE,
        "supported_formats": ["PDF"],
        "performance_tiers": {
            "fast": {"max_pages": 50, "estimated_time": "10-30 seconds"},
            "medium": {"max_pages": 125, "estimated_time": "30-90 seconds"},
            "slow": {"max_pages": 200, "estimated_time": "2-5 minutes"},
            "very_slow": {"max_pages": 300, "estimated_time": "5+ minutes"}
        },
        "optimization_applied": [
            "Batch embedding processing",
            "Larger chunk sizes (2000 chars)",
            "Smart text splitting",
            "File size validation"
        ]
    }
