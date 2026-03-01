from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from assets.db import c


# Main keyboard
def main_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Show',
            callback_data='show_table'
        ),
        types.InlineKeyboardButton(
            text='Buy',
            callback_data='save'
        ),
        types.InlineKeyboardButton(
            text='Sell',
            callback_data='sell'
        ),
        types.InlineKeyboardButton(
            text='Drop',
            callback_data='delete_table'
        )
    )
    return kb.as_markup()


# Back from showing
def back_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Main',
            callback_data='main'
        ),
        types.InlineKeyboardButton(
            text='Buy',
            callback_data='save'
        ),
        types.InlineKeyboardButton(
            text='Sell',
            callback_data='sell'
        ),
        types.InlineKeyboardButton(
            text='Send CSV',
            callback_data='send_csv'
        )
    )
    kb.adjust(3)
    return kb.as_markup()


def back_df_kb():
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(
            text='Main',
            callback_data='main'
        ),
        types.InlineKeyboardButton(
            text='Show',
            callback_data='show_table'
        ),
        types.InlineKeyboardButton(
            text='Buy',
            callback_data='save'
        ),
        types.InlineKeyboardButton(
            text='Sell',
            callback_data='sell'
        ),
        types.InlineKeyboardButton(
            text='Send CSV',
            callback_data='send_csv'
        )
    )
    kb.adjust(3)
    return kb.as_markup()


# Back from saving
def saving_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Main',
            callback_data='main'
        ),
        types.InlineKeyboardButton(
            text='Show',
            callback_data='show_table'
        ),
    )
    return kb.as_markup()


# Back from saving
def back_from_csv_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Main',
            callback_data='main_csv'
        )
    )
    return kb.as_markup()


# Saving keyboard
def save_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Buy',
            callback_data='save'
        )
    )
    return kb.as_markup()


# Cancel keyboard and delete message
def cancel_kb():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Cancel',
            callback_data='cancel'
        )
    )
    return kb.as_markup()
    

# Back to main menu keyboard
def main_menu_kb():
    ''' Cancel current state and return to the main menu '''
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Main',
            callback_data='main'
        )
    )
    return kb.as_markup()


# Cancel and return to main
def cancel_kb_market():
    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Cancel',
            callback_data='main'
        )
    )
    return kb.as_markup()


# Select Sell mode by token/by USD
def sell_input_mode_kb(symbol: str):
    symbol = symbol.upper().strip()

    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Sell in USD',
            callback_data=f'sell_mode:usd:{symbol}',
        ),
        types.InlineKeyboardButton(
            text=f'Sell in {symbol}',
            callback_data=f'sell_mode:qty:{symbol}'
        )
    )
    kb.add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
    kb.adjust(2, 1)
    return kb.as_markup()


# Select buy mode by token/by USD
def buy_input_mode_kb(symbol: str):
    symbol = symbol.upper().strip()

    kb = InlineKeyboardBuilder()
    kb.add(
        types.InlineKeyboardButton(
            text='Buy in USD',
            callback_data=f'buy_mode:usd:{symbol}'
        ),
        types.InlineKeyboardButton(
            text=f'Buy in {symbol}',
            callback_data=f'buy_mode:qty:{symbol}'
        )
    )
    kb.add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
    kb.adjust(2, 1)
    return kb.as_markup()


# Select symbol to sell
def sell_symbol_kb(symbols: list[str]):
    kb = InlineKeyboardBuilder()
    for s in symbols:
        s = s.upper().strip()
        kb.add(
            types.InlineKeyboardButton(text=s, callback_data=f'sell_sym:{s}')
        )
    kb.add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
    kb.adjust(2)
    return kb.as_markup()