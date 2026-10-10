import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_client import Counter, Histogram, make_asgi_app
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.errors import http_exception_handler, validation_exception_handler, unhandled_exception_handler
from app.db.session import engine
from app.models import Base
from app.api.routes import router

configure_logging(settings.log_level)
logger = logging.getLogger("fowforge")
REQUESTS = Counter("fowforge_requests_total", "Total API requests", ["method", "path", "status"])
LATENCY = Histogram("fowforge_request_latency_seconds", "API request latency", ["method", "path"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="FowForge API", version="2.0.0", lifespan=lifespan)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    path = request.url.path
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(request.method, path).observe(elapsed)
    logger.info("request method=%s path=%s status=%s latency_ms=%.2f", request.method, path, response.status_code, elapsed * 1000, extra={"request_id": request_id})
    return response


app.include_router(router, prefix="/api")
app.mount("/metrics", make_asgi_app())
