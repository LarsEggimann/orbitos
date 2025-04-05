from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, primary_key=True)
    email: str | None = Field(default=None)
    full_name: str | None = Field(default=None, max_length=255)
    disabled: bool | None = Field(default=False)
    is_superuser: bool | None = Field(default=False)


class User(UserBase, table=True):
    hashed_password: str | None = Field(default=None)


class UserPublic(UserBase):
    pass
