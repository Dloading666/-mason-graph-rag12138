"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.config.settings import settings
from backend.graphrag_core.runtime import bootstrap_runtime
from backend.server.api.endpoints import auth, document, evaluation, feedback, graph, jobs, qa, research, traces


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_runtime()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="建材企业私有化 GraphRAG 智能问答系统 API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["qa"])
app.include_router(research.router, prefix="/api/v1/research", tags=["research"])
app.include_router(document.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(traces.router, prefix="/api/v1/traces", tags=["traces"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["evaluation"])


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str | bool]:
    return {
        "status": "success",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "neo4j_enabled": settings.NEO4J_ENABLED,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.error("HTTP exception on {}: {} {}", request.url.path, exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on {}: {}", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误，请联系管理员", "data": None},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn_kwargs = {
        "app": "backend.server.api.main:app",
        "host": settings.HOST,
        "port": settings.PORT,
    }
    if settings.DEV_MODE:
        uvicorn_kwargs["reload"] = True
    else:
        uvicorn_kwargs["workers"] = 4
    uvicorn.run(**uvicorn_kwargs)
