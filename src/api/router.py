from fastapi import APIRouter
from src.api.gmail_routes import router as gmail_router
from src.api.slack_routes import router as slack_router
from src.api.health_routes import router as health_router

router = APIRouter()

router.include_router(gmail_router)
router.include_router(slack_router)
router.include_router(health_router)
