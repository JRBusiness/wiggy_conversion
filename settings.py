from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
base_dir = f"{os.path.dirname(os.path.abspath(__file__))}"


class Config:
    # APP
    fastapi_key: str = "ff8f5d6e-9ed8-4d62-b343-e151ddd32715"
    agent_key: str = "a33e748b-054d-462c-bcf5-2c5880394a17"
    jwt_algo: str = "HS256"
    admin_key: str = "a33e748b-054d-462c-bcf5-2c5880394a17"
    postgres_connection = os.getenv(
        "POSTGRES_CONNECTION", "postgres:1121@localhost:5432/stocks"
    )

    MAX_TRADES = os.getenv("MAX_TRADES", 6)
    MAX_LONG_TRADES = os.getenv("MAX_LONG_TRADES", 3)
    MAX_SHORT_TRADES = os.getenv("MAX_SHORT_TRADES", 3)
    APP_NAME = os.getenv("APP_NAME", "FastAPI")
    APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "FastAPI")
    APP_VERSION = os.getenv("APP_VERSION", "0.0.1")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = os.getenv("APP_PORT", 8005)
    APP_DEBUG = os.getenv("APP_DEBUG", True)
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "debug")
    APP_LOG_FILE = os.getenv("APP_LOG_FILE", "app.log")
    APP_LOG_FILE_MAX_BYTES = os.getenv("APP_LOG_FILE_MAX_BYTES", 1024)
    APP_LOG_FILE_BACKUP_COUNT = os.getenv("APP_LOG_FILE_BACKUP_COUNT", 3)
    APP_LOG_FORMAT = os.getenv(
        "APP_LOG_FORMAT", "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    APP_LOG_DATE_FORMAT = os.getenv("APP_LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
    APP_LOG_FORCE = os.getenv("APP_LOG_FORCE", True)
    APP_LOG_STREAM = os.getenv("APP_LOG_STREAM", True)
    APP_LOG_STREAM_LEVEL = os.getenv("APP_LOG_STREAM_LEVEL", "debug")
    APP_LOG_STREAM_FORMAT = os.getenv(
        "APP_LOG_STREAM_FORMAT", "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    APP_LOG_STREAM_DATE_FORMAT = os.getenv(
        "APP_LOG_STREAM_DATE_FORMAT", "%Y-%m-%d %H:%M:%S"
    )
    APP_LOG_STREAM_FORCE = os.getenv("APP_LOG_STREAM_FORCE", True)
    APP_LOG_STREAM_STREAM = os.getenv("APP_LOG_STREAM_STREAM", True)
    APP_LOG_STREAM_COLORIZE = os.getenv("APP_LOG_STREAM_COLORIZE", True)
    APP_LOG_STREAM_BACKTRACE = os.getenv("APP_LOG_STREAM_BACKTRACE", True)
    APP_LOG_STREAM_BACKTRACE_HIDDEN = os.getenv("APP_LOG_STREAM_BACKTRACE_HIDDEN", True)
    APP_LOG_STREAM_BACKTRACE_STYLE = os.getenv(
        "APP_LOG_STREAM_BACKTRACE_STYLE", "darkbg2"
    )

    # DATABASE

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", 5432)
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_POOL_MIN_SIZE = os.getenv("DB_POOL_MIN_SIZE", 10)
    DB_POOL_MAX_SIZE = os.getenv("DB_POOL_MAX_SIZE", 20)
    DB_POOL_MAX_QUERIES = os.getenv("DB_POOL_MAX_QUERIES", 50000)
    DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME = os.getenv(
        "DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME", 300
    )
    DB_POOL_TIMEOUT = os.getenv("DB_POOL_TIMEOUT", 30)
    DB_ECHO = os.getenv("DB_ECHO", True)
    DB_SSL = os.getenv("DB_SSL", False)
    DB_USE_CONNECTION_FOR_REQUEST = os.getenv("DB_USE_CONNECTION_FOR_REQUEST", True)
    DB_RETRY_LIMIT = os.getenv("DB_RETRY_LIMIT", 3)
    DB_RETRY_INTERVAL = os.getenv("DB_RETRY_INTERVAL", 1)
    DB_RETRY_INTERVAL_UNIT = os.getenv("DB_RETRY_INTERVAL_UNIT", "seconds")
    DB_RETRY_TIMEOUT = os.getenv("DB_RETRY_TIMEOUT", 10)

    # JWT

    APP_JWT_HASH = os.getenv("APP_JWT_HASH", "HS256")
    APP_JWT_ALGORITHM = os.getenv("APP_JWT_ALGORITHM", "HS256")
    APP_JWT_EXPIRE = os.getenv("APP_JWT_EXPIRE", 3600)

    # EMAIL

    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_TLS = os.getenv("EMAIL_TLS", True)
    EMAIL_SSL = os.getenv("EMAIL_SSL", False)

    # REDIS

    REDIS_HOST = os.getenv("REDIS_HOST", "")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)
    REDIS_DB = os.getenv("REDIS_DB", 0)
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_MIN_SIZE = os.getenv("REDIS_MIN_SIZE", 10)
    REDIS_MAX_SIZE = os.getenv("REDIS_MAX_SIZE", 20)
    REDIS_TIMEOUT = os.getenv("REDIS_TIMEOUT", 30)
    REDIS_SSL = os.getenv("REDIS_SSL", False)
    REDIS_ENCODING = os.getenv("REDIS_ENCODING", "utf-8")
    REDIS_CONNECTION_TIMEOUT = os.getenv("REDIS_CONNECTION_TIMEOUT", 30)
    REDIS_RETRY_LIMIT = os.getenv("REDIS_RETRY_LIMIT", 3)
    REDIS_RETRY_INTERVAL = os.getenv("REDIS_RETRY_INTERVAL", 1)
    REDIS_RETRY_INTERVAL_UNIT = os.getenv("REDIS_RETRY_INTERVAL_UNIT", "seconds")

    # CELERY

    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    CELERY_TASK_SERIALIZER = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_RESULT_SERIALIZER = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT = os.getenv("CELERY_ACCEPT_CONTENT", ["json"])
    CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC = os.getenv("CELERY_ENABLE_UTC", True)
    CELERY_TASK_TRACK_STARTED = os.getenv("CELERY_TASK_TRACK_STARTED", True)
    CELERY_TASK_TIME_LIMIT = os.getenv("CELERY_TASK_TIME_LIMIT", 30 * 60)
    CELERY_TASK_SOFT_TIME_LIMIT = os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", 30 * 60)
    CELERY_TASK_TIME_LIMIT_WARN = os.getenv("CELERY_TASK_TIME_LIMIT_WARN", 30 * 60 - 10)
    CELERY_TASK_DEFAULT_QUEUE = os.getenv("CELERY_TASK_DEFAULT_QUEUE", "default")
    CELERY_TASK_DEFAULT_EXCHANGE = os.getenv("CELERY_TASK_DEFAULT_EXCHANGE", "default")
    CELERY_TASK_DEFAULT_EXCHANGE_TYPE = os.getenv(
        "CELERY_TASK_DEFAULT_EXCHANGE_TYPE", "direct"
    )
    CELERY_TASK_DEFAULT_ROUTING_KEY = os.getenv(
        "CELERY_TASK_DEFAULT_ROUTING_KEY", "default"
    )

    # RABBITMQ

    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)

    # SENTRY

    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_RELEASE = os.getenv("SENTRY_RELEASE", "0.0.1")
    SENTRY_TRACES_SAMPLE_RATE = os.getenv("SENTRY_TRACES_SAMPLE_RATE", 1.0)
    SENTRY_TRACES_SAMPLING = os.getenv("SENTRY_TRACES_SAMPLING", True)
    SENTRY_TRACES_INTEGRATIONS = os.getenv(
        "SENTRY_TRACES_INTEGRATIONS", ["celery", "sqlalchemy"]
    )
    SENTRY_TRACES_SQLALCHEMY_INTEGRATIONS = os.getenv(
        "SENTRY_TRACES_SQLALCHEMY_INTEGRATIONS", True
    )
    SENTRY_TRACES_CELERY_INTEGRATIONS = os.getenv(
        "SENTRY_TRACES_CELERY_INTEGRATIONS", True
    )
    SENTRY_TRACES_CELERY_INTEGRATIONS_EXCLUDE = os.getenv(
        "SENTRY_TRACES_CELERY_INTEGRATIONS_EXCLUDE", ["celery.app.trace"]
    )
    SENTRY_TRACES_CELERY_INTEGRATIONS_INCLUDE = os.getenv(
        "SENTRY_TRACES_CELERY_INTEGRATIONS_INCLUDE", []
    )

    # LOGGING

    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
    LOGGING_FORMAT = os.getenv(
        "LOGGING_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOGGING_DATE_FORMAT = os.getenv("LOGGING_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
    LOGGING_FILE = os.getenv("LOGGING_FILE", "logs/app.log")
    LOGGING_FILE_MAX_BYTES = os.getenv("LOGGING_FILE_MAX_BYTES", 1024 * 1024 * 10)
    LOGGING_FILE_BACKUP_COUNT = os.getenv("LOGGING_FILE_BACKUP_COUNT", 10)
    LOGGING_FILE_ENCODING = os.getenv("LOGGING_FILE_ENCODING", "utf-8")
    LOGGING_FILE_DELAY = os.getenv("LOGGING_FILE_DELAY", True)
    LOGGING_FILE_WHEN = os.getenv("LOGGING_FILE_WHEN", "D")
    LOGGING_FILE_INTERVAL = os.getenv("LOGGING_FILE_INTERVAL", 1)
    LOGGING_FILE_UTC = os.getenv("LOGGING_FILE_UTC", True)
    LOGGING_FILE_AT_TIME = os.getenv("LOGGING_FILE_AT_TIME", "")

    # Trading

    TRADING_EXCHANGE = os.getenv("TRADING_EXCHANGE", "binance")
    TRADING_SYMBOL = os.getenv("TRADING_SYMBOL", "BTCUSDT")
    TRADING_INTERVAL = os.getenv("TRADING_INTERVAL", "1m")
    TRADING_LIMIT = os.getenv("TRADING_LIMIT", 1000)
    TRADING_START_DATE = os.getenv("TRADING_START_DATE", "2020-01-01")
    TRADING_END_DATE = os.getenv("TRADING_END_DATE", "2020-01-02")
    TRADING_TIMEFRAME = os.getenv("TRADING_TIMEFRAME", "1m")
    TRADING_MAX_ORDERS = os.getenv("TRADING_MAX_ORDERS", 1)
    api_key = "f4c2130e7365dce72a71b11e543b5cfb-7764770b-41949093"
    alpha_api_key = 'ZXOV8SDY9BX8RF9N'