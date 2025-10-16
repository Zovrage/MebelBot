from aiogram import Router

from handlers.admin import router as admin_router
from handlers.user import router as user_router


router = Router()

router.include_routers(
    admin_router,
    user_router
)

