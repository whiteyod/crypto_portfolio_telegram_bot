from email import message
from aiogram import F, types, Router
from aiogram.filters.state import State, StatesGroup  
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from assets.db import get_position, apply_sell, get_symbol_all
from keyboards import saving_kb, cancel_kb, sell_symbol_kb, sell_input_mode_kb
from services.container import get_quotes


router = Router()


# Define the states for the FSM
class States(StatesGroup):
    market_price = State()
    sell_mode = State()
    selling_amount = State() # State for getting selling amount


# Callback handler for the 'Sell' button
@router.callback_query(F.data == 'sell')
async def sell_button(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    # Fetch symbols from positions
    rows = await get_symbol_all(user_id)
    symbols = [r[0].upper() for r in rows]

    if not symbols:
        await callback.message.answer('Portfolio is empty', show_alert=True)
        return

    await state.clear()
    await callback.message.answer(
        'Select symbol to sell:',
        reply_markup=sell_symbol_kb(symbols)
    )


# Select sell symbol handler
@router.callback_query(F.data.startswith('sell_sym:'))
async def sell(callback: types.CallbackQuery, state: FSMContext):
    symbol = callback.data.split(':', 2)[1].upper()
    user_id = callback.from_user.id
    # Fetch position data
    pos = await get_position(user_id=user_id, symbol=symbol)
    if pos is None:
        await callback.answer('Position not found', show_alert=True)
        return
    token_amount, avg_cost, realized_pnl = map(float, pos)
    # Get quotes from cache or CMC
    quotes = await get_quotes([symbol])
    market_price = quotes.get(symbol.upper())
    if market_price is None:
        await callback.answer(f'{symbol} price not found', show_alert=True)
        return
    # Add market price to the state
    await state.update_data(market_price=market_price, symbol=symbol)
    await state.set_state(States.sell_mode)
    # Ask user to choose selling mode
    await callback.message.edit_text(
        f'Selected symbol: <b>{symbol}</b>'
        f'\nAvailable balance: <b>{token_amount}({token_amount * market_price}$)</b>'
        f'\n\nChoose how you want to enter the sell amount:',
        reply_markup=sell_input_mode_kb(symbol)
        )
        

# Sell mode handler by token/ by USD
@router.callback_query(F.data.startswith('sell_mode:'))
async def sell_mode_selected(callback: types.CallbackQuery, state: FSMContext):
    # Get sym and mode data from callback
    parts = callback.data.split(':', 2)
    mode = parts[1]
    symbol = parts[2] if len(parts) > 2 else None
    # Update mode state
    await state.update_data(sell_mode=mode)
    # Update symbol state if exists
    if symbol:
        await state.update_data(symbol=symbol)
    # Set state to catch selling amount
    await state.set_state(States.selling_amount)
    # Get symbol data from state
    data = await state.get_data()
    sym = data['symbol']
    # Send message based on sell mode
    if mode == 'qty':
        await callback.message.answer(
            f'Enter selling amount in <b>{sym}</b> (tokens):',
            reply_markup=cancel_kb()
        )
    else:
        await callback.message.answer(
            'Enter selling amount in <b>USD$</b>',
            reply_markup=cancel_kb()
        )


# Waiting for user respond
@router.message(States.selling_amount)
async def sell_amount(message: Message, state=FSMContext):
    user_id = message.from_user.id
    # Get symbol data
    data = await state.get_data()
    symbol = data['symbol']
    market_price = float(data['market_price'])
    mode = data['sell_mode']

    # Get input from user
    try:
        amount = float(message.text)
    except:
        await message.answer(
            'Please send the number without any characters',
            reply_markup=cancel_kb()
            )

    # Get values from db and map data
    pos = await get_position(user_id, symbol)
    if pos is None:
        await message.answer('Position not found', reply_markup=saving_kb())
        await state.clear()
        return

    token_amount, avg_cost, realized_pnl = map(float, pos)

    # Check remainig amount based on selling mode
    if mode == 'usd':
        selling_amount_usd = amount
        if selling_amount_usd > token_amount * market_price:
            await message.answer(
                f'You try to sell <b>{selling_amount_usd}$</b> but your balance is <b>{token_amount * market_price:.2f}$</b>'
                f'\nEnter correct value: ',
                reply_markup=cancel_kb()
            )
            return

        sell_qty = selling_amount_usd / market_price

    else:
        sell_qty = amount
        if sell_qty > token_amount:
            await message.answer(
                f'You try to sell <b>{sell_qty}</b> but your balance is <b>{token_amount:.6f}</b> {symbol}'
                f'\nEnter correct value:',
                reply_markup=cancel_kb()
            )
            return
        selling_amount_usd = sell_qty * market_price
    await apply_sell(
        user_id=user_id, symbol=symbol, qty=sell_qty, price=market_price
    )
    await message.answer(
        f'<b>{symbol}</b> sold at <b>{selling_amount_usd}$</b>',
        reply_markup=saving_kb()
    )

    # Reseting the FSM
    await state.clear()