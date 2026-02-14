from aiogram import Router, F, types

from assets.db import c, get_ticker_data
from handlers.commands import get_ticker_price
from keyboards import back_kb
from services.container import cmc, quotes_cache

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


    # Normalize symbols from DB rows
    symbols = [''.join(x).upper() for x in pair]

    # Send alert if user has no pairs data saved
    if not symbols:
        await callback.answer(
                text='Portfolio is empty...',
                show_alert=True
            )
    else: 
        # Cache sorted key for this set of symbols
        cache_key = 'quotes:' + ','.join(sorted(symbols))

        # Try cache first
        quotes = quotes_cache.get(cache_key)

        # If no catch -> fetch once from CMC and store in cache
        if quotes is None:
            quotes = cmc.get_quotes_usd(symbols)
            quotes_cache.set(cache_key, quotes)

        # Totals for the whole portfolio
        total_current_value = 0.0
        total_cost_value = 0.0

        # Duild per-asset info
        for symbol in symbols:
            # Get current market price
            market_price = quotes.get(symbol)
            # Send alert if symbol has no price on CMC
            if market_price is None:
                await callback.answer(
                    f'{symbol} price not found in CoinMarketCap',
                    show_alert=True
                )
                continue

            # Get amount and mean buy price from DB
            price, token_amount = await get_ticker_data(symbol, user_id)

            # Calculate values
            buying_value = token_amount * price
            current_value = token_amount * market_price
            current_pnl = current_value - buying_value

            # Update totals
            total_current_value += current_value
            total_cost_value += buying_value

            # Format values
            formatted_current_value = '{:.2f}'.format(current_value)
            formatted_buy_price = '{:.9f}'.format(price)
            formatted_pnl = float('{:.2f}'.format(current_pnl))

            portfolio_info.append(
                f'<b>{symbol} {round(token_amount, 2)} ({formatted_current_value} USD)</b>'
                f'\nMean buying price: <b>{formatted_buy_price}$</b>'
                f'\n P&L: {"+" if formatted_pnl > 0 else ""}{formatted_pnl}$'
                f'\n{chr(8212) * 13}'
            )

        # Add totals footer
        total_pnl = total_current_value - total_cost_value
        total_pnl_pct = (total_pnl / total_cost_value * 100.0)\
            if total_cost_value else 0.0

        portfolio_info.append(
            f'\n<b>Total value:</b> {total_cost_value:.2f} USD'
            f'\n<b>Total P/L:</b> {total_pnl:+.2f} USD ({total_pnl_pct:+.2f}%)'
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