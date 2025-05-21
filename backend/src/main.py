from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from src.core.config import config
from src.core.db import init_db
from src.modules.electrometer import module as electrometer_module

api_router = APIRouter()
api_router.include_router(electrometer_module.router)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

@asynccontextmanager
async def lifespan(app: FastAPI):

    # setup core application
    init_db()

    # setup modules
    electrometer_module.init_module()


    yield  # run the app

    # shutdown
    electrometer_module.shutdown_module()


app = FastAPI(
    title="ORBITOS API",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

app.include_router(api_router, prefix=config.API_V1_STR)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
