import logging
from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from environs import Env
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from libs.api_client import (fetch_mentors, fetch_postcards,
                             extract_holidays_from_postcards)
from libs.utils import get_shortened_body, replace_placeholder

env = Env()
env.read_env()

API_URL = env.str('API_URL', 'http://localhost:8000')

mentor_router = Router()


class SendPostcardStates(StatesGroup):
    waiting_for_mentor = State()
    waiting_for_holiday = State()  # Новое состояние для выбора праздника
    waiting_for_postcard = State()


MENTORS_PER_PAGE = 2


# Обработчик списка менторов
@mentor_router.callback_query(lambda c: c.data == "list_mentors")
async def list_mentors(callback: types.CallbackQuery, state: FSMContext):
    await show_mentor_list(callback, state, page=1)


# Функция показа списка менторов
async def show_mentor_list(callback: types.CallbackQuery, state, page=1):
    mentors = fetch_mentors(API_URL)
    if mentors is None:
        await callback.answer(
            "Не удалось подключиться к серверу. Попробуйте позже.",
            show_alert=True)
        return

    total_mentors = len(mentors)
    if total_mentors == 0:
        await callback.answer("Список менторов пуст. Попробуйте позже.",
                              show_alert=True)
        return

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
        logging.info(
            f"Creating button for mentor: {mentor}")  # Логируем данные ментора
        if not isinstance(mentor.get('id'), int):  # Защита от некорректного id
            logging.error(f"Incorrect mentor ID: {mentor.get('id')}")
            continue

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

    # Добавляем кнопки навигации
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
        if navigation_buttons:
            keyboard.inline_keyboard.append(navigation_buttons)

    try:
        # Редактируем текущее сообщение
        await callback.message.edit_text(
            f"Страница {page} из {total_pages}\n\n"
            "Выберите ментора:",
            reply_markup=keyboard
        )
    except Exception as e:
        # Если редактирование невозможно, отправляем новое сообщение
        await callback.message.answer(
            f"Страница {page} из {total_pages}\n\n"
            "Выберите ментора:",
            reply_markup=keyboard
        )

    # Устанавливаем состояние ожидания выбора ментора
    await state.set_state(SendPostcardStates.waiting_for_mentor)


# Обработчик навигации между страницами
@mentor_router.callback_query(lambda c: c.data.startswith("page_"))
async def navigate_pages(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    await show_mentor_list(callback, state, page=page)


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
                "Не удалось загрузить открытки. Попробуйте позже.")
            return

        holidays = extract_holidays_from_postcards(postcards)
        if not holidays:
            await callback.message.answer(
                "Не найдено ни одного праздника. Попробуйте позже.")
            return

        holiday_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=holiday['name_ru'],
                                      callback_data=f"select_holiday_{holiday['id']}")]
                for holiday in holidays
            ]
        )

        # Подтверждаем выбор ментора и предлагаем выбрать праздник
        mentors = fetch_mentors(API_URL)
        if not mentors:
            await callback.message.answer(
                "Список менторов недоступен. Попробуйте позже.")
            return

        mentor = next((m for m in mentors if m['id'] == mentor_id), None)
        if not mentor:
            await callback.message.answer(
                "Ментор не найден. Попробуйте снова.")
            return

        full_name = f"{mentor['name']['first']} {mentor['name']['second']}"
        await callback.message.answer(
            f"Вы выбрали ментора: {full_name}.\n\n"
            "Теперь выберите праздник для открытки:",
            reply_markup=holiday_keyboard
        )
        await state.set_state(SendPostcardStates.waiting_for_holiday)
    except Exception as e:
        await callback.message.answer(
            f"Произошла ошибка: {str(e)}. Попробуйте позже.")


@mentor_router.callback_query(
    lambda c: c.data.startswith("select_holiday_"),
    StateFilter(SendPostcardStates.waiting_for_holiday)
)
async def select_holiday(callback: types.CallbackQuery, state: FSMContext):
    try:
        holiday_id = callback.data.split("_")[2]
        await state.update_data(holiday_id=holiday_id)

        postcards = fetch_postcards(API_URL)
        if postcards is None:
            await callback.message.answer(
                "Не удалось загрузить открытки. Попробуйте позже.")
            return

        filtered_postcards = [p for p in postcards if
                              p['holidayId'] == holiday_id]
        if not filtered_postcards:
            await callback.message.answer(
                "Для этого праздника нет открыток. Попробуйте другой праздник.")
            return

        user_data = await state.get_data()
        mentor_id = user_data.get("mentor_id")
        mentors = fetch_mentors(API_URL)

        if not mentors or not mentor_id:
            await callback.message.answer(
                "Ментор не выбран или данные недоступны. Начните сначала.")
            return

        mentor = next((m for m in mentors if m['id'] == mentor_id), None)
        if not mentor:
            await callback.message.answer(
                "Ментор не найден. Попробуйте снова.")
            return

        postcard_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{get_shortened_body(replace_placeholder(postcard['body'], mentor['name']['first']))}",
                        callback_data=f"select_postcard_{postcard['id']}"
                    )
                ]
                for postcard in filtered_postcards
            ]
        )

        await callback.message.answer(
            "Выберите открытку для отправки:",
            reply_markup=postcard_keyboard
        )
        await state.set_state(SendPostcardStates.waiting_for_postcard)
    except Exception as e:
        await callback.message.answer(
            f"Произошла ошибка: {str(e)}. Попробуйте позже.")


# Обработчик выбора открытки
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
                "Сервер временно недоступен. Список менторов не загружен. "
                "Попробуйте позже."
            )
            return

        mentor = next((m for m in mentors if m['id'] == mentor_id), None)
        if not mentor:
            await callback.message.answer(
                "Ментор не найден. Попробуйте снова.")
            return

        postcards = fetch_postcards(API_URL)
        if postcards is None:
            await callback.message.answer(
                "Сервер временно недоступен. Список открыток не загружен. "
                "Попробуйте позже."
            )
            return

        postcard = next((p for p in postcards if p['id'] == postcard_id), None)
        if not postcard:
            await callback.message.answer(
                "Открытка не найдена. Попробуйте снова.")
            return

        # Получаем chat_id ментора
        mentor_chat_id = mentor.get('tg_chat_id')
        if not mentor_chat_id:
            await callback.message.answer(
                f"Не удалось найти chat_id для ментора {mentor['name']['first']} {mentor['name']['second']}."
            )
            return

        # Формируем полное имя ментора
        full_name = f"{mentor['name']['first']} {mentor['name']['second']}"

        # Заменяем #name на имя ментора
        personalized_body = replace_placeholder(postcard['body'], full_name)

        try:
            # Отправляем открытку ментору с замененным текстом
            await bot.send_message(
                chat_id=mentor_chat_id,
                text=f"Тебе отправили открытку: \"{postcard['name_ru']}\"\n\n{personalized_body}"
            )
        except Exception as e:
            await callback.message.answer(
                f"Произошла ошибка при отправке: {str(e)}. Попробуйте позже."
            )
            return

        # Подтверждаем отправку пользователю
        await callback.message.answer(
            f"Открытка \"{postcard['name_ru']}\" успешно отправлена ментору "
            f"{mentor['name']['first']} {mentor['name']['second']}!\n\n"
            f"Текст открытки:\n{personalized_body}"
        )
        await state.clear()
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {str(e)}. "
                                      f"Попробуйте позже.")
