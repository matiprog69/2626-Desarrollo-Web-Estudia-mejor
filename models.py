from flask_login import UserMixin
from conexion.conexion import get_connection


class User(UserMixin):
    """
    Clase de usuario compatible con Flask-Login mediante UserMixin.
    Representa un registro de la tabla 'usuarios'.
    """

    def __init__(self, id, usuario, password):
        self.id = id
        self.usuario = usuario
        self.password = password

    # ------------------------------------------------------------
    # Métodos estáticos (usan consultas parametrizadas)
    # ------------------------------------------------------------

    @staticmethod
    def get_by_id(user_id):
        """Recupera un usuario desde la BD por su identificador."""
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, usuario, password FROM usuarios WHERE id = %s',
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return User(id=row[0], usuario=row[1], password=row[2])
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_usuario(usuario):
        """Recupera un usuario desde la BD por su nombre de usuario."""
        conn = get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, usuario, password FROM usuarios WHERE usuario = %s',
                (usuario,)
            )
            row = cursor.fetchone()
            if row:
                return User(id=row[0], usuario=row[1], password=row[2])
            return None
        finally:
            cursor.close()
            conn.close()