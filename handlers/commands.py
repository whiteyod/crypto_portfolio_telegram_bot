from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from assets.db import create_actions_table, \
    create_positions_table, create_transactions_table
from assets.texts import WELCOME_TEXT
from keyboards import main_kb


router = Router()


# Start command handler
@router.message(Command('start'))
async def cmd_start(message: Message):
    await create_actions_table()
    await create_transactions_table()
    await create_positions_table()
    await message.answer(WELCOME_TEXT, reply_markup=main_kb())
