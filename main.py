from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.conf.config import app_settings
from app.api.v1.contacts import router as contacts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

app = FastAPI(title=app_settings.APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Limit exceeded."},
    )