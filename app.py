import os
from flask import Flask, render_template, redirect, url_for, flash, request
from conexion.conexion import get_connection
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2.extras
import psycopg2

# ------------------ APLICACIÓN FLASK ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'clave-secreta-para-desarrollo'

# ------------------ CONFIGURACIÓN DE FLASK-LOGIN ------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

# ------------------ IMPORTAR FORMULARIOS ------------------
from forms.actividad_form import ActividadForm
from forms.estudiante_form import EstudianteForm
from forms.recurso_form import RecursoForm
from forms.rendimiento_form import RendimientoForm
from forms.login_form import LoginForm
from forms.usuario_form import UsuarioForm

# ------------------ IMPORTAR MODELO DE USUARIO ------------------
from models import User


# ------------------ CARGADOR DE USUARIO (Flask-Login) ------------------
@login_manager.user_loader
def load_user(user_id):
    """Recupera el usuario desde la BD por su id."""
    return User.get_by_id(int(user_id))


# ==================================================================
#                       MÓDULO AUTENTICACIÓN
# ==================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicia sesión validando usuario y contraseña con hash."""
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))

    form = LoginForm()
    if form.validate_on_submit():
        # SELECT parametrizado
        user = User.get_by_usuario(form.usuario.data)

        # Validar con check_password_hash (nunca comparar texto plano)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Bienvenido, {user.usuario}', 'success')

            # Redirigir a la página que intentaba acceder
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('inicio'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html', form=form)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registra un nuevo usuario con contraseña hasheada."""
    form = UsuarioForm()
    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()

                # Verificar que el usuario no exista (aunque la BD ya tiene UNIQUE)
                cursor.execute(
                    'SELECT id FROM usuarios WHERE usuario = %s',
                    (form.usuario.data,)
                )
                if cursor.fetchone():
                    flash('El nombre de usuario ya está registrado.', 'danger')
                    return render_template('registro.html', form=form)

                # Generar HASH de la contraseña
                password_hash = generate_password_hash(form.password.data)

                # INSERT parametrizado
                cursor.execute(
                    'INSERT INTO usuarios (usuario, password) VALUES (%s, %s)',
                    (form.usuario.data, password_hash)
                )
                conn.commit()
                flash('Usuario registrado correctamente. Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('login'))

            except Exception as e:
                conn.rollback()
                flash(f'Error al registrar: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()

    return render_template('registro.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario autenticado."""
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))


# ==================================================================
#                       RUTA PRINCIPAL (protegida)
# ==================================================================
@app.route('/')
@login_required
def inicio():
    actividades_disponibles = [
        {"nombre": "Proyecto Flask", "estado": True},
        {"nombre": "Examen de Base de Datos", "estado": False},
        {"nombre": "Tarea de Programación", "estado": True}
    ]
    estudiante = {
        "nombre": "Fernando Matías Sarango",
        "carrera": "Tecnologías de la Información"
    }
    return render_template(
        'index.html',
        mensaje="Bienvenido al Sistema de Gestión Académica",
        estudiante=estudiante,
        actividades=actividades_disponibles
    )


# ==================================================================
#                       MÓDULO ACTIVIDADES
# ==================================================================
@app.route('/actividades', methods=['GET', 'POST'])
@login_required
def actividades():
    form = ActividadForm()

    conn = get_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, nombre FROM estudiantes ORDER BY nombre')
        estudiantes_db = cursor.fetchall()
        cursor.close()
        conn.close()
        form.estudiante_id.choices = [(e['id'], e['nombre']) for e in estudiantes_db]

    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO actividades (nombre, descripcion, categoria, estudiante_id)
                    VALUES (%s, %s, %s, %s)
                ''', (form.nombre.data, form.descripcion.data, form.categoria.data, form.estudiante_id.data))
                conn.commit()
                flash('Actividad agregada correctamente', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error al agregar: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('actividades'))

    conn = get_connection()
    lista_actividades = []
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT a.id, a.nombre, a.descripcion, a.categoria, e.nombre as estudiante_nombre
            FROM actividades a
            LEFT JOIN estudiantes e ON a.estudiante_id = e.id
            ORDER BY a.id DESC
        ''')
        lista_actividades = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('actividades.html', form=form, lista_actividades=lista_actividades)


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_actividad(id):
    conn = get_connection()
    if not conn: return "Error de conexión"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM actividades WHERE id = %s', (id,))
    actividad = cursor.fetchone()

    if not actividad:
        flash('Actividad no encontrada', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('actividades'))

    form = ActividadForm(data=dict(actividad))

    cursor.execute('SELECT id, nombre FROM estudiantes ORDER BY nombre')
    estudiantes_db = cursor.fetchall()
    form.estudiante_id.choices = [(e['id'], e['nombre']) for e in estudiantes_db]

    if form.validate_on_submit():
        try:
            cursor.execute('''
                UPDATE actividades
                SET nombre = %s, descripcion = %s, categoria = %s, estudiante_id = %s
                WHERE id = %s
            ''', (form.nombre.data, form.descripcion.data, form.categoria.data, form.estudiante_id.data, id))
            conn.commit()
            flash('Actividad actualizada', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error al actualizar: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('actividades'))

    cursor.close()
    conn.close()
    return render_template('formulario_actividad.html', form=form, accion='Editar')


@app.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_actividad(id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM actividades WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Actividad eliminada', 'info')
    return redirect(url_for('actividades'))


# ==================================================================
#                       MÓDULO ESTUDIANTES
# ==================================================================
@app.route('/estudiantes', methods=['GET', 'POST'])
@login_required
def estudiantes_lista():
    form = EstudianteForm()
    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO estudiantes (nombre, email, telefono, carrera, direccion)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (form.nombre.data, form.email.data, form.telefono.data,
                      form.carrera.data, form.direccion.data))
                conn.commit()
                flash('Estudiante agregado correctamente', 'success')
            except psycopg2.IntegrityError:
                conn.rollback()
                flash('Error: El correo ya está registrado.', 'danger')
            except Exception as e:
                conn.rollback()
                flash(f'Error inesperado: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('estudiantes_lista'))

    conn = get_connection()
    lista_estudiantes = []
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM estudiantes ORDER BY id DESC')
        lista_estudiantes = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('estudiantes.html', form=form, lista_estudiantes=lista_estudiantes)


@app.route('/estudiantes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def estudiante_editar(id):
    conn = get_connection()
    if not conn: return "Error de conexión"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM estudiantes WHERE id = %s', (id,))
    estudiante = cursor.fetchone()

    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('estudiantes_lista'))

    form = EstudianteForm(data=dict(estudiante))
    if form.validate_on_submit():
        try:
            cursor.execute('''
                UPDATE estudiantes
                SET nombre = %s, email = %s, telefono = %s, carrera = %s, direccion = %s
                WHERE id = %s
            ''', (form.nombre.data, form.email.data, form.telefono.data,
                  form.carrera.data, form.direccion.data, id))
            conn.commit()
            flash('Estudiante actualizado correctamente', 'success')
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('El correo electrónico ya está en uso por otro estudiante', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Error inesperado: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('estudiantes_lista'))

    cursor.close()
    conn.close()
    return render_template('formulario_estudiante.html', form=form, accion='Editar')


@app.route('/estudiantes/eliminar/<int:id>', methods=['POST'])
@login_required
def estudiante_eliminar(id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM estudiantes WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Estudiante eliminado correctamente', 'info')
    return redirect(url_for('estudiantes_lista'))


# ==================================================================
#                       MÓDULO RECURSOS
# ==================================================================
@app.route('/recursos', methods=['GET', 'POST'])
@login_required
def recursos_lista():
    form = RecursoForm()
    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO recursos (nombre, tipo, descripcion, cantidad)
                    VALUES (%s, %s, %s, %s)
                ''', (form.nombre.data, form.tipo.data, form.descripcion.data, form.cantidad.data))
                conn.commit()
                flash('Recurso agregado correctamente', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('recursos_lista'))

    conn = get_connection()
    lista_recursos = []
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM recursos ORDER BY id DESC')
        lista_recursos = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('recursos.html', form=form, lista_recursos=lista_recursos)


@app.route('/recursos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def recurso_editar(id):
    conn = get_connection()
    if not conn: return "Error"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM recursos WHERE id = %s', (id,))
    recurso = cursor.fetchone()

    if not recurso:
        flash('Recurso no encontrado', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('recursos_lista'))

    form = RecursoForm(data=dict(recurso))
    if form.validate_on_submit():
        try:
            cursor.execute('''
                UPDATE recursos
                SET nombre = %s, tipo = %s, descripcion = %s, cantidad = %s
                WHERE id = %s
            ''', (form.nombre.data, form.tipo.data, form.descripcion.data, form.cantidad.data, id))
            conn.commit()
            flash('Recurso actualizado', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('recursos_lista'))

    cursor.close()
    conn.close()
    return render_template('formulario_recurso.html', form=form, accion='Editar')


@app.route('/recursos/eliminar/<int:id>', methods=['POST'])
@login_required
def recurso_eliminar(id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM recursos WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Recurso eliminado', 'info')
    return redirect(url_for('recursos_lista'))


# ==================================================================
#                       MÓDULO RENDIMIENTO
# ==================================================================
@app.route('/rendimiento', methods=['GET', 'POST'])
@login_required
def rendimiento_lista():
    form = RendimientoForm()
    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rendimiento (estudiante, asignatura, nota, fecha, observaciones)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (form.estudiante.data, form.asignatura.data, form.nota.data,
                      form.fecha.data, form.observaciones.data))
                conn.commit()
                flash('Registro de rendimiento agregado', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('rendimiento_lista'))

    conn = get_connection()
    lista_rendimientos = []
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM rendimiento ORDER BY id DESC')
        lista_rendimientos = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template('rendimiento.html', form=form, lista_rendimientos=lista_rendimientos)


@app.route('/rendimiento/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def rendimiento_editar(id):
    conn = get_connection()
    if not conn: return "Error"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM rendimiento WHERE id = %s', (id,))
    rend = cursor.fetchone()

    if not rend:
        flash('Registro no encontrado', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('rendimiento_lista'))

    form = RendimientoForm(data=dict(rend))
    if form.validate_on_submit():
        try:
            cursor.execute('''
                UPDATE rendimiento
                SET estudiante = %s, asignatura = %s, nota = %s, fecha = %s, observaciones = %s
                WHERE id = %s
            ''', (form.estudiante.data, form.asignatura.data, form.nota.data,
                  form.fecha.data, form.observaciones.data, id))
            conn.commit()
            flash('Registro actualizado', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('rendimiento_lista'))

    cursor.close()
    conn.close()
    return render_template('formulario_rendimiento.html', form=form, accion='Editar')


@app.route('/rendimiento/eliminar/<int:id>', methods=['POST'])
@login_required
def rendimiento_eliminar(id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rendimiento WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Registro eliminado', 'info')
    return redirect(url_for('rendimiento_lista'))


# ------------------ EJECUCIÓN ------------------
if __name__ == '__main__':
    app.run(debug=True)