from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup

import asyncio

from assets.db import apply_buy
from keyboards import saving_kb, cancel_kb, cancel_kb_market
from handlers.commands import get_ticker_data_from_cmc
from services.container import get_quotes

import sys
sys.path.append('/home/whiteyod/projects/portfolio_bot/')


router = Router()


# Create class of states
class SaveHandler(StatesGroup):
    pair_state = State()
    price_state = State()
    amount_state = State()


# Save button handler
@router.callback_query(F.data == 'save')
async def saving(callback: types.CallbackQuery, state:FSMContext):
    # Clear state before start another
    await state.clear()
    # Set states to wait for user respond
    await state.set_state(SaveHandler.pair_state)
    await callback.message.answer(
        'Enter ticker name, use lowercase letters (example: btc, xrp, matic):',
        reply_markup=cancel_kb()
        )


# Pair state handling    
@router.message(SaveHandler.pair_state)
async def get_pair_state(message: Message, state=FSMContext):
    # Informing user that process is running
    msg = await message.answer('Processing ...')
    # Update states data 
    await state.update_data(pair=message.text)
    data = await state.get_data()
    symbol = data['pair'].upper()
    quotes = await get_quotes(symbol)
    result = quotes.get(symbol)

    # Check pair name correctness
    if result is None: # If no pairs with that name in CMC db ask to enter another name
        await state.update_data(pair=message.text)
        await asyncio.sleep(1)
        await msg.edit_text(
            f'No ticker with name <b>{symbol}</b> in <b>CoinMarketCap DB</b> '
            f'\nPlease enter correct ticker name: ',
            reply_markup=cancel_kb()
            )
    else: # Else set states to get buying price
        ticker_name, ticker_symbol = await get_ticker_data_from_cmc(symbol)
        result = f'{result:f}'
        await state.set_state(SaveHandler.price_state)
        await msg.edit_text(
            f'Ticker: <b>{ticker_name}</b>'
            f'\nSymbol: <b>{ticker_symbol}</b>'
            f'\nLast market price: <b>{result}$</b>'
            f'\nEnter buying price:',
            reply_markup=cancel_kb_market()
            )


# Price state handling
@router.message(SaveHandler.price_state)
async def get_price_state(message: Message, state=FSMContext):
    # Update price state and wait for respond
    await state.update_data(price=message.text)
    await state.set_state(SaveHandler.amount_state)
    await message.answer(
        'Enter amount in <b>USD$</b>:',
        reply_markup=cancel_kb_market())


# Amount state handling
@router.message(SaveHandler.amount_state)
async def get_amount_state(message: Message, state=FSMContext):
    await state.update_data(amount=message.text)
    # Get user id
    user_id = message.from_user.id

    # Get data from user through FSM and CMC API
    data = await state.get_data()
    symbol = data['pair'].upper()
    price = float(data['price'])
    try:
        amount_usd = float(data['amount'])
    except: 
        await message.answer(
            'Please send the number without any characters',
            reply_markup=cancel_kb()
            )
    qty = amount_usd / price
    await apply_buy(
        user_id=user_id, symbol=symbol, qty=qty, price=price
        )
    
    await state.clear()
    await message.answer(
        'Portfolio has been updated',
        reply_markup=saving_kb())