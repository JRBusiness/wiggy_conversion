import uvicorn
from app import app
from app.webhook.views import router as webhook_router


app.include_router(webhook_router)
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8005,
    reload=False,
    workers=1,

)
