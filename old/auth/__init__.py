from fastapi import FastAPI
from .auth.views import router as auth_router

app = FastAPI()

# Include the auth router
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
