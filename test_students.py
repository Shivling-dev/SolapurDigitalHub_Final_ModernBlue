
from db import get_connection

conn = get_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute('SELECT * FROM students ORDER BY created_at DESC LIMIT 5')
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()
