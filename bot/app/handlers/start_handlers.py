from environs import Env
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from libs.api_tools import fetch_mentors
from libs.db_tools import save_user
import app.keyboards as kb

start_router = Router()

env = Env()
env.read_env()

API_URL = env.str('API_URL', 'http://localhost:8000')


@start_router.message(CommandStart())
async def send_welcome(message: types.Message):
    telegram_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    full_name = message.from_user.full_name
    tg_username = message.from_user.username

    save_user(telegram_id, chat_id, full_name, tg_username)

    mentors = fetch_mentors(API_URL)

    is_mentor = any(str(telegram_id) == str(mentor.get('telegram_id'))
                    for mentor in mentors)

    welcome_message = f"Привет, {user_name}!\n"
    if is_mentor:
        welcome_message += "Я вижу, что ты ментор! 😊\n"
    else:
        welcome_message += ("Добро пожаловать в наш бот для поздравлений "
                            "менторов!\n ")

    await message.reply(welcome_message, reply_markup=kb.main_menu_keyboard)
