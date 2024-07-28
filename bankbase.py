import sqlite3
conn = sqlite3.connect('bankbase.db')
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS bank (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cardnumber INTEGER,
    expmonth INTEGER,
    expyear INTEGER,
    cvv INTEGER,
    balance FLOAT
)
''')
conn.commit()
conn.close() 