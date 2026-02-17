from keyword import iskeyword
from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup

import json
import requests
from requests import Session

from handlers.commands import get_ticker_data_from_cmc
router = Router()


api_key = '5e856765-b752-4650-bb68-2b20240b477f'

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key,
}

parameters = {
  'convert':'USD'
}

session = Session()
session.headers.update(headers)


def get_all_tickers(ticker: str):
    ''' Gets list of all available tickers from CMC API'''
    # Send request to API
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={ticker.upper()}'
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    # return data['data'][ticker.upper()]['quote']['USD']['price']
    return print(data)


# Tests
@router.message(Command('test'))
async def test(message: Message): 
    user_id = message.from_user.id
    msg_text = message.text.replace('/test', '').strip().upper()
    ticker_name, ticker_symbol = await get_ticker_data_from_cmc(msg_text)
    await message.answer(
        f'Ticker name: {ticker_name}, ticker symbol: {ticker_symbol}'
    )

