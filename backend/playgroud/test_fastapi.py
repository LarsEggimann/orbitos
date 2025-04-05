from typing import Union
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from contextlib import asynccontextmanager
from sqlmodel import Field, Session, SQLModel, create_engine

# env stuff (just for testing)
SECRET_KEY = "414e9fc8fe74444cefe3b216f9034aba3f669da8e59ca97644425634d7b6626c"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


# setup
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str, session: Session):
    user = get_user(username, session)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# database
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class User(SQLModel, BaseModel, table=True):
    username: str = Field(index=True, primary_key=True)
    email: str | None = Field(default=None, index=True)
    full_name: str | None = Field(default=None, index=True)
    hashed_password: str | None = Field(default=None, index=True)
    disabled: bool | None = Field(default=False, index=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup database
    create_db_and_tables()

    yield  # run the app

    # cleanup


app = FastAPI(lifespan=lifespan)


def get_user(username: str | None, session: SessionDep):
    if username:
        return session.get(User, username)


async def get_user_by_username(
    username: str,
    session: SessionDep,
):
    user = session.get(User, username)
    if user:
        return user
    return None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/user")
async def create_user(user: User, session: SessionDep):
    user_data = user.model_dump(exclude_unset=True)
    db_user = User.model_validate(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/token")
async def read_tokens(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


itemlist: list[Item] = []


@app.get("/items")
def read_items():
    return {i: item for i, item in enumerate(itemlist)}


@app.put("/items")
def update_item(item: Item):
    itemlist.append(item)
    return item
