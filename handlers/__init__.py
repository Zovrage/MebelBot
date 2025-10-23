from aiogram import Router

from .admin.admin import router as admin_router
from .admin.manage_product import router as manage_product_router
from .admin.add_product import router as add_product_router
from .admin.applications import router as applications_router
from .user import router as user_router


router = Router()

router.include_routers(
    admin_router,
    manage_product_router,
    add_product_router,
    applications_router,
    user_router
)