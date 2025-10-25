from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.admin.admin import admin_main_kb
from config import ADMIN_IDS

router = Router()

# Вход в админ-панель
@router.callback_query(F.data == 'admin_panel')
async def admin_panel_entry(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Доступ запрещён', show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer('⚙️ Админская панель', reply_markup=admin_main_kb)
    await callback.answer()
