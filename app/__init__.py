import logging

import sentry_sdk
from fastapi import FastAPI

from starlette.responses import RedirectResponse

from app.shared.bases.base_model import ModelMixin
from app.webhook.views import router as webhook_router
from fastapi_sqlalchemy import DBSessionMiddleware, db
from settings import Config

from app.shared.middleware.auth import JWTBearer
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sentry_sdk
# logger.configure(
#     handlers=[
#         {
#             "sink": "app.log", "level": logging.DEBUG,
#             "format": "{time} {level} {message}",
#             "rotation": "1 week",
#             "retention": "10 days",
#             "compression": "zip",
#             "enqueue": True,
#             "backtrace": True,
#             "diagnose": True,
#
#         }
#
#     ]
# )

# sentry_sdk.init(
#     # ...
#     integrations=[
#         StarletteIntegration(transaction_style="url"),
#         FastApiIntegration(transaction_style="url"),
#
#     ],
# )
app = FastAPI()

sentry_sdk.init(
    traces_sample_rate=1.0,
    dsn="https://2b423e58b39c41eeb25db4c33b9203eb@o1351112.ingest.sentry.io/4505433874235392",
    max_breadcrumbs=100,
    debug=True,
    environment="development",
    release="ouroboros@0.0.1",
    send_default_pii=True,
    attach_stacktrace=True,
    request_bodies="always",
    profiles_sample_rate=1.0,


)


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/docs")


app.add_middleware(
    DBSessionMiddleware,
    db_url=f"postgresql+psycopg2://{Config.postgres_connection}",
    engine_args={"pool_size": 100000, "max_overflow": 10000},
)

origins = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "https://baohule-dashboard.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(AuthenticationMiddleware, backend=JWTBearer())

logger.debug("Middleware registered")

logger.debug("Database connection established")

app.build_middleware_stack()
app.include_router(webhook_router)

with db():
    ModelMixin.set_session(db.session)


# socket = SocketManager(app)

#


# redis = RedisServices().redis
