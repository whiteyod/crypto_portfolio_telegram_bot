import sqlite3


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
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS actions (
        [id] INTEGER PRIMARY KEY AUTOINCREMENT,
        [user_id] INTEGER NOT NULL,
        [action_type] TEXT NOT NULL, -- BUY, SELL, DROP, UPDATE
        [pair] TEXT,
        [payload_json] TEXT NOT NULL,
        [created_at] TEXT DEFAULT (datetime("now"))
        )
        ''')
    conn.commit()


# Create table to store full transaction data
async def create_transactions_table():
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY ATOINCREMENT,
        user_id  INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL, -- "BUY" or "SELL"
        quantity REAL NOT NULL, -- token quantity
        price REAL NOT NULL, -- price per token (USD)
        fee_usd REAL NOT NULL DEFAULT 0,
        timestamp TEXT DEFAULT (datetime("now")),
        note TEXT
        )
    ''')
    conn.commit()


# Create table to store current positions and p&l
async def create_positions_table():
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS positions (
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        quantity REAL NOT NULL,
        avg_cost REAL NOT NULL, -- average cost per token
        realized_pnl REAL NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT (datetime("now")),
        PRIMARY KEY (user_id, symbol)
        )
    ''')
    conn.commit()