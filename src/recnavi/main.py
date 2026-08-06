# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Starting server."""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

from recnavi.apis.schemas.response_schemas import GreetingResponse
from recnavi.config.variables import ENV
from recnavi.exceptions.error_handler import custom_exception_handler
from recnavi.exceptions.error_handler import send_error_alert
from recnavi.exceptions.error_handler import send_notice


BASE_DIR = Path(__file__).resolve().parent
API_DESCRIPTION_PATH = BASE_DIR / "apis" / "api_description.md"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan function."""
    logger.info("start booting server.")
    try:
        await send_notice(
            subject=f"{ENV}: ECS Task started!",
            message=f"{ENV}: ECS task started.",
        )
        logger.info("server initialize succeed.")
        yield

    except Exception as e:
        logger.critical("Server startup failed", exc_info=True)
        await send_error_alert(
            "lifespan_startup", e, kwargs={"phase": "startup"}
        )
        raise

    finally:
        logger.info("shutdown server")


app = FastAPI(
    title="TRUST API",
    description=API_DESCRIPTION_PATH.read_text(encoding="utf-8"),
    lifespan=lifespan,
)

app.add_middleware(
    ServerErrorMiddleware,  # noqa: type
    handler=custom_exception_handler,
)

app.add_middleware(
    CORSMiddleware,  # noqa: type
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(root_router)
app.include_router(cms_router)
app.include_router(pub_router)


@app.middleware("http")
async def cache_request_body(request: Request, call_next):
    """Cache request body."""
    body_bytes = await request.body()
    request.state.body = body_bytes
    response = await call_next(request)
    return response


@app.get("/health")
def health_check():
    """Health check api."""
    return {"status": "ok"}


@app.get("/greeting")
async def greeting():
    """Test API endpoint **without** authentication."""
    return {
        "status": "ok",
        "timestamp": int(time.time()),
        "environment": ENV,
    }


@app.post("/greetingMe", response_model=GreetingResponse)
async def greeting_me(
    request: Request,
    x_user: XUser = Depends(verify_user),
) -> GreetingResponse:
    """Task status check API for pooling."""
    _ = request
    return GreetingResponse(x_user=x_user)
