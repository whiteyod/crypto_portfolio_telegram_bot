from aiogram import F, types, Router
from aiogram.filters.state import State, StatesGroup  
from assets.db import c, get_ticker_data, conn
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
        SELECT pair 
        FROM messages
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
        price, token_amount = await get_ticker_data(pair, user_id)
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
        
        # Check data corectness
        print(
            f'########## Initial amount: {token_amount*market_price}, price: {price}, tokens: {token_amount}'
            f'\n########## Current market price: {market_price}'
            f'\n########## Last profit based on initial amount: {None}'
        )
        
        print(f' >>>>>>>>>>>>>>>>>> {get_callback()}')

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
        print(
            f'########## Selling amount from user input: {selling_amount}'
        )
    except:
        await message.answer(
            'Please send the number without any characters',
            reply_markup=cancel_kb()
            )
    # Get values from db
    price, token_amount = await get_ticker_data(pair, user_id)
    market_price = get_ticker_price(pair)
    current_token_amount_price = token_amount * market_price
    
    # Check data corectness
    print(
        f'########## Amount: {current_token_amount_price}, price: {price}'
        f'\n########## market_price: {market_price}, profit: {current_token_amount_price - (token_amount * price)}'
    )

    # Check if remaining amount is less or equal to selling amount
    if selling_amount > current_token_amount_price:
        if current_token_amount_price > 0.1: # If less ask to enter new value
            await state.update_data(sl_am=message.text)
            await message.answer(
                f'You trying to sell <b>{selling_amount}$</b> which is more than your balance of <b>{current_token_amount_price}$</b>'
                f'\nEnter correct value: ',
                reply_markup=cancel_kb()
                )
        else: 
            c.execute(
                '''
                DELETE FROM messages WHERE user_id = ? AND pair = ?
                ''',
                (user_id, pair)
            )
            await state.clear()
            conn.commit()
            await message.answer(
                f'{pair} sold at <b>{selling_amount + (current_token_amount_price - (token_amount * price))}$</b> with the total profit of <b>{current_token_amount_price - (token_amount * price)}$</b> and has been removed from the table',
                reply_markup=saving_kb()
            )
    elif (current_token_amount_price - selling_amount) < 0.1 : # If equal ask do user want to sell everything
        await state.update_data(sl_am=message.text)
        await state.set_state(States.yes_no_state)
        # Create inline keyboard to take answers from user
        kb = InlineKeyboardBuilder()
        kb.add(
            types.InlineKeyboardButton(
                text='Yes',
                callback_data='answer_yes'
            ),
            types.InlineKeyboardButton(
                text='No',
                callback_data='answer_no'
            )
        )
        await state.clear()
        await message.answer(
            f'Remaining amount of <b>{pair}</b> is equal to the selling amount, do you want to sell everything?'
            f'\nThe ticker will be deleted from the portfolio.',
            reply_markup=kb.as_markup()
        )
    else: ###################################################################################################
        # Calculating curent profit and amount adjusting
        
        token_selling_amount = selling_amount / market_price
        remaining_tokens = token_amount - token_selling_amount
        
        c.execute(
            '''
            UPDATE messages SET  token_amount = ?
            WHERE user_id = ? AND pair = ?
            ''',
            (remaining_tokens, user_id, pair)
        )
        conn.commit()
        await message.answer(
            f'<b>{pair}</b> sold at <b>{selling_amount}$</b>',
            reply_markup=saving_kb()
        )
        
        # Check data corectness
        print(
            f'########## New amount: {remaining_tokens * market_price}, profit: {(current_token_amount_price - (token_amount * price))}, tokens {remaining_tokens}'
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