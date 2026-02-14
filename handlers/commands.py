from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from requests import Session

import json
import sys

from assets.db import create_tickers_table
from config_reader import config
from keyboards import main_kb

sys.path.append('/home/whiteyod/projects/portfolio_bot/')


router = Router()


# Set up API key
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': config.api_key.get_secret_value(),
}

parameters = {
  'convert':'USD'
}

session = Session()
session.headers.update(headers)


# Get current market price
def get_ticker_price(ticker: str):
    ''' Get current market price for pair from CMC'''
    try:
        # Send request to API
        url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={ticker.upper()}'
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        result = data['data'][ticker.upper()]['quote']['USD']['price']
    except:
        return '0564'
    return result


# Get ticker data
async def get_ticker_data_from_cmc(ticker: str):
    ''' Returns ticker name, symbol name '''
    
    try:
        # Send request
        url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={ticker.upper()}'
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        ticker_name = data['data'][ticker.upper()]['name']
        ticker_symbol = data['data'][ticker.upper()]['symbol']
    except: 
        print('no data')
    return ticker_name, ticker_symbol

# Start command handler
@router.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await create_tickers_table(user_id)
    await message.answer(
        f'<b>Bot is ready!</b>'
        f'\n<b>• Press "Show"</b> to view your current portfolio.'
        f'\n<b>• Press "Buy"</b> to add new assets to your portfolio.'
        f'\n<b>• Press "Sell"</b> to sell assets from portfolio.'
        f'\n<b>• Press "Drop"</b> to clear the entire portfolio.',
        reply_markup=main_kb()
        )
