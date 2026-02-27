from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from assets.db import create_actions_table, \
    create_positions_table, create_transactions_table
from keyboards import main_kb


router = Router()


# Start command handler
@router.message(Command('start'))
async def cmd_start(message: Message):
    await create_actions_table()
    await create_transactions_table()
    await create_positions_table()
    await message.answer(
        f'<b>Bot is ready!</b>'
        f'\n<b>• Press "Show"</b> to view your current portfolio.'
        f'\n<b>• Press "Buy"</b> to add new assets to your portfolio.'
        f'\n<b>• Press "Sell"</b> to sell assets from portfolio.'
        f'\n<b>• Press "Drop"</b> to clear the entire portfolio.',
        reply_markup=main_kb()
        )
