import settings
from app.webhook.views import router as webhook_router
import uvicorn
from app import app


app.include_router(webhook_router)

uvicorn.run(
    "app:app",
    host=settings.Config.APP_HOST,
    port=settings.Config.APP_PORT,
    log_level=settings.Config.APP_LOG_LEVEL,
    reload=False,
    workers=1,
    ssl_keyfile="certs/local.key",
    ssl_certfile="certs/local.pem"

)
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()
