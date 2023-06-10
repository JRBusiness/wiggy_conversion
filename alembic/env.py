import logging
import os
import sys

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

import settings
from app.shared.bases.base_model import ModelMixin
from settings import base_dir as app_base_dir

logging.basicConfig(
    filename=f"{app_base_dir}/logs/alembic.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="a",
    datefmt="%d-%b-%y %H:%M:%S",
    force=True,
)
logger = logging.getLogger("alembic")

# for route in APIPrefix.include:
#     try:
#         exec(f"from app.api.{route}.models import ModelMixin as Base")
#     except ImportError as e:
#         logger.error(f"Route {route} has no tables defined")
#
# for route in Games.include:
#     try:
#         exec(f"from app.games.{route}.models import ModelMixin as Base")
#     except ImportError as e:
#         logger.error(f"Route {route} has no tables defined")

from app.shared.bases.base_model import ModelMixin as Base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(BASE_DIR)
config = context.config
url = f"postgresql+psycopg2://{settings.Config.postgres_connection}"
config.set_main_option("sqlalchemy.url", url)
alembic_config = config.get_section(config.config_ini_section)
connectable = engine_from_config(
    alembic_config, prefix="sqlalchemy.", poolclass=pool.NullPool
)

target_base = Base.metadata

with connectable.connect() as connect:
    context.configure(
        connection=connect, target_metadata=target_base, include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()
