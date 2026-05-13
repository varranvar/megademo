from fastapi import APIRouter

from mdmo.api.packages import router as packages_router

router = APIRouter()
router.include_router(packages_router, tags=["dashboard"])
