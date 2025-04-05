from typing import Any

from fastapi import APIRouter

from app.deps import SessionDep
from app.core.security import get_password_hash
from app.models.user import (
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(UserPublic):
    """
    UserCreate model for creating a user.
    """

    password: str


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """
    user_in_dict = user_in.model_dump()
    user_in_dict["hashed_password"] = get_password_hash(user_in.password)

    user = User(**user_in_dict)

    session.add(user)
    session.commit()

    return user
