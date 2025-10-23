from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import async_session
from database.crud import get_leads, update_lead_status, delete_lead
from database.models import LeadStatus

router = Router()



# Просмотр всех заявок/лидов
@router.callback_query(F.data == "show_applications")
async def show_applications(callback: CallbackQuery):
    async with async_session() as session:
        leads = await get_leads(session)
    if not leads:
        await callback.message.answer("Нет заявок.")
        await callback.answer()
        return
    for lead in leads:
        text = f"Заявка #{lead.id}\nСтатус: {lead.status}\nИмя: {lead.name}\nТелефон: {lead.phone}"
        await callback.message.answer(text)
    await callback.answer()

# Изменение статуса заявки
@router.callback_query(F.data.startswith("set_lead_status_"))
async def set_lead_status(callback: CallbackQuery):
    parts = callback.data.split("_")
    lead_id = int(parts[-2])
    status = LeadStatus[parts[-1]]
    async with async_session() as session:
        await update_lead_status(session, lead_id, status)
    await callback.message.answer(f"Статус заявки #{lead_id} изменён на {status.value}.")
    await callback.answer()

# Удаление заявки
@router.callback_query(F.data.startswith("delete_lead_"))
async def delete_lead_handler(callback: CallbackQuery):
    lead_id = int(callback.data.split("_", 2)[2])
    async with async_session() as session:
        await delete_lead(session, lead_id)
    await callback.message.answer(f"Заявка #{lead_id} удалена.")
    await callback.answer()
