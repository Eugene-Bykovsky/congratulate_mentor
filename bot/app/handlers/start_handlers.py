from environs import Env
from aiogram import Router, types
from aiogram.filters import CommandStart

from libs.api_client import fetch_mentors
import app.keyboards as kb

start_router = Router()

env = Env()
env.read_env()

API_URL = env.str('API_URL', 'http://localhost:8000')


@start_router.message(CommandStart())
async def send_welcome(message: types.Message):
    mentors = fetch_mentors(API_URL)
    if mentors is None:
        await message.reply("Не удалось подключиться к серверу. Попробуйте "
                            "позже.")
        return

    telegram_id = message.from_user.id
    user_name = message.from_user.first_name
    is_mentor = any(str(telegram_id) == str(mentor.get('tg_chat_id'))
                    for mentor in mentors)

    welcome_message = f"Привет, {user_name}!\n"
    if is_mentor:
        welcome_message += "Я вижу, что ты ментор! 😊\n"
    else:
        welcome_message += ("Добро пожаловать в наш бот для поздравлений "
                            "менторов, ученик!\n")

    await message.reply(welcome_message, reply_markup=kb.main_menu_keyboard)
