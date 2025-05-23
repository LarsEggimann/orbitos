import logging

from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.core.config import config
from src.core.logging import setup_logging
from src.core.db import init_db
from src.modules.electrometer import module as electrometer_module
from src.modules.electrometer.router import router as electrometer_router

logger = logging.getLogger()

api_router = APIRouter()
api_router.include_router(electrometer_router)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # setup logging
    setup_logging()

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
    elif hasattr(exc, 'status_code'):  # For custom exceptions
        status_code = exc.status_code
    
    return JSONResponse(
        status_code=status_code,
        content={
            "message": str(exc),
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )
