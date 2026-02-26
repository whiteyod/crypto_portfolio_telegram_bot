from aiogram import F, types, Router
from aiogram.filters.state import State, StatesGroup  
from assets.db import c, get_position, apply_sell
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from decimal import Decimal
import sys

from handlers.commands import get_ticker_price
from keyboards import saving_kb, cancel_kb, cancel_kb_market


sys.path.append('/home/whiteyod/projects/inputToDFbot/')


router = Router()

# Define the states for the FSM
class States(StatesGroup):
    selling_amount_state = State() # State for getting selling amount
    yes_no_state = State() # State for handling yes/no answers


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
async def create_sell_callback(router, pair, user_id):
    @router.callback_query(F.data  == pair)
    async def sell(callback: types.CallbackQuery, state: FSMContext):
        pos = await get_position(user_id=user_id, symbol=pair)
        if pos is None:
            await callback.answer('Position not found', show_alert=True)
            return
        token_amount, avg_cost, realized_pnl = map(float, pos)
        market_price = get_ticker_price(pair)

        await state.set_state(States.selling_amount_state)
        await callback.message.edit_text(
            f'Selected ticker: <b>{pair}</b>'
            f'\nAwailable balance: <b>{token_amount * market_price}$</b>'
            f'\nHow much to sell?',
            reply_markup=cancel_kb()
            )

        clear_callback()
        add_callback(pair)

    return sell
        

# Waiting for user respond
@router.message(States.selling_amount_state)
async def sell_amount(message: Message, state=FSMContext):
    # Get ticker data
    pair = get_callback()[0]
    pair = ''.join(pair).upper()
    print(f'pair {pair}')
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
    pos = await get_position(user_id, pair)
    if pos is None:
        await message.answer('Position not found', reply_markup=saving_kb())
        await state.clear()
        return

    token_amount, avg_cost, realized_pnl = map(float, pos)

    market_price = get_ticker_price(pair)
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
            user_id=user_id, symbol=pair, qty=sell_qty, price=market_price
        )
    except Exception as e:
        await message.answer(f'Sell failed: {e}', reply_markup=saving_kb())
        await state.clear()
        return

    await message.answer(
        f'<b>{pair}</b> sold at <b>{selling_amount}$</b>',
        reply_markup=saving_kb()
    )

    # Reseting the FSM
    await state.clear()


# Handling answer 'Yes'
@router.callback_query(F.data == 'answer_yes')
async def answer_yes(callback: types.CallbackQuery, state: FSMContext):
    # Select pair, price, amount values from DB
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    pair = get_callback()[0]
    pair = ''.join(pair).upper()
    user_id = callback.from_user.id
    price, amount = await get_ticker_data(pair, user_id)

    market_price = get_ticker_price(pair)
    # Calculating profit
    await state.update_data(ans=callback.message.text)
    # Removing pair from the DB
    c.execute(
        '''
        DELETE FROM messages WHERE user_id = ? AND pair = ?
        ''',
        (user_id, pair)
    )
    conn.commit()
    await callback.message.answer(
        f'{pair} sold at <b>{amount * market_price}$</b> and has been removed from the portfolio',
        reply_markup=saving_kb()
    )
    await callback.bot.delete_message(chat_id=chat_id, message_id=message_id)
    await state.clear()


# Handling answer 'No' 
@router.callback_query(F.data == 'answer_no')
async def answer_no(callback: types.CallbackQuery, state: FSMContext):
    # Ask user to enter new selling amount
    await state.update_data(sl_am=callback.message.text)
    await state.set_state(States.selling_amount_state)
    await callback.message.answer('Enter new amount: ')
    await state.clear()