"""
main.py — FastAPI entry point & MCP server setup for Criterion AI.

Starts the FastAPI application, mounts the MCP SSE transport so
Gemini (or any MCP-compatible client) can discover and invoke tools,
and exposes a basic health-check endpoint.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import ensure_indexes
from tools import mcp

load_dotenv()

# ---------------------------------------------------------------------------
# Lifespan: runs on startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — setup DB indexes on boot."""
    ensure_indexes()
    print("🚀  Criterion AI backend is live.")
    yield
    print("👋  Criterion AI backend shutting down.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Criterion AI",
    description=(
        "Autonomous O/A Level academic agent — exposes MCP tools for "
        "question fetching, auto-grading, and adaptive weakness tracking."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Mount MCP SSE transport at /mcp
# ---------------------------------------------------------------------------

# The FastMCP instance from tools.py exposes an SSE endpoint that
# MCP-compatible clients (e.g. Gemini on Google Cloud) can connect to
# in order to discover and call our tools.
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)


# ---------------------------------------------------------------------------
# REST endpoints (lightweight — most logic goes through MCP)
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "Criterion AI",
        "version": "0.1.0",
        "status": "healthy",
        "mcp_endpoint": "/mcp",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Run with: uvicorn main:app --reload
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
