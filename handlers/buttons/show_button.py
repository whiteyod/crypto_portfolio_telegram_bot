from aiogram import Router, F, types

from assets.db import get_position_all
from keyboards import back_kb
from services.container import get_quotes

import sys


router = Router()


# Show button handler 
@router.callback_query(F.data == 'show_table')
async def starting(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rows = await get_position_all(user_id)

    # Init portfolio message header
    portfolio_info = [f'Current portfolio: \n']


    # Normalize symbols from DB rows
    symbols = [r[0].upper() for r in rows]

    # Send alert if user has no pairs data saved
    if not symbols:
        await callback.answer(
                text='Portfolio is empty...',
                show_alert=True
            )
    else: 
        # Try get quotes
        quotes = await get_quotes(symbols)
        # Totals for the whole portfolio
        items = []
        total_current_value = 0.0
        total_cost_value = 0.0
        total_realized = 0.0

        # Duild per-asset info
        for symbol, qty, avg_cost, realized_pnl in rows:
            # Convert data values
            symbol = symbol.upper()
            qty = float(qty)
            avg_cost = float(avg_cost)
            realized_pnl = float(realized_pnl)

            # Get current market price, if none continue
            market_price = quotes.get(symbol)
            if market_price is None:
                continue

            current_value = qty * market_price
            cost_value = qty * avg_cost
            unrealized = current_value - cost_value
            total = unrealized + realized_pnl

            # Update totals
            total_current_value += current_value
            total_cost_value += cost_value
            total_realized +=realized_pnl


            items.append({
                'symbol': symbol,
                'qty': qty,
                'avg_cost': avg_cost,
                'market_price': market_price,
                'current_value': current_value,
                'unrealized': unrealized,
                'realized': realized_pnl,
                'total': total,
            })

        # Pass formatted data with allocation
        for it in items:
            # Calculate allocation for each symbol separately
            allocation = (it['current_value'] / total_current_value * 100.0) \
                if total_current_value else 0.0
            # Create message for each symbol
            portfolio_info.append(
                f'<b>{it["symbol"]} {it["qty"]:.3f} ({it["current_value"]:.2f}USD)</b>'
                f'\nAvg cost: <b>{it["avg_cost"]:.9f}$</b>'
                f'\nMarket: <b>{it["market_price"]:.9f}$</b>'
                f'\nUnrealized P/L: {it["unrealized"]:+.2f}$'
                f'\nRealized P/L: {it["realized"]:+.2f}$'
                f'\nTotal P/L: {it["total"]:+.2f}$'
                f'\nAllocation: <b>{allocation:.2f}%</b>'
                f'\n{chr(8212) * 13}'
            )

        # Add totals footer
        total_unrealized = (total_current_value - total_cost_value)
        total_pnl = total_unrealized + total_realized
        total_pnl_pct = (total_pnl / total_cost_value * 100.0)\
            if total_cost_value else 0.0

        portfolio_info.append(
            f'\n<b>Total value:</b> {total_current_value:.2f} USD'
            f'\n<b>Unrealized P/L:</b> {total_unrealized:+.2f} USD'
            f'\n<b>Realized P/L:</b> {total_realized:+.2f}'
            f'\n<b>Total P/L:</b> {total_pnl:+.2f} USD ({total_pnl_pct:+.2f}%)'
        )

    if rows:
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