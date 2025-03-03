from environs import Env
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from asyncio import run

from app.handlers.start_handlers import start_router
from app.handlers.mentor_handlers import mentor_router


async def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    env = Env()
    env.read_env()
    TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_BOT_TOKEN:
        logging.error("Токен Telegram-бота не указан! Укажите переменную "
                      "окружения TELEGRAM_BOT_TOKEN.")
        return
    logging.info("Бот запущен!")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(start_router, mentor_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    run(main())
