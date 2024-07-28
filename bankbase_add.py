import sqlite3

conn = sqlite3.connect('bankbase.db')
cur = conn.cursor()
data = [
    (1234567890123456, 12, 25, 123, 1000.50),
    (2345678901234567, 11, 24, 456, 2500.00),
    (3456789012345678, 10, 23, 789, 1500.00)
]
cur.executemany('''
INSERT INTO bank (cardnumber, expmonth, expyear, cvv, balance)
VALUES (?, ?, ?, ?, ?)
''', data)
conn.commit()
conn.close()