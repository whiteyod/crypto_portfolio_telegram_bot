from aiogram import F, types, Router
from aiogram.filters.state import State, StatesGroup  
from assets.db import c, get_position, apply_sell
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import sys

from services.container import get_quotes
from keyboards import saving_kb, cancel_kb, cancel_kb_market


sys.path.append('/home/whiteyod/projects/inputToDFbot/')


router = Router()

# Define the states for the FSM
class States(StatesGroup):
    selling_amount_state = State() # State for getting selling amount
    market_price = State()


# Creating callbacks list
def create_callback_list():
    callbacks = []
    def add_callback(callback):
        callbacks.append(callback)
    def get_callbacks():
        return callbacks
    def clear_callback():
        callbacks.clear()
    return add_callback, get_callbacks, clear_callback

add_callback, get_callback, clear_callback = create_callback_list()


# Callback handler for the 'Sell' button
@router.callback_query(F.data == 'sell')
async def sell_button(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pairs = c.execute(
        '''
        SELECT symbol 
        FROM positions
        WHERE user_id = ?
        ''',
        (user_id,)
    )
    # Clear pairs data every time 'Sell' button is pressed
    clear_callback()
    # Populate pairs list with data
    for x in pairs:
        add_callback(x)

    # Check if there are pairs
    if pairs:
        # Iterate through pairs and create buttons
        kb = InlineKeyboardBuilder()
        for pair in get_callback():
            pairs_str = ''.join(pair).upper()
            callback_data = pairs_str
            kb.add(
                types.InlineKeyboardButton(text=pairs_str, callback_data=callback_data)
            )
            # Create a dynamic callback handler for each pair
            await create_sell_callback(router, callback_data, user_id)
        kb.add(
            types.InlineKeyboardButton(
                text='Cancel',
                callback_data='cancel')
        )
        kb.adjust(2)
        
        # Return pairs keyboard and message
        try:
            print(f'########## Selected callback data: {callback_data}')
            await callback.message.answer(
                'Select ticker to sell ... ',
                reply_markup=kb.as_markup()
            )
        except: 
            await callback.answer(
                text='Portfolio is empty ',
                show_alert=True
            )
    else: 
        await callback.answer(
            text='Portfolio is empty ',
            show_alert=True
            )


# Selling handler
async def create_sell_callback(router, symbol, user_id):
    @router.callback_query(F.data  == symbol)
    async def sell(callback: types.CallbackQuery, state: FSMContext):
        pos = await get_position(user_id=user_id, symbol=symbol)
        if pos is None:
            await callback.answer('Position not found', show_alert=True)
            return
        token_amount, avg_cost, realized_pnl = map(float, pos)
        # Get quotes from cache or CMC
        quotes = await get_quotes([symbol])
        market_price = quotes.get(symbol.upper())
        # Add market price to the state
        await state.update_data(market_price=market_price)
        if market_price is None:
            await callback.answer(f'{symbol} price not found', show_alert=True)
            return

        await state.set_state(States.selling_amount_state)
        await callback.message.edit_text(
            f'Selected ticker: <b>{symbol}</b>'
            f'\nAvailable balance: <b>{token_amount * market_price}$</b>'
            f'\nHow much to sell?',
            reply_markup=cancel_kb()
            )

        clear_callback()
        add_callback(symbol)

    return sell
        

# Waiting for user respond
@router.message(States.selling_amount_state)
async def sell_amount(message: Message, state=FSMContext):
    # Get ticker data
    symbol = get_callback()[0]
    symbol = ''.join(symbol).upper()
    print(f'pair {symbol}')
    user_id = message.from_user.id
    await state.update_data(sl_am=message.text)
    data = await state.get_data()
    # Get input from user
    try:
        selling_amount = float(data['sl_am'])
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

    market_price = float(data['market_price'])

    current_value = token_amount * market_price
    

    # Check if remaining amount is less or equal to selling amount
    if selling_amount > current_value:

        await message.answer(
            f'You try to sell <b>{selling_amount}$</b> but your balance is <b>{current_value:.2f}$</b>'
            f'\nEnter correct value: ',
            reply_markup=cancel_kb()
        )
        return

    sell_qty = selling_amount / market_price

    try: 
        await apply_sell(
            user_id=user_id, symbol=symbol, qty=sell_qty, price=market_price
        )
    except Exception as e:
        await message.answer(f'Sell failed: {e}', reply_markup=saving_kb())
        await state.clear()
        return

    await message.answer(
        f'<b>{symbol}</b> sold at <b>{selling_amount}$</b>',
        reply_markup=saving_kb()
    )

    # Reseting the FSM
    await state.clear()