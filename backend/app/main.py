import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown hooks."""
    logger.info("Initializing YouTube Shorts AI Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL} ({settings.EMBEDDING_DIMENSIONS} dimensions)")
    yield
    logger.info("Shutting down YouTube Shorts AI Backend...")


app = FastAPI(
    title="YouTube Shorts AI — Backend API",
    description="A RAG-powered pipeline that turns any YouTube video into ready-to-post Shorts scripts with exact source timestamps.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration - Allow all origins for seamless Vercel / Render / Localhost deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Guarantees CORS headers on every single response including OPTIONS preflights and errors."""
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        response = Response(status_code=200)
    else:
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"Middleware caught unhandled error on {request.url.path}: {exc}", exc_info=True)
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An internal server error occurred.", "error": str(exc)},
            )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# Register API routes
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception catcher to guarantee structured JSON errors with CORS headers."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.api_route("/", methods=["GET", "HEAD"], tags=["Root"])
async def root():
    """Root landing endpoint with system status and documentation links (supports Render HEAD health checks)."""
    return {
        "name": "YouTube Shorts AI API",
        "version": "1.0.0",
        "documentation": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
    }
