import sqlite3
import datetime

connection = sqlite3.connect("project.db",check_same_thread=False)
cursor = connection.cursor()

dates= cursor.execute("select id, released from shows").fetchall()
print(dates)

for row in dates:
    print(row)
    ndate = datetime.datetime.strptime(row[1], '%d %b %Y').strftime('%Y/%m/%d')
    print(ndate)
    cursor.execute("UPDATE shows SET released = ? WHERE id = ?", (ndate,row[0]))

connection.commit()