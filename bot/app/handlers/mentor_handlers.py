from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from environs import Env
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from libs.api_tools import fetch_mentors, fetch_postcards

env = Env()
env.read_env()

API_URL = env.str('API_URL', 'http://localhost:8000')

mentor_router = Router()

bot = Bot(token=env.str('TELEGRAM_BOT_TOKEN'))


class SendPostcardStates(StatesGroup):
    waiting_for_mentor = State()
    waiting_for_postcard = State()


@mentor_router.callback_query(lambda c: c.data == "list_mentors")
async def list_mentors(callback: types.CallbackQuery, state: FSMContext):
    mentors = fetch_mentors(API_URL)

    if not mentors:
        await callback.message.answer("Список менторов пуст. Попробуйте позже.")
        return

    mentor_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{mentor['name']}",
                                  callback_data=f"select_mentor_{mentor['id']}")]
            for mentor in mentors
        ]
    )

    await callback.message.answer("Выберите ментора:", reply_markup=mentor_keyboard)
    await state.set_state(SendPostcardStates.waiting_for_mentor)


@mentor_router.callback_query(lambda c: c.data.startswith("select_mentor_"), SendPostcardStates.waiting_for_mentor)
async def select_mentor(callback: types.CallbackQuery, state: FSMContext):
    try:
        mentor_id = int(callback.data.split("_")[-1])
        await state.update_data(mentor_id=mentor_id)

        postcards = fetch_postcards(API_URL)

        if not postcards:
            await callback.message.answer("Список открыток пуст. Попробуйте "
                                          "позже.")
            return

        # Создаем клавиатуру с открытками
        postcard_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{postcard['name']}",
                                      callback_data=f"select_postcard_{postcard['id']}")]
                for postcard in postcards
            ]
        )

        await callback.message.answer("Выберите открытку для отправки:", reply_markup=postcard_keyboard)
        await state.set_state(SendPostcardStates.waiting_for_postcard)
    except ValueError:
        await callback.message.answer("Произошла ошибка при выборе ментора.")


@mentor_router.callback_query(lambda c: c.data.startswith("select_postcard_"), SendPostcardStates.waiting_for_postcard)
async def select_postcard(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    try:
        postcard_id = int(callback.data.split("_")[-1])
        user_data = await state.get_data()
        mentor_id = user_data.get("mentor_id")

        if not mentor_id:
            await callback.message.answer("Ментор не выбран. Начните сначала.")
            return

        # Ищем данные ментора по ID
        mentors = fetch_mentors(API_URL)
        mentor = next((m for m in mentors if m['id'] == mentor_id), None)

        if not mentor:
            await callback.message.answer("Ментор не найден. Попробуйте снова.")
            return

        # Ищем данные открытки по ID
        postcards = fetch_postcards(API_URL)
        postcard = next((postcard
                         for postcard in postcards
                         if postcard['id'] == postcard_id), None)

        if not postcard:
            await callback.message.answer("Открытка не найдена. Попробуйте "
                                          "снова.")
            return

        # Получаем chat_id ментора
        mentor_chat_id = mentor.get('chat_id')
        if not mentor_chat_id:
            await callback.message.answer(f"Не удалось найти chat_id для ментора {mentor['name']}.")
            return

        # Отправляем открытку ментору
        await bot.send_message(
            chat_id=mentor_chat_id,
            text=f"Тебе отправили открытку: \"{postcard['name']}\"\n\n{postcard['body']}"
        )

        # Уведомляем пользователя об успешной отправке
        await callback.message.answer(
            f"Открытка \"{postcard['name']}\" успешно отправлена ментору {mentor['name']}!"
        )
        await state.clear()
    except ValueError:
        await callback.message.answer("Произошла ошибка при выборе открытки.")