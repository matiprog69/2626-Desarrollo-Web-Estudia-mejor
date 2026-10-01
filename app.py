import os
import calendar
from datetime import date, datetime, timedelta
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from conexion.conexion import get_connection
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect          # ← ESTA LÍNEA FALTA
import psycopg2.extras
import psycopg2

# ------------------ APLICACIÓN FLASK ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'clave-secreta-para-desarrollo'

# ------------------ PROTECCIÓN CSRF ------------------
csrf = CSRFProtect(app)

# ------------------ CONFIGURACIÓN DE FLASK-LOGIN ------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'
# ------------------ IMPORTAR FORMULARIOS ------------------
# ------------------ IMPORTAR FORMULARIOS ------------------
from forms.actividad_form import ActividadForm
from forms.estudiante_form import EstudianteForm
from forms.recurso_form import RecursoForm
from forms.rendimiento_form import RendimientoForm
from forms.login_form import LoginForm
from forms.usuario_form import UsuarioForm
from forms.servicio_form import ServicioForm
from forms.producto_form import ProductoForm
from forms.factura_form import FacturaForm
from utils.pdf_factura import generar_pdf_factura
from forms.pago_form import PagoForm
from flask_wtf.csrf import CSRFProtect

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
    """Página principal con estadísticas y servicios destacados."""
    conn = get_connection()
    stats = {
        'servicios': 0,
        'productos': 0,
        'estudiantes': 0,
        'facturas': 0,
    }
    servicios_destacados = []

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Contadores para estadísticas
        cursor.execute('SELECT COUNT(*) AS total FROM servicios WHERE activo = TRUE')
        stats['servicios'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) AS total FROM productos WHERE activo = TRUE')
        stats['productos'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) AS total FROM estudiantes')
        stats['estudiantes'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) AS total FROM facturas')
        stats['facturas'] = cursor.fetchone()['total']

        # Servicios con sus primeros 3 productos
        cursor.execute('''
            SELECT id, nombre, descripcion, icono
            FROM servicios
            WHERE activo = TRUE
            ORDER BY id
            LIMIT 4
        ''')
        servicios_destacados = cursor.fetchall()

        for s in servicios_destacados:
            cursor.execute('''
                SELECT id, nombre, precio
                FROM productos
                WHERE servicio_id = %s AND activo = TRUE
                ORDER BY id
                LIMIT 3
            ''', (s['id'],))
            s['productos'] = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template(
        'index.html',
        stats=stats,
        servicios_destacados=servicios_destacados
    )

# ==================================================================
#                       MÓDULO ACTIVIDADES
# ==================================================================
@app.route('/actividades', methods=['GET', 'POST'])
@login_required
def actividades():
    form = ActividadForm()

    # Cargar estudiantes para el SelectField
    conn = get_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, nombre FROM estudiantes ORDER BY nombre')
        estudiantes_db = cursor.fetchall()
        cursor.close()
        conn.close()
        form.estudiante_id.choices = [(e['id'], e['nombre']) for e in estudiantes_db]

    # Si el formulario se envía desde el modal
    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO actividades (nombre, descripcion, categoria, estudiante_id)
                    VALUES (%s, %s, %s, %s)
                ''', (form.nombre.data, form.descripcion.data,
                      form.categoria.data, form.estudiante_id.data))
                conn.commit()
                flash('Actividad agregada correctamente', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error al agregar: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('actividades'))

    # Cargar datos para mostrar
    conn = get_connection()
    lista_actividades = []
    stats = {
        'total': 0,
        'categorias': 0,
        'estudiantes': 0,
        'ultima': '—',
    }

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Lista con JOIN
        cursor.execute('''
            SELECT a.id, a.nombre, a.descripcion, a.categoria,
                   e.nombre AS estudiante_nombre
            FROM actividades a
            LEFT JOIN estudiantes e ON a.estudiante_id = e.id
            ORDER BY a.id DESC
        ''')
        lista_actividades = cursor.fetchall()

        # Estadísticas
        cursor.execute('SELECT COUNT(*) AS total FROM actividades')
        stats['total'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(DISTINCT categoria) AS total FROM actividades')
        stats['categorias'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(DISTINCT estudiante_id) AS total FROM actividades')
        stats['estudiantes'] = cursor.fetchone()['total']

        cursor.execute('SELECT nombre FROM actividades ORDER BY id DESC LIMIT 1')
        ultima = cursor.fetchone()
        stats['ultima'] = ultima['nombre'] if ultima else '—'

        cursor.close()
        conn.close()

    return render_template(
        'actividades.html',
        form=form,
        lista_actividades=lista_actividades,
        stats=stats
    )

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
            ''', (form.nombre.data, form.descripcion.data,
                  form.categoria.data, form.estudiante_id.data, id))
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

    # Cargar datos y estadísticas
    conn = get_connection()
    lista_estudiantes = []
    stats = {
        'total': 0,
        'carreras': 0,
        'con_email': 0,
        'ultimo': '—',
    }

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('SELECT * FROM estudiantes ORDER BY id DESC')
        lista_estudiantes = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) AS total FROM estudiantes')
        stats['total'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(DISTINCT carrera) AS total FROM estudiantes')
        stats['carreras'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) AS total FROM estudiantes WHERE email IS NOT NULL')
        stats['con_email'] = cursor.fetchone()['total']

        cursor.execute('SELECT nombre FROM estudiantes ORDER BY id DESC LIMIT 1')
        ultimo = cursor.fetchone()
        stats['ultimo'] = ultimo['nombre'] if ultimo else '—'

        cursor.close()
        conn.close()

    return render_template(
        'estudiantes.html',
        form=form,
        lista_estudiantes=lista_estudiantes,
        stats=stats
    )

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
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM estudiantes WHERE id = %s', (id,))
            conn.commit()
            flash('Estudiante eliminado correctamente.', 'info')
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'fk_estudiante_factura' in str(e):
                flash(
                    'No se puede eliminar: este estudiante tiene facturas asociadas. '
                    'Elimina primero sus facturas.',
                    'danger'
                )
            elif 'actividades' in str(e):
                flash(
                    'No se puede eliminar: este estudiante tiene actividades asignadas. '
                    'Elimina primero sus actividades.',
                    'danger'
                )
            elif 'rendimiento' in str(e):
                flash(
                    'No se puede eliminar: este estudiante tiene registros de rendimiento. '
                    'Elimina primero sus registros.',
                    'danger'
                )
            else:
                flash(f'No se puede eliminar el estudiante: {e}', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Error inesperado: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('estudiantes_lista'))

# ==================================================================
#                       MÓDULO RECURSOS
# ==================================================================
@app.route('/recursos', methods=['GET', 'POST'])
@login_required
def recursos_lista():
    form = RecursoForm()

    # Cargar servicios para el SelectField
    conn = get_connection()
    servicios_db = []
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, nombre FROM servicios WHERE activo = TRUE ORDER BY nombre')
        servicios_db = cursor.fetchall()
        cursor.close()
        conn.close()
    # Opción "Sin servicio" = 0
    form.servicio_id.choices = [(0, '— Sin servicio asociado —')] + [
        (s['id'], s['nombre']) for s in servicios_db
    ]

    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Si servicio_id es 0, guardar NULL
                servicio_id = form.servicio_id.data if form.servicio_id.data != 0 else None

                cursor.execute('''
                    INSERT INTO recursos (nombre, tipo, descripcion, cantidad, servicio_id)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    form.nombre.data,
                    form.tipo.data,
                    form.descripcion.data,
                    form.cantidad.data,
                    servicio_id
                ))
                conn.commit()
                flash('Recurso agregado correctamente', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('recursos_lista'))

    # Cargar lista con JOIN a servicios y estadísticas
    conn = get_connection()
    lista_recursos = []
    stats = {
        'total': 0,
        'tipos': 0,
        'cantidad_total': 0,
        'ultimo': '—',
    }

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('''
            SELECT r.*, s.nombre AS servicio_nombre
            FROM recursos r
            LEFT JOIN servicios s ON r.servicio_id = s.id
            ORDER BY r.id DESC
        ''')
        lista_recursos = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) AS total FROM recursos')
        stats['total'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(DISTINCT tipo) AS total FROM recursos')
        stats['tipos'] = cursor.fetchone()['total']

        cursor.execute('SELECT COALESCE(SUM(cantidad), 0) AS total FROM recursos')
        stats['cantidad_total'] = cursor.fetchone()['total']

        cursor.execute('SELECT nombre FROM recursos ORDER BY id DESC LIMIT 1')
        ultimo = cursor.fetchone()
        stats['ultimo'] = ultimo['nombre'] if ultimo else '—'

        cursor.close()
        conn.close()

    return render_template(
        'recursos.html',
        form=form,
        lista_recursos=lista_recursos,
        stats=stats
    )

@app.route('/recursos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def recurso_editar(id):
    conn = get_connection()
    if not conn: return "Error"

    # Cargar servicios primero para el SelectField
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT id, nombre FROM servicios WHERE activo = TRUE ORDER BY nombre')
    servicios_db = cursor.fetchall()

    cursor.execute('SELECT * FROM recursos WHERE id = %s', (id,))
    recurso = cursor.fetchone()

    if not recurso:
        flash('Recurso no encontrado', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('recursos_lista'))

    form = RecursoForm(data=dict(recurso))
    form.servicio_id.choices = [(0, '— Sin servicio asociado —')] + [
        (s['id'], s['nombre']) for s in servicios_db
    ]

    if form.validate_on_submit():
        try:
            servicio_id = form.servicio_id.data if form.servicio_id.data != 0 else None

            cursor.execute('''
                UPDATE recursos
                SET nombre = %s, tipo = %s, descripcion = %s,
                    cantidad = %s, servicio_id = %s
                WHERE id = %s
            ''', (
                form.nombre.data,
                form.tipo.data,
                form.descripcion.data,
                form.cantidad.data,
                servicio_id,
                id
            ))
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

    # Cargar estudiantes para el SelectField
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
                # Obtener nombre del estudiante para la columna legacy
                cursor.execute(
                    'SELECT nombre FROM estudiantes WHERE id = %s',
                    (form.estudiante_id.data,)
                )
                est = cursor.fetchone()
                nombre_est = est[0] if est else ''

                cursor.execute('''
                    INSERT INTO rendimiento
                        (estudiante, estudiante_id, asignatura, nota, fecha, observaciones)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    nombre_est,
                    form.estudiante_id.data,
                    form.asignatura.data,
                    form.nota.data,
                    form.fecha.data,
                    form.observaciones.data
                ))
                conn.commit()
                flash('Registro de rendimiento agregado', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        return redirect(url_for('rendimiento_lista'))

    # Cargar lista y estadísticas
    conn = get_connection()
    lista_rendimientos = []
    stats = {'total': 0, 'promedio': 0.0, 'aprobados': 0, 'asignaturas': 0}

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('''
            SELECT r.*, e.nombre AS estudiante_nombre
            FROM rendimiento r
            LEFT JOIN estudiantes e ON r.estudiante_id = e.id
            ORDER BY r.id DESC
        ''')
        lista_rendimientos = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) AS total FROM rendimiento')
        stats['total'] = cursor.fetchone()['total']

        cursor.execute('SELECT COALESCE(AVG(nota), 0) AS promedio FROM rendimiento')
        stats['promedio'] = float(cursor.fetchone()['promedio'])

        cursor.execute('SELECT COUNT(*) AS total FROM rendimiento WHERE nota >= 14')
        stats['aprobados'] = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(DISTINCT asignatura) AS total FROM rendimiento')
        stats['asignaturas'] = cursor.fetchone()['total']

        cursor.close()
        conn.close()

    return render_template(
        'rendimiento.html',
        form=form,
        lista_rendimientos=lista_rendimientos,
        stats=stats
    )


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

    cursor.execute('SELECT id, nombre FROM estudiantes ORDER BY nombre')
    estudiantes_db = cursor.fetchall()
    form.estudiante_id.choices = [(e['id'], e['nombre']) for e in estudiantes_db]

    if form.validate_on_submit():
        try:
            cursor.execute(
                'SELECT nombre FROM estudiantes WHERE id = %s',
                (form.estudiante_id.data,)
            )
            est = cursor.fetchone()
            nombre_est = est['nombre'] if est else ''

            cursor.execute('''
                UPDATE rendimiento
                SET estudiante = %s, estudiante_id = %s, asignatura = %s,
                    nota = %s, fecha = %s, observaciones = %s
                WHERE id = %s
            ''', (
                nombre_est,
                form.estudiante_id.data,
                form.asignatura.data,
                form.nota.data,
                form.fecha.data,
                form.observaciones.data,
                id
            ))
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
# ==================================================================
#               MÓDULO SERVICIOS Y PRODUCTOS (Semana 15)
# ==================================================================

# ------------------ VISTA PÚBLICA ------------------
@app.route('/servicios')
@login_required
def servicios_publico():
    """Muestra las categorías con sus productos (vista pública)."""
    conn = get_connection()
    servicios = []

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('''
            SELECT id, nombre, descripcion, icono
            FROM servicios
            WHERE activo = TRUE
            ORDER BY id
        ''')
        servicios = cursor.fetchall()

        for s in servicios:
            cursor.execute('''
                SELECT id, nombre, descripcion, precio, stock, modalidad, imagen
                FROM productos
                WHERE servicio_id = %s AND activo = TRUE
                ORDER BY id
            ''', (s['id'],))
            s['productos'] = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template('servicios.html', servicios=servicios)

# ------------------ PANEL ADMIN ------------------
@app.route('/servicios/administrar')
@login_required
def admin_servicios():
    """Panel de administración: lista categorías y productos."""
    conn = get_connection()
    servicios = []
    productos = []

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute('SELECT * FROM servicios ORDER BY id')
        servicios = cursor.fetchall()

        cursor.execute('''
            SELECT p.*, s.nombre AS categoria
            FROM productos p
            INNER JOIN servicios s ON p.servicio_id = s.id
            ORDER BY s.id, p.id
        ''')
        productos = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template('admin_servicios.html', servicios=servicios, productos=productos)


# ------------------ CRUD CATEGORÍAS ------------------
@app.route('/servicios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_servicio():
    form = ServicioForm()
    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO servicios (nombre, descripcion, icono, activo)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    form.nombre.data,
                    form.descripcion.data,
                    form.icono.data,
                    form.activo.data
                ))
                conn.commit()
                flash('Categoría creada correctamente', 'success')
                return redirect(url_for('admin_servicios'))
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()

    return render_template('formulario_servicio.html', form=form, accion='Crear')


@app.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_servicio(id):
    conn = get_connection()
    if not conn:
        return "Error de conexión"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM servicios WHERE id = %s', (id,))
    servicio = cursor.fetchone()

    if not servicio:
        flash('Categoría no encontrada', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('admin_servicios'))

    form = ServicioForm(data=dict(servicio))

    if form.validate_on_submit():
        try:
            cursor.execute('''
                UPDATE servicios
                SET nombre = %s, descripcion = %s, icono = %s, activo = %s
                WHERE id = %s
            ''', (
                form.nombre.data,
                form.descripcion.data,
                form.icono.data,
                form.activo.data,
                id
            ))
            conn.commit()
            flash('Categoría actualizada', 'success')
            return redirect(url_for('admin_servicios'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    cursor.close()
    conn.close()
    return render_template('formulario_servicio.html', form=form, accion='Editar')

@app.route('/servicios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_servicio(id):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM servicios WHERE id = %s', (id,))
            conn.commit()
            flash('Categoría eliminada correctamente.', 'info')
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'fk_servicio_recurso' in str(e) or 'recursos' in str(e):
                flash(
                    'No se puede eliminar: esta categoría tiene recursos asociados. '
                    'Elimina primero sus recursos o desactívala.',
                    'danger'
                )
            else:
                flash(f'No se puede eliminar la categoría: {e}', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Error inesperado: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('admin_servicios'))

# ------------------ CRUD PRODUCTOS ------------------
@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    form = ProductoForm()

    conn = get_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT id, nombre FROM servicios WHERE activo = TRUE ORDER BY id')
        servicios_db = cursor.fetchall()
        cursor.close()
        conn.close()
        form.servicio_id.choices = [(s['id'], s['nombre']) for s in servicios_db]

    if form.validate_on_submit():
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO productos
                        (servicio_id, nombre, descripcion, precio, stock, modalidad, imagen, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    form.servicio_id.data,
                    form.nombre.data,
                    form.descripcion.data,
                    form.precio.data,
                    form.stock.data,
                    form.modalidad.data,
                    form.imagen.data,
                    form.activo.data
                ))
                conn.commit()
                flash('Producto creado correctamente', 'success')
                return redirect(url_for('admin_servicios'))
            except Exception as e:
                conn.rollback()
                flash(f'Error: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()

    return render_template('formulario_producto.html', form=form, accion='Crear')


@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    conn = get_connection()
    if not conn:
        return "Error de conexión"
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM productos WHERE id = %s', (id,))
    producto = cursor.fetchone()

    if not producto:
        flash('Producto no encontrado', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('admin_servicios'))

    form = ProductoForm(data=dict(producto))

    cursor.execute('SELECT id, nombre FROM servicios WHERE activo = TRUE ORDER BY id')
    servicios_db = cursor.fetchall()
    form.servicio_id.choices = [(s['id'], s['nombre']) for s in servicios_db]

    if form.validate_on_submit():
        try:
            cursor.execute('''
                UPDATE productos
                SET servicio_id = %s, nombre = %s, descripcion = %s,
                    precio = %s, stock = %s, modalidad = %s,
                    imagen = %s, activo = %s
                WHERE id = %s
            ''', (
                form.servicio_id.data,
                form.nombre.data,
                form.descripcion.data,
                form.precio.data,
                form.stock.data,
                form.modalidad.data,
                form.imagen.data,
                form.activo.data,
                id
            ))
            conn.commit()
            flash('Producto actualizado', 'success')
            return redirect(url_for('admin_servicios'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    cursor.close()
    conn.close()
    return render_template('formulario_producto.html', form=form, accion='Editar')


@app.route('/productos/desactivar/<int:id>', methods=['POST'])
@login_required
def desactivar_producto(id):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE productos SET activo = FALSE WHERE id = %s', (id,))
            conn.commit()
            flash('Producto desactivado. Ya no aparecerá en el catálogo.', 'info')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('admin_servicios'))

@app.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM productos WHERE id = %s', (id,))
            conn.commit()
            flash('Producto eliminado correctamente.', 'info')
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'fk_producto' in str(e) or 'detalle_factura' in str(e):
                flash(
                    'No se puede eliminar: este producto ya fue usado en una factura. '
                    'En lugar de eliminarlo, edítalo y desactívalo.',
                    'danger'
                )
            else:
                flash(f'No se puede eliminar el producto: {e}', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Error inesperado: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('admin_servicios'))



# ==================================================================
#               MÓDULO FACTURACIÓN (Semana 15)
# ==================================================================

def add_months(source_date, months):
    """Suma N meses a una fecha, respetando el día correcto."""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


# ------------------ LISTA DE FACTURAS ------------------
@app.route('/facturas')
@login_required
def facturas_lista():
    """Lista todas las facturas con filtro opcional por estado."""
    estado_filtro = request.args.get('estado', '').strip()

    conn = get_connection()
    facturas = []

    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = '''
            SELECT 
                f.id,
                f.fecha_emision,
                f.total,
                f.tipo_pago,
                f.num_cuotas,
                f.estado,
                e.nombre AS estudiante_nombre,
                e.email AS estudiante_email
            FROM facturas f
            INNER JOIN estudiantes e ON f.estudiante_id = e.id
        '''

        params = ()
        if estado_filtro in ('pendiente', 'parcial', 'pagada'):
            query += ' WHERE f.estado = %s '
            params = (estado_filtro,)

        query += ' ORDER BY f.id DESC '

        cursor.execute(query, params)
        facturas = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template(
        'facturas_lista.html',
        facturas=facturas,
        estado_filtro=estado_filtro
    )


# ------------------ NUEVA FACTURA ------------------
@app.route('/facturas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_factura():
    """Formulario para emitir una nueva factura."""
    form = FacturaForm()

    # ============================================================
    # CARGAR ESTUDIANTES PARA EL SELECTFIELD
    # ============================================================
    conn = get_connection()

    if conn:
        cursor = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cursor.execute('''
            SELECT id, nombre
            FROM estudiantes
            ORDER BY nombre
        ''')

        estudiantes_db = cursor.fetchall()

        cursor.close()
        conn.close()

        form.estudiante_id.choices = [
            (e['id'], e['nombre'])
            for e in estudiantes_db
        ]

    # ============================================================
    # CARGAR SERVICIOS Y PRODUCTOS DISPONIBLES
    # ============================================================
    conn = get_connection()
    servicios = []

    if conn:
        cursor = conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        cursor.execute('''
            SELECT id, nombre
            FROM servicios
            WHERE activo = TRUE
            ORDER BY id
        ''')

        servicios = cursor.fetchall()

        for s in servicios:

            cursor.execute('''
                SELECT
                    id,
                    nombre,
                    precio,
                    stock
                FROM productos
                WHERE servicio_id = %s
                  AND activo = TRUE
                  AND stock > 0
                ORDER BY id
            ''', (s['id'],))

            s['productos'] = cursor.fetchall()

        cursor.close()
        conn.close()

    # ============================================================
    # PROCESAR FORMULARIO
    # ============================================================
    if form.validate_on_submit():

        # Los productos vienen como:
        # producto_id|cantidad
        productos_raw = request.form.getlist('productos[]')

        if not productos_raw:
            flash(
                'Debes agregar al menos un producto a la factura.',
                'danger'
            )

            return render_template(
                'nueva_factura.html',
                form=form,
                servicios=servicios
            )

        # ========================================================
        # CONVERTIR PRODUCTOS RECIBIDOS
        # ========================================================
        productos_parseados = []

        for item in productos_raw:

            try:
                prod_id, cant = item.split('|')

                productos_parseados.append(
                    (int(prod_id), int(cant))
                )

            except (ValueError, AttributeError):
                continue

        if not productos_parseados:

            flash(
                'Los productos enviados no son válidos.',
                'danger'
            )

            return render_template(
                'nueva_factura.html',
                form=form,
                servicios=servicios
            )

        # ========================================================
        # CONEXIÓN PARA CREAR LA FACTURA
        # ========================================================
        conn = get_connection()

        if not conn:

            flash(
                'Error de conexión a la base de datos.',
                'danger'
            )

            return render_template(
                'nueva_factura.html',
                form=form,
                servicios=servicios
            )

        cursor = None

        try:

            cursor = conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # ====================================================
            # 1. OBTENER PRODUCTOS, PRECIOS Y VALIDAR STOCK
            # ====================================================
            total = 0
            detalles_a_insertar = []

            for prod_id, cant in productos_parseados:

                cursor.execute('''
                    SELECT
                        id,
                        nombre,
                        precio,
                        stock
                    FROM productos
                    WHERE id = %s
                    FOR UPDATE
                ''', (prod_id,))

                prod = cursor.fetchone()

                # Si el producto no existe
                if not prod:
                    continue

                # -----------------------------------------------
                # Validar cantidad
                # -----------------------------------------------
                if cant <= 0:

                    conn.rollback()

                    flash(
                        f'La cantidad de "{prod["nombre"]}" '
                        f'debe ser mayor a 0.',
                        'danger'
                    )

                    return render_template(
                        'nueva_factura.html',
                        form=form,
                        servicios=servicios
                    )

                # -----------------------------------------------
                # Validar stock
                # -----------------------------------------------
                if prod['stock'] < cant:

                    conn.rollback()

                    flash(
                        f'Stock insuficiente para '
                        f'"{prod["nombre"]}". '
                        f'Disponible: {prod["stock"]}, '
                        f'solicitado: {cant}.',
                        'danger'
                    )

                    return render_template(
                        'nueva_factura.html',
                        form=form,
                        servicios=servicios
                    )

                # -----------------------------------------------
                # Calcular subtotal
                # -----------------------------------------------
                subtotal = float(prod['precio']) * cant

                total += subtotal

                detalles_a_insertar.append({
                    'producto_id': prod['id'],
                    'nombre': prod['nombre'],
                    'precio_unitario': float(prod['precio']),
                    'cantidad': cant,
                    'subtotal': subtotal
                })

            # ====================================================
            # VERIFICAR QUE EXISTAN PRODUCTOS VÁLIDOS
            # ====================================================
            if not detalles_a_insertar:

                conn.rollback()

                flash(
                    'No se encontraron productos válidos.',
                    'danger'
                )

                return render_template(
                    'nueva_factura.html',
                    form=form,
                    servicios=servicios
                )

            # ====================================================
            # 2. DETERMINAR TIPO DE PAGO
            # ====================================================
            tipo_pago = form.tipo_pago.data

            num_cuotas = (
                form.num_cuotas.data
                if tipo_pago == 'cuotas'
                else 1
            )

            # Validación básica de cuotas
            if tipo_pago == 'cuotas':

                if not num_cuotas or num_cuotas <= 0:

                    conn.rollback()

                    flash(
                        'El número de cuotas debe ser mayor a 0.',
                        'danger'
                    )

                    return render_template(
                        'nueva_factura.html',
                        form=form,
                        servicios=servicios
                    )

            # ====================================================
            # 3. INSERTAR FACTURA
            # ====================================================
            cursor.execute('''
                INSERT INTO facturas
                    (
                        estudiante_id,
                        usuario_id,
                        total,
                        tipo_pago,
                        num_cuotas,
                        estado
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                form.estudiante_id.data,
                current_user.id,
                total,
                tipo_pago,
                num_cuotas,
                'pendiente'
            ))

            factura_id = cursor.fetchone()['id']

            # ====================================================
            # 4. INSERTAR DETALLES Y DESCONTAR STOCK
            # ====================================================
            for d in detalles_a_insertar:

                # -----------------------------------------------
                # Guardar detalle de factura
                # -----------------------------------------------
                cursor.execute('''
                    INSERT INTO detalle_factura
                        (
                            factura_id,
                            producto_id,
                            cantidad,
                            precio_unitario,
                            subtotal
                        )
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    factura_id,
                    d['producto_id'],
                    d['cantidad'],
                    d['precio_unitario'],
                    d['subtotal']
                ))

                # -----------------------------------------------
                # Descontar stock del producto
                # -----------------------------------------------
                cursor.execute('''
                    UPDATE productos
                    SET stock = stock - %s
                    WHERE id = %s
                ''', (
                    d['cantidad'],
                    d['producto_id']
                ))

            # ====================================================
            # 5. CREAR CUOTAS / PAGOS
            # ====================================================
            hoy = date.today()

            # ----------------------------------------------------
            # PAGO AL CONTADO
            # ----------------------------------------------------
            if tipo_pago == 'contado':

                cursor.execute('''
                    INSERT INTO pagos
                        (
                            factura_id,
                            numero_cuota,
                            monto,
                            fecha_vencimiento,
                            estado
                        )
                    VALUES (%s, %s, %s, %s, %s)
                ''', (
                    factura_id,
                    1,
                    total,
                    hoy,
                    'pendiente'
                ))

            # ----------------------------------------------------
            # PAGO EN CUOTAS
            # ----------------------------------------------------
            else:

                monto_por_cuota = round(
                    total / num_cuotas,
                    2
                )

                acumulado = 0

                for i in range(1, num_cuotas + 1):

                    # Todas menos la última
                    if i < num_cuotas:

                        monto_cuota = monto_por_cuota

                    # Última cuota
                    else:

                        monto_cuota = round(
                            total - acumulado,
                            2
                        )

                    acumulado += monto_cuota

                    fecha_venc = add_months(
                        hoy,
                        i - 1
                    )

                    cursor.execute('''
                        INSERT INTO pagos
                            (
                                factura_id,
                                numero_cuota,
                                monto,
                                fecha_vencimiento,
                                estado
                            )
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (
                        factura_id,
                        i,
                        monto_cuota,
                        fecha_venc,
                        'pendiente'
                    ))

            # ====================================================
            # 6. GUARDAR TODOS LOS CAMBIOS
            # ====================================================
            conn.commit()

            flash(
                f'Factura #{factura_id:04d} '
                f'emitida correctamente.',
                'success'
            )

            return redirect(
                url_for(
                    'ver_factura',
                    id=factura_id
                )
            )

        # ========================================================
        # MANEJO DE ERRORES
        # ========================================================
        except Exception as e:

            conn.rollback()

            flash(
                f'Error al emitir la factura: {e}',
                'danger'
            )

        finally:

            if cursor:
                cursor.close()

            conn.close()

    # ============================================================
    # MOSTRAR FORMULARIO
    # ============================================================
    return render_template(
        'nueva_factura.html',
        form=form,
        servicios=servicios
    )


# ------------------ VER DETALLE DE FACTURA ------------------
def _cargar_datos_factura(factura_id):
    """Helper: carga factura, detalles, pagos e historial de una factura."""
    conn = get_connection()
    if not conn:
        return None, None, None, None, None, None

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Factura + estudiante + usuario
    cursor.execute('''
        SELECT 
            f.*,
            e.nombre AS estudiante_nombre,
            e.email AS estudiante_email,
            e.telefono AS estudiante_telefono,
            e.carrera AS estudiante_carrera,
            e.direccion AS estudiante_direccion,
            u.usuario AS usuario_emisor
        FROM facturas f
        INNER JOIN estudiantes e ON f.estudiante_id = e.id
        INNER JOIN usuarios u ON f.usuario_id = u.id
        WHERE f.id = %s
    ''', (factura_id,))
    factura = cursor.fetchone()

    if not factura:
        cursor.close()
        conn.close()
        return None, None, None, None, None, None

    # Detalles con JOIN a productos
    cursor.execute('''
        SELECT 
            d.*,
            p.nombre AS producto_nombre
        FROM detalle_factura d
        INNER JOIN productos p ON d.producto_id = p.id
        WHERE d.factura_id = %s
        ORDER BY d.id
    ''', (factura_id,))
    detalles = cursor.fetchall()

    # Pagos (cuotas)
    cursor.execute('''
        SELECT * FROM pagos WHERE factura_id = %s ORDER BY numero_cuota
    ''', (factura_id,))
    pagos = cursor.fetchall()

    # Historial de pagos realizados
    cursor.execute('''
        SELECT 
            pr.*,
            p.numero_cuota
        FROM pagos_realizados pr
        INNER JOIN pagos p ON pr.pago_id = p.id
        WHERE p.factura_id = %s
        ORDER BY pr.fecha_pago DESC
    ''', (factura_id,))
    pagos_realizados = cursor.fetchall()

    # Total pagado
    cursor.execute('''
        SELECT COALESCE(SUM(monto_pagado), 0) AS total_pagado
        FROM pagos
        WHERE factura_id = %s
    ''', (factura_id,))
    total_pagado = float(cursor.fetchone()['total_pagado'])

    cursor.close()
    conn.close()

    return factura, detalles, pagos, total_pagado, pagos_realizados, conn

@app.route('/facturas/<int:id>')
@login_required
def ver_factura(id):
    """Muestra el detalle completo de una factura."""
    factura, detalles, pagos, total_pagado, pagos_realizados, _ = _cargar_datos_factura(id)

    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('facturas_lista'))

    return render_template(
        'factura_detalle.html',
        factura=factura,
        detalles=detalles,
        pagos=pagos,
        pagos_realizados=pagos_realizados,
        total_pagado=total_pagado
    )


# ------------------ DESCARGAR PDF ------------------
@app.route('/facturas/<int:id>/pdf')
@login_required
def descargar_factura_pdf(id):
    """Genera y descarga el PDF de la factura (solo si está pagada al 100%)."""
    factura, detalles, pagos, total_pagado, pagos_realizados, _ = _cargar_datos_factura(id)

    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('facturas_lista'))

    # ⚠️ Solo se puede descargar si está totalmente pagada
    if factura['estado'] != 'pagada':
        flash(
            'Solo puedes descargar la factura cuando esté completamente pagada.',
            'warning'
        )
        return redirect(url_for('ver_factura', id=id))

    pdf_buffer = generar_pdf_factura(factura, detalles, pagos, total_pagado)

    nombre_archivo = f'factura_{id:04d}.pdf'
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype='application/pdf'
    )

# ------------------ MARCAR PAGO COMO REALIZADO ------------------
@app.route('/pagos/<int:pago_id>/agregar', methods=['POST'])
@login_required
def agregar_pago(pago_id):
    """Registra un pago (parcial o total) sobre una cuota."""
    form = PagoForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
        return redirect(url_for('facturas_lista'))

    monto_ingresado = float(form.monto.data)
    metodo = form.metodo_pago.data

    conn = get_connection()
    if not conn:
        flash('Error de conexión.', 'danger')
        return redirect(url_for('facturas_lista'))

    factura_id = None
    cursor = None

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. Obtener el pago (cuota)
        cursor.execute('SELECT * FROM pagos WHERE id = %s', (pago_id,))
        pago = cursor.fetchone()

        if not pago:
            flash('Pago no encontrado.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('facturas_lista'))

        factura_id = pago['factura_id']

        # 2. Si ya está pagado, no hacer nada
        if pago['estado'] == 'pagado':
            flash('Esta cuota ya estaba completamente pagada.', 'info')
            cursor.close()
            conn.close()
            return redirect(url_for('ver_factura', id=factura_id))

        # 3. Validar monto
        monto_total = float(pago['monto'])
        monto_previo = float(pago['monto_pagado'] or 0)
        pendiente = monto_total - monto_previo

        if monto_ingresado <= 0:
            flash('El monto debe ser mayor a 0.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('ver_factura', id=factura_id))

        if monto_ingresado > pendiente + 0.01:
            flash(
                f'El monto no puede exceder lo pendiente (${pendiente:.2f}).',
                'danger'
            )
            cursor.close()
            conn.close()
            return redirect(url_for('ver_factura', id=factura_id))

        # 4. Insertar en pagos_realizados
        cursor.execute('''
            INSERT INTO pagos_realizados (pago_id, monto, metodo_pago)
            VALUES (%s, %s, %s)
        ''', (pago_id, monto_ingresado, metodo))

        # 5. Actualizar monto_pagado y estado de la cuota
        nuevo_pagado = monto_previo + monto_ingresado
        if nuevo_pagado >= monto_total - 0.01:
            cursor.execute('''
                UPDATE pagos
                SET monto_pagado = %s, estado = 'pagado', fecha_pago = NOW()
                WHERE id = %s
            ''', (monto_total, pago_id))
        else:
            cursor.execute('''
                UPDATE pagos
                SET monto_pagado = %s, estado = 'parcial'
                WHERE id = %s
            ''', (nuevo_pagado, pago_id))

        # 6. Verificar si toda la factura está pagada
        cursor.execute('''
            SELECT 
                COUNT(*) AS total_cuotas,
                SUM(CASE WHEN estado = 'pagado' THEN 1 ELSE 0 END) AS cuotas_pagadas
            FROM pagos
            WHERE factura_id = %s
        ''', (factura_id,))
        stats = cursor.fetchone()

        if stats['cuotas_pagadas'] == stats['total_cuotas']:
            cursor.execute('''
                UPDATE facturas
                SET estado = 'pagada', fecha_pagada = NOW()
                WHERE id = %s
            ''', (factura_id,))
            flash('🎉 ¡Factura completamente pagada! Ya puedes descargar el PDF.', 'success')
        else:
            cursor.execute('''
                UPDATE facturas
                SET estado = 'parcial'
                WHERE id = %s
            ''', (factura_id,))
            flash(f'Pago de ${monto_ingresado:.2f} registrado correctamente.', 'success')

        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f'Error al registrar el pago: {e}', 'danger')
    finally:
        if cursor:
            cursor.close()
        conn.close()

    if factura_id:
        return redirect(url_for('ver_factura', id=factura_id))
    return redirect(url_for('facturas_lista'))

# ==================================================================
#               PERFIL DE ESTUDIANTE
# ==================================================================
@app.route('/estudiantes/perfil/<int:id>')
@login_required
def perfil_estudiante(id):
    """Muestra el perfil completo de un estudiante."""
    conn = get_connection()
    if not conn:
        flash('Error de conexión.', 'danger')
        return redirect(url_for('estudiantes_lista'))

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Datos del estudiante
    cursor.execute('SELECT * FROM estudiantes WHERE id = %s', (id,))
    estudiante = cursor.fetchone()

    if not estudiante:
        cursor.close()
        conn.close()
        flash('Estudiante no encontrado.', 'danger')
        return redirect(url_for('estudiantes_lista'))

    # 2. Actividades
    cursor.execute('''
        SELECT id, nombre, descripcion, categoria
        FROM actividades
        WHERE estudiante_id = %s
        ORDER BY id DESC
    ''', (id,))
    actividades = cursor.fetchall()

    # 3. Rendimiento
    cursor.execute('''
        SELECT id, asignatura, nota, fecha, observaciones
        FROM rendimiento
        WHERE estudiante_id = %s
        ORDER BY fecha DESC
    ''', (id,))
    rendimientos = cursor.fetchall()

    promedio = 0.0
    if rendimientos:
        promedio = sum(float(r['nota']) for r in rendimientos) / len(rendimientos)

    # 4. Facturas
    cursor.execute('''
        SELECT id, fecha_emision, total, tipo_pago, num_cuotas, estado
        FROM facturas
        WHERE estudiante_id = %s
        ORDER BY id DESC
    ''', (id,))
    facturas = cursor.fetchall()

    total_facturado = sum(float(f['total']) for f in facturas)

    cursor.close()
    conn.close()

    return render_template(
        'perfil_estudiante.html',
        estudiante=estudiante,
        actividades=actividades,
        rendimientos=rendimientos,
        promedio=promedio,
        facturas=facturas,
        total_facturado=total_facturado
    )


# ------------------ EJECUCIÓN ------------------
if __name__ == '__main__':
    # En local: corre con debug
    # En Render: gunicorn maneja la ejecución (ignora este bloque)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)