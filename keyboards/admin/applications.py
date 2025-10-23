from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import LeadStatus

# Клавиатура статусов лида
lead_status_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=status.value, callback_data=f"lead_status_{status.name}")]
        for status in LeadStatus
    ]
)

# Клавиатура списка лидов
def get_leads_kb(leads):
    kb = InlineKeyboardMarkup()
    for lead in leads:
        kb.add(InlineKeyboardButton(text=f"{lead.name} ({lead.status.value})", callback_data=f"lead_{lead.id}"))
    return kb

# Клавиатура управления отдельным лидом
def get_lead_manage_kb(lead_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить статус", callback_data=f"change_status_{lead_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_lead_{lead_id}")]
        ]
    )

