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
            text='Show DF',
            callback_data='data_frame'
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
