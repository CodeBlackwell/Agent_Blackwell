"""
Main FastAPI application for Agent Blackwell API.

This module initializes and configures the FastAPI application,
including all API routers and middleware.
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import dependencies
from src.api.dependencies import initialize_orchestrator, shutdown_orchestrator
from src.api.metrics import PrometheusMiddleware, metrics_router
from src.api.v1.chatops.platforms.slack import router as slack_router

# Import routers
from src.api.v1.chatops.router import router as chatops_router
from src.api.v1.feature_request.router import router as feature_request_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for initialization and cleanup."""
    # Initialize shared resources
    logger.info("Initializing application resources")
    try:
        await initialize_orchestrator()
        yield
    finally:
        # Clean up resources
        logger.info("Shutting down application resources")
        await shutdown_orchestrator()


# Create app
app = FastAPI(
    title="Agent Blackwell API",
    description="API for the Agent Blackwell orchestration system",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers for monitoring."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Include routers
app.include_router(chatops_router)
app.include_router(slack_router)
app.include_router(feature_request_router)
app.include_router(metrics_router)


# Root endpoint
@app.get("/", tags=["Health Check"])
async def root():
    """Root endpoint for health check."""
    return {
        "name": "Agent Blackwell API",
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint."""
    # Check the status of various services
    health_status = {
        "api": "up",
        "redis": "unknown",
        "slack": "unknown",
    }

    # Check Redis if configured
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis.asyncio as redis

            redis_client = redis.from_url(redis_url)
            await redis_client.ping()
            health_status["redis"] = "up"
            await redis_client.close()
        except Exception:
            health_status["redis"] = "down"

    # Check Slack configuration
    slack_token = os.getenv("SLACK_API_TOKEN")
    slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    if slack_token and slack_signing_secret:
        health_status["slack"] = "configured"

    return {
        "status": all(v in ["up", "configured"] for v in health_status.values())
        and "healthy"
        or "degraded",
        "services": health_status,
    }


if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))

    # Start the API server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload during development
    )
