from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(paie_variablepaie);")
    for row in cursor.fetchall():
        print(row)
