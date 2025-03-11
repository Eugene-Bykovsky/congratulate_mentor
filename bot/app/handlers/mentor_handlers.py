from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from environs import Env
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from libs.api_client import fetch_mentors, fetch_postcards

env = Env()
env.read_env()

API_URL = env.str('API_URL', 'http://localhost:8000')

mentor_router = Router()


class SendPostcardStates(StatesGroup):
    waiting_for_mentor = State()
    waiting_for_postcard = State()


MENTORS_PER_PAGE = 2


@mentor_router.callback_query(lambda c: c.data == "list_mentors")
async def list_mentors(callback: types.CallbackQuery, state: FSMContext):
    await show_mentor_list(callback, state, page=1)


@mentor_router.callback_query(lambda c: c.data.startswith("page_"))
async def navigate_pages(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    await show_mentor_list(callback, state, page=page)


async def show_mentor_list(context, state, page=1):
    mentors = fetch_mentors(API_URL)
    if mentors is None:
        await context.message.answer(
            "Не удалось подключиться к серверу. Попробуйте позже.")
        return

    total_mentors = len(mentors)
    total_pages = (total_mentors + MENTORS_PER_PAGE - 1) // MENTORS_PER_PAGE

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * MENTORS_PER_PAGE
    end = page * MENTORS_PER_PAGE
    current_mentors = mentors[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for mentor in current_mentors:
        full_name = f"{mentor['name']['first']} {mentor['name']['second']}"
        tg_username = mentor.get('tg_username', "")

        words = full_name.split()
        if len(words) > 2:
            displayed_name = f"{words[0]} {words[1]}..."
        else:
            displayed_name = full_name

        if tg_username:
            displayed_text = f"{displayed_name} ({tg_username})"
        else:
            displayed_text = displayed_name

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=displayed_text,
                callback_data=f"select_mentor_{mentor['id']}"
            )
        ])

    navigation_buttons = []
    if total_pages > 1:
        if page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text="← Предыдущая",
                                     callback_data=f"page_{page - 1}")
            )
        if page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text="Следующая →",
                                     callback_data=f"page_{page + 1}")
            )
        keyboard.inline_keyboard.append(navigation_buttons)

    await context.message.answer(
        f"Страница {page} из {total_pages}\n\n"
        "Выберите ментора:",
        reply_markup=keyboard
    )
    await state.set_state(SendPostcardStates.waiting_for_mentor)


@mentor_router.callback_query(
    lambda c: c.data.startswith("select_mentor_"),
    StateFilter(SendPostcardStates.waiting_for_mentor)
)
async def select_mentor(callback: types.CallbackQuery, state: FSMContext):
    try:
        mentor_id = int(callback.data.split("_")[-1])
        await state.update_data(mentor_id=mentor_id)

        postcards = fetch_postcards(API_URL)
        if postcards is None:
            await callback.message.answer(
                "Не удалось подключиться к серверу. Попробуйте позже.")
            return
        if not postcards:
            await callback.message.answer(
                "Список открыток пуст. Попробуйте позже.")
            return

        postcard_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=postcard['name_ru'],
                                      callback_data=f"select_postcard"
                                                    f"_{postcard['id']}")]
                for postcard in postcards
            ]
        )

        await callback.message.answer("Выберите открытку для отправки:",
                                      reply_markup=postcard_keyboard)
        await state.set_state(SendPostcardStates.waiting_for_postcard)
    except ValueError:
        await callback.message.answer("Произошла ошибка при выборе ментора.")


@mentor_router.callback_query(
    lambda c: c.data.startswith("select_postcard_"),
    StateFilter(SendPostcardStates.waiting_for_postcard)
)
async def select_postcard(callback: types.CallbackQuery, state: FSMContext,
                          bot: Bot):
    try:
        postcard_id = int(callback.data.split("_")[-1])
        user_data = await state.get_data()
        mentor_id = user_data.get("mentor_id")

        if not mentor_id:
            await callback.message.answer("Ментор не выбран. Начните сначала.")
            return

        mentors = fetch_mentors(API_URL)
        if mentors is None:
            await callback.message.answer(
                "Не удалось подключиться к серверу. Попробуйте позже.")
            return
        mentor = next((m for m in mentors if m['id'] == mentor_id), None)
        if not mentor:
            await callback.message.answer(
                "Ментор не найден. Попробуйте снова.")
            return

        postcards = fetch_postcards(API_URL)
        if postcards is None:
            await callback.message.answer(
                "Не удалось подключиться к серверу. Попробуйте позже.")
            return
        postcard = next((p for p in postcards if p['id'] == postcard_id), None)
        if not postcard:
            await callback.message.answer(
                "Открытка не найдена. Попробуйте снова.")
            return

        # Используем tg_chat_id вместо chat_id
        mentor_chat_id = mentor.get('tg_chat_id')
        if not mentor_chat_id:
            await callback.message.answer(
                f"Не удалось найти chat_id для ментора"
                f" {mentor['name']['first']} {mentor['name']['second']}.")
            return

        try:
            await bot.send_message(
                chat_id=mentor_chat_id,
                text=f"Тебе отправили открытку:"
                     f" \"{postcard['name_ru']}\"\n\n{postcard['body']}"
            )
        except Exception as e:
            await callback.message.answer(
                f"Произошла ошибка при отправке: {str(e)}. Попробуйте позже.")
            return

        await callback.message.answer(
            f"Открытка \"{postcard['name_ru']}\" успешно отправлена ментору"
            f" {mentor['name']['first']} {mentor['name']['second']}!"
        )
        await state.clear()
    except Exception as e:
        await callback.message.answer(
            f"Произошла ошибка: {str(e)}. Попробуйте позже.")
