from aiogram import Router, F, types

from assets.db import c, get_ticker_data
from keyboards import back_kb
from handlers.commands import get_ticker_price

import sys
sys.path.append('/home/whiteyod/projects/portfolio_bot/')


router = Router()
     

# Show button handler 
@router.callback_query(F.data == 'show_table')
async def starting(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    c.execute(
        '''
        SELECT pair FROM messages WHERE user_id = ?
        ''',
        (user_id,)
    )
    pair = c.fetchall()

    # 
    portfolio_info = [f'Current portfolio: \n']

    # Calculating and updating current profit/loss by pair
    for i in pair:
            i = ''.join(i) # Select pair name and convert it to str
            market_price = get_ticker_price(i)
            
            # Get amount and price values from db by pair name
            price, token_amount = await get_ticker_data(i, user_id)
            # Adding portfolio info
            price = '{:.9f}'.format(price)
            portfolio_info.append(
                f'<b>{i.upper()} {round(token_amount, 2)} ({token_amount*market_price} USD)</b>'
                f'\nMean buying price: <b>{price}$</b>'
                f'\n{chr(8212) * 3}'
            )
    c.execute(
        '''
        SELECT pair, price, token_amount
        FROM messages
        WHERE user_id = ?
        ''',
              (user_id,))
    results = c.fetchall()

    if results:
        # Sending portfolio as a message
        edited_portfolio = '\n'.join(portfolio_info)
        await callback.message.edit_text(
            f'{edited_portfolio}',
            reply_markup=back_kb()
            )
        await callback.answer()
    else:
        await callback.answer(
            text='Portfolio is empty...',
            show_alert=True
        )