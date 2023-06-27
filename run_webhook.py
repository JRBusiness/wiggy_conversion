import uvicorn
from app import app
from app.webhook.views import router as webhook_router
from settings import Config

app.include_router(webhook_router)
uvicorn.run(
    app,
    host=Config.APP_HOST,
    port=8005,
    reload=False,
    workers=1
)
