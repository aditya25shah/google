from apis.v1 import agent
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(agent.router, tags=["agent"])