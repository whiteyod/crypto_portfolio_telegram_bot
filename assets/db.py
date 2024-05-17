import sqlite3

# Connecting  to database
conn = sqlite3.connect('messages.db')
c = conn.cursor()


# Create the table for tickers list
async def create_tickers_table(user_id):
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

