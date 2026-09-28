import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

def get_connection():
    """Establece la conexión con PostgreSQL usando variables de entorno."""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        return connection
    except Exception as e:
        print("Error al conectar a PostgreSQL:", e)
        return None