import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Cargar variables del archivo .env (solo funciona en local)
load_dotenv()


def get_connection():
    """
    Establece la conexión con PostgreSQL.
    - En Render usa DATABASE_URL (variable de entorno del servicio).
    - En local usa las variables DB_HOST, DB_NAME, etc. del archivo .env
    """
    try:
        # ---------------------------------------------------------
        # PRIORIDAD 1: Variable DATABASE_URL (Render la inyecta)
        # ---------------------------------------------------------
        database_url = os.getenv('DATABASE_URL')

        if database_url:
            # Render puede entregar la URL con el prefijo "postgres://"
            # pero psycopg2 requiere "postgresql://"
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)

            connection = psycopg2.connect(database_url)
            return connection

        # ---------------------------------------------------------
        # PRIORIDAD 2: Variables separadas (entorno local)
        # ---------------------------------------------------------
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