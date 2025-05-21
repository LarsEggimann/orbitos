from fastapi import APIRouter, Depends

router = APIRouter(
    tags=["electrometer"],
    prefix="/electrometer",
)
