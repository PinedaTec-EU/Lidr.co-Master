from uuid import uuid4

from fastapi import APIRouter

from app.schemas import SessionCreateResponse
from app.sessions import SessionStore

router = APIRouter()
session_store = SessionStore()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    session_id = str(uuid4())
    session_store.create(session_id)
    return SessionCreateResponse(session_id=session_id)
