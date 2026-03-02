from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup

import asyncio

from assets.db import apply_buy
from keyboards import saving_kb, cancel_kb, cancel_kb_market, \
    buy_input_mode_kb
from services.container import get_quotes, cmc

import sys
sys.path.append('/home/whiteyod/projects/portfolio_bot/')


router = Router()


# Create class of states
class SaveHandler(StatesGroup):
    amount_state = State()
    mode_state = State()
    pair_state = State()
    price_state = State()


# Save button handler
@router.callback_query(F.data == 'save')
async def saving(callback: types.CallbackQuery, state:FSMContext):
    # Clear state before start another
    await state.clear()
    # Set states to wait for user respond
    await state.set_state(SaveHandler.pair_state)
    await callback.message.answer(
        'Enter token symbol (example: BTC, Xrp, skr):',
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
    quotes = await get_quotes([symbol])
    result = quotes.get(symbol.upper())

    # Check pair name correctness
    if result is None: # If no pairs with that name in CMC db ask to enter another name
        await state.update_data(pair=message.text)
        await asyncio.sleep(1)
        await msg.edit_text(
            f'No symbol with name <b>{symbol}</b> in <b>CoinMarketCap DB</b> '
            f'\nPlease enter correct symbol name: ',
            reply_markup=cancel_kb()
            )
    else: # Else set states to get buying price
        asset_info = cmc.get_assets_info([symbol], fields={'name', 'symbol'})
        # Get asset infom from cache
        coin_name = asset_info.get(symbol, {}).get('name')
        coin_symbol = asset_info.get(symbol, {}).get('symbol')
        print(asset_info, coin_name, coin_symbol)
        result = f'{result:f}'
        await state.set_state(SaveHandler.mode_state)
        await msg.edit_text(
            f'Coin: <b>{coin_name}</b>'
            f'\nSymbol: <b>{coin_symbol}</b>'
            f'\nLast market price: <b>{result}$</b>'
            f'\n\nChoose how you want to enter the buy amount:',
            reply_markup=buy_input_mode_kb(symbol)
            )


# Buying amount handler
@router.callback_query(F.data.startswith('buy_mode:'))
async def buy_mode_selected(callback: types.CallbackQuery, state: FSMContext):
    # Get buying mode state(by token/by USD)
    mode = callback.data.split(':', 2)[1]
    await state.update_data(buy_mode=mode)
    # Set state to catch buying price
    await state.set_state(SaveHandler.price_state)
    await callback.message.edit_text(
        'Enter buying price:',
        reply_markup=cancel_kb_market()
    )


# Price state handling
@router.message(SaveHandler.price_state)
async def get_price_state(message: Message, state=FSMContext):
    # Get mode state data 
    data = await state.get_data()
    symbol = data['pair'].upper()
    mode = data.get('buy_mode')
    # Update price state and wait for respond
    await state.update_data(price=message.text)
    await state.set_state(SaveHandler.amount_state)
    # Edit message based on buy mode
    if mode == 'qty':
        msg = symbol.upper().strip()
    else:
        msg = 'USD$'
    await message.answer(
        f'Enter buying amount in <b>{msg}</b>:',
        reply_markup=cancel_kb_market())


# Amount state handling
@router.message(SaveHandler.amount_state)
async def get_amount_state(message: Message, state=FSMContext):
    await state.update_data(amount=message.text)
    # Get user id
    user_id = message.from_user.id

    # Get data from user through FSM
    data = await state.get_data()
    mode = data.get('buy_mode')
    symbol = data['pair'].upper()
    price = float(data['price'])
    # Convert input data based on buying mode
    if mode == 'usd':
        usd_amount = float(data['amount'])
        qty = usd_amount / price
    elif mode == 'qty':
        qty = float(data['amount'])
    else:
        await message.answer('Please choose buy mode again.')
        return
    await apply_buy(
        user_id=user_id, symbol=symbol, qty=qty, price=price
        )
    
    await state.clear()
    await message.answer(
        'Portfolio has been updated',
        reply_markup=saving_kb())