import psycopg2
import psycopg2.extras

def get_connection():
    try:
        connection = psycopg2.connect(
            host='localhost',
            database='estudia_mejor_db',
            user='postgres',
            password='123456',
            port='5432'
        )
        return connection
    except Exception as e:
        print("Error al conectar a PostgreSQL:", e)
        return None