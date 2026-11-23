import logging

from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.core.logging import setup_logging

from .module import init_pandora_server, shutdown_pandora_server
from .router import router as pandora_server_router
from .pandora_wheels.router import router as wheels_router
from .pandora_relays.router import router as relays_router

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(pandora_server_router)
api_router.include_router(wheels_router)
api_router.include_router(relays_router)



def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):

    setup_logging()

    # startup
    logger.info("Starting PANDORA Control Server API")
    init_pandora_server()

    yield  # run the app

    # shutdown
    logger.info("Shutting down PANDORA Control Server API")
    shutdown_pandora_server()

app = FastAPI(
    title="PANDORA Control Server API",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that catches ALL unhandled exceptions
    """
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url, exc)

    # Map specific exception types to appropriate HTTP status codes
    status_code = 500
    error_type = type(exc).__name__

    if isinstance(exc, ValueError):
        status_code = 400
    elif isinstance(exc, ConnectionError):
        status_code = 503
    elif isinstance(exc, FileNotFoundError):
        status_code = 404
    elif isinstance(exc, PermissionError):
        status_code = 403
    elif hasattr(exc, "status_code"):  # For custom exceptions
        status_code = exc.status_code

    return JSONResponse(
        status_code=status_code,
        content={
            "message": str(exc),
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
        },
    )
