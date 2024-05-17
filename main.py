import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage 

from config_reader import config
from handlers import commands, tests
from handlers.buttons import another_buttons, buy_buttons, sell_buttons, show_button



# Configure logging 
logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()


# Enable polling
async def main():
    bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')
    dp = Dispatcher(storage=storage)
    dp.include_routers(commands.router, another_buttons.router, sell_buttons.router, tests.router, buy_buttons.router, show_button.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())