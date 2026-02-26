from math import e
from multiprocessing import Value
import sqlite3
from loguru import logger as log


# Connecting  to database
conn = sqlite3.connect('assets.db')
c = conn.cursor()


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




# ----------------------------- Table creation ----------------------------


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





# ------------------------- Helper Functions -------------------------


# Get one position from the DB
async def get_position(user_id: int, symbol: str):
    c.execute(
        ''' 
        SELECT quantity, avg_cost, realized_pnl
        FROM positions
        WHERE user_id = ? AND symbol = ?
        ''', (user_id, symbol.upper().strip())
    )

    return c.fetchone()


# Get all the positions from the DB
async def get_position_all(user_id: int):
    c.execute(
        '''
        SELECT symbol, quantity, avg_cost, realized_pnl
        FROM positions
        WHERE user_id = ?
        ''', (user_id,)
    )

    return c.fetchall()


# Add new buy transaction and save symbol values to the positions
async def apply_buy(
    user_id: int, symbol: str, qty: float, price: float, fee_usd: float = 0.0
    ):
    # Convert symbol name 
    symbol = symbol.upper().strip()
    # Validate symbol values
    if qty <= 0 or price <= 0:
        raise ValueError('qty and price must be > 0')

    # Get previos position data if exists, else map new values to be saved
    pos = await get_position(user_id, symbol)
    if pos is None:
        old_qty, old_avg, old_realized = 0, 0, 0
    else: 
        old_qty, old_avg, old_realized = map(float, pos)
    
    # Calculate new position values
    new_qty = old_qty + qty
    total_cost = (old_qty * old_avg) + (qty * price) + fee_usd
    new_avg = total_cost / new_qty

    # Insert new transaction data
    c.execute(
        '''
        INSERT INTO transactions (user_id, symbol, side, quantity, price, fee_usd)
        VALUES (?, ?, 'BUY', ?, ?, ?)
        ''', (user_id, symbol, qty, price, fee_usd)
    )
    
    # Insert new position's data
    c.execute(
        '''
        INSERT INTO positions (user_id, symbol, quantity, avg_cost, realized_pnl)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, symbol) DO UPDATE SET
            quantity=excluded.quantity,
            avg_cost=excluded.avg_cost,
            realized_pnl=excluded.realized_pnl,
            updated_at=CURRENT_TIMESTAMP
        ''', (user_id, symbol, new_qty, new_avg, old_realized)
    )
    
    conn.commit()


# Add new sell transaction and save updated symbol values to the postitions
async def apply_sell(
    user_id: int, symbol: str, qty: float, price: float, fee_usd: float = 0.0
    ):
    # Convert symbol name
    symbol = symbol.upper().strip()
    if qty <= 0 or price <= 0:
        raise ValueError('qty and price must be > 0')
    
    # Get position data
    pos = await get_position(user_id, symbol)
    if pos is None:
        raise ValueError('no position')
    
    # If exists map data and calculate new position values
    old_qty, avg_cost, realized = map(float, pos)
    if qty > old_qty + 1e-12:
        raise ValueError('not enough quantity')
    
    realized_delta = (qty * (price - avg_cost)) - fee_usd
    new_realized = realized + realized_delta
    new_qty = old_qty - qty
    
    # Add new transaction data
    c.execute(
        '''
        INSERT INTO transactions (user_id, symbol, side, quantity, price, fee_usd)
        VALUES (?, ?, 'SELL', ?, ?, ?)
        ''', (user_id, symbol, qty, price, fee_usd)
    )

    # Close position if all qty has been selling and delete position
    if new_qty <= 1e-12:
        c.execute(
            'DELETE FROM positions WHERE user_id = ? AND symbol = ?',
            (user_id, symbol)
        )
    else: # Update remaining position
        c.execute(
            '''
            UPDATE positions
            SET quantity = ?, realized_pnl = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND symbol = ?
            ''', (new_qty, new_realized, user_id, symbol)
        )
        
    conn.commit()