from aiogram import Router, F, types
from aiogram.types import FSInputFile
import pandas as pd

from assets.db import c, conn
from keyboards import main_kb, back_df_kb, back_from_csv_kb
from handlers.commands import get_ticker_price

import os
import sys
sys.path.append('/home/whiteyod/projects/portfolio_bot/')


router = Router()


# Show table as DF button handler
@router.callback_query(F.data == 'data_frame')
async def show_data_frame(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    c.execute('''
              SELECT pair, price, token_amount
              FROM messages
              WHERE user_id = ?
              ''',
              (user_id,))
    results = c.fetchall()
    if results:
        # Create DF
        df = pd.DataFrame(results, columns=['ticker', 'buy_price', 'token_amount'])
        
        # Collect market price for all tickers
        market_price = []
        for i in df['ticker']:
            market_price.append(get_ticker_price(i))
        print(market_price)
        
        # Add new columns
        df['last_market_price'] = market_price
        df['usd_amount'] = df['token_amount'] * df['last_market_price']
        
        # Convert e-notation to real numbers if so
        pd.set_option('display.float_format', '{:.8f}'.format)
        await callback.message.edit_text(
            f'{df}',
            reply_markup=back_df_kb()
        )


# Sending data as CVS file
@router.callback_query(F.data == 'send_csv')
async def send_csv(callback: types.CallbackQuery): # Sending DF as CSV
    user_id = callback.from_user.id
    c.execute('''
              SELECT pair, price, token_amount
              FROM messages
              WHERE user_id = ?
              ''',
              (user_id,))
    results = c.fetchall()

    if results:
        # Create DF
        df = pd.DataFrame(results, columns=['ticker', 'buy_price', 'token_amount'])
        
        # Collect narket price for all tickers
        market_price = []
        for i in df['ticker']:
            market_price.append(get_ticker_price(i))
        print(market_price)
        
        # Add new columns
        df['last_market_price'] = market_price
        df['usd_amount'] = df['token_amount'] * df['last_market_price']
        
        # Convert e-notation to real numbers if so
        pd.set_option('display.float_format', '{:.8f}'.format)
        
        # Create csv file
        df.to_csv(f'csv/{user_id}.csv', float_format='%.8f')
        path = f'csv/{user_id}.csv'
    try:
        doc = FSInputFile(path)
        await callback.message.reply_document(
            doc,
            reply_markup=back_from_csv_kb()
            )
        os.remove(f'csv/{user_id}.csv')
    except: 
        await callback.answer(
            'No data to convert',
            show_alert=True)


# Back to main button handler
@router.callback_query(F.data == 'main')
async def menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f'<b>Bot is ready!</b>'
        f'\n<b>• Press "Show"</b> to view your current portfolio.'
        f'\n<b>• Press "Buy"</b> to add new assets to your portfolio.'
        f'\n<b>• Press "Sell"</b> to sell assets from portfolio.'
        f'\n<b>• Press "Drop"</b> to clear the entire portfolio.',
        reply_markup=main_kb()
        )
    await callback.answer()


# Cancel and delete message button handler
@router.callback_query(F.data == 'cancel')
async def cancel(callback: types.CallbackQuery):
    await callback.message.delete()
    
    
# Return to main from csv creating
@router.callback_query(F.data == 'main_csv')
async def from_csv_to_main(callback: types.CallbackQuery):
    await callback.message.answer(
        f'<b>Bot is ready!</b>'
        f'\n<b>• Press "Show"</b> to view your current portfolio.'
        f'\n<b>• Press "Buy"</b> to add new assets to your portfolio.'
        f'\n<b>• Press "Sell"</b> to sell assets from portfolio.'
        f'\n<b>• Press "Drop"</b> to clear the entire portfolio.',
        reply_markup=main_kb()
    )


# Drop button handler
@router.callback_query(F.data == 'delete_table')
async def deleting(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    c.execute('''
              DELETE FROM messages WHERE user_id = ?
              ''',
              (user_id,))
    conn.commit()
    await callback.answer(
        text='Portfolio was cleared!',
        show_alert=True
    )