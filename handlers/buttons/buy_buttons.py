from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup

import asyncio

from assets.db import c, get_ticker_data, conn, create_symbols_table
from keyboards import saving_kb, cancel_kb, cancel_kb_market
from handlers.commands import get_ticker_price, get_ticker_data_from_cmc

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
    user_id = callback.message.from_user.id
    # Create table if not exists
    await create_symbols_table(user_id)
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
    pair = data['pair'].upper()
    result = get_ticker_price(pair)

    # Check pair name correctness
    if result == '0564': # If no pairs with that name in CMC db ask to enter another name
        await state.update_data(pair=message.text)
        await asyncio.sleep(1)
        await msg.edit_text(
            f'No ticker with name <b>{pair}</b> in <b>CoinMarketCap DB</b> '
            f'\nPlease enter correct ticker name: ',
            reply_markup=cancel_kb()
            )
    else: # Else set states to get buying price
        ticker_name, ticker_symbol = await get_ticker_data_from_cmc(pair)
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
    pair = data['pair'].upper()
    price = float(data['price'])
    try:
        amount_usd = float(data['amount'])
    except: 
        await message.answer(
            'Please send the number without any characters',
            reply_markup=cancel_kb()
            )
    token_amount = amount_usd / price

    # Cheking if row already exists
    c.execute(
        '''
        SELECT count(*) FROM messages
        WHERE pair = ? AND user_id = ?
        ''',
        (pair, user_id)
        )
    result = c.fetchone()

    # Saving if there is no data before
    if result[0] == 0:
        c.execute(
            '''
            INSERT INTO messages (user_id, pair, price, token_amount)
            VALUES (?, ?, ?, ?)
            ''',
            (user_id, pair, price, token_amount)
        )  
        conn.commit()
        # Clear state and inform user about saving
        await state.clear()
        await message.answer(
            f'Saved <b>{pair}</b>',
            reply_markup=saving_kb())
    else: # Changing values if there are data
        # Calculating mean price and amount adjusting
        previous_price, token_amount = await get_ticker_data(pair, user_id)
        total_quantity = token_amount + (amount_usd / price)
        total_amount_usd = (token_amount * previous_price) + amount_usd
        mean_price = total_amount_usd / total_quantity
        new_token_amount = total_amount_usd / mean_price

        # Updating data in the db
        c.execute(
            '''
            UPDATE messages SET price = ?, token_amount = ?
            WHERE pair = ? AND user_id = ?
            ''',
            (mean_price, new_token_amount, pair, user_id)
        )
        conn.commit()
        await state.clear()
        await message.answer(
            'Portfolio has been updated',
            reply_markup=saving_kb())