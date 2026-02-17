from math import e
import sqlite3
from loguru import logger as log


# Connecting  to database
conn = sqlite3.connect('messages.db')
c = conn.cursor()


# Create the table for symbols list
async def create_symbols_table(user_id):
    c.execute('''
              CREATE TABLE IF NOT EXISTS messages
              ([id] INTEGER PRIMARY KEY AUTOINCREMENT,
              [user_id] INTEGER,
              [pair] TEXT,
              [price] FLOAT,
              [token_amount] FLOAT
              )
              ''')
    result = conn.commit()
    if result:
        print(f'Table was created for user {user_id}')
        

# Selecting values from the table
async def get_ticker_data(pair: str, user_id: int):
    ''' Returns a price and token amount values for specific pair and user'''
    
    # Get values
    c.execute(
        '''
        SELECT price, token_amount
        FROM messages
        WHERE user_id = ? AND pair = ?
        ''',
        (user_id, pair,)
    )
    result = c.fetchone()
    return result


# Create table for perfoming actions with the symbol values
async def create_actions_table():
    try:
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL, -- BUY, SELL, DROP, UPDATE
            pair TEXT,
            payload_json TEXT NOT NULL,
            created_at TTEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        log.info('Table "Actions" has been created')
    except Exception as e:
        log.exception(f'Can\'t create "Actions" table! And here is why: {e}')


# Create table to store full transaction data
async def create_transactions_table():
    try:
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL, -- "BUY" or "SELL"
            quantity REAL NOT NULL, -- token quantity
            price REAL NOT NULL, -- price per token (USD)
            fee_usd REAL NOT NULL DEFAULT 0,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            note TEXT
            )
        ''')
        conn.commit()
        log.info('Table "Transactions" has been created')
    except Exception as e:
        log.error('Can\'t create "Transactions" table!')


# Create table to store current positions and p&l
async def create_positions_table():
    try:
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS positions (
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_cost REAL NOT NULL, -- average cost per token
            realized_pnl REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, symbol)
            )
        ''')
        conn.commit()
        log.info('Table "Actions" has been created')
    except Exception as e:
        log.error(f'Can\'t create "Positions" table! Reason{e}')





# -------------------- Helper Functions -------------------------

# One-time function for DB migration
async def migrate_messafes_to_positions():
    # Ensure new tables exist
    await create_positions_table()
    await create_transactions_table()

    # Read existing positions from old table
    c.execute('SELECT user_id, pair, price, token_amount FROM messages')
    rows = c.fetchall()

    for user_id, pair, avg_cost, qty in rows:
        symbol = (pair or '').upper().strip()
        if not symbol or qty is None or avg_cost is None:
            continue
        
        # Insert/replcae position
        c.execute(
            '''
            INSERT INTO positions (user_id, symbol, quantity, avg_cost, realized_pnl)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT (user_id, symbol) DO UPDATE SET
                quantity=excluded.quantity,
                avg_cost=excluded.avg_cost,
                updated_at=datetime("now")
            ''', (user_id, symbol, float(qty), float(avg_cost))
        )