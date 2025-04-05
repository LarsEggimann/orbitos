from typing import Any

from fastapi import APIRouter, Depends

from app.deps import reusable_oauth2, CurrentActiveUser
from app.models.user import UserPublic

router = APIRouter(dependencies=[Depends(reusable_oauth2)], tags=["users"])


@router.get("/user/me", response_model=UserPublic)
def get_own_user(user: CurrentActiveUser) -> Any:
    """
    get own user
    """
    return user


@router.get("/test")
def test_auth():
    """
    test auth
    """
    return {"msg": "ok"}
