from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Список менторов",
                                 callback_data="list_mentors")
        ],
        [
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot")
        ],
        [
            InlineKeyboardButton(text="📞 Связь с администратором",
                                 callback_data="contact_admin")
        ],
    ]
)
