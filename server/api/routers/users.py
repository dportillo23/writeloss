from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from mock_users import users_db

router = APIRouter(prefix='/users')

@router.get('/')
async def users():
    return users_db