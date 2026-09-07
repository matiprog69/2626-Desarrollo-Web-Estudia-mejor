import os
from flask import Flask, render_template, redirect, url_for, flash, request
import sqlite3

# ------------------ CONFIGURACIÓN DE BASE DE DATOS ------------------
DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'estudia_mejor.db')

def get_db_connection():
    """Establece conexión con SQLite y permite acceder a las columnas por nombre."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea todas las tablas si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de actividades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')
    
    # Tabla de estudiantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefono TEXT,
            carrera TEXT NOT NULL,
            direccion TEXT
        )
    ''')
    
    # Tabla de recursos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            cantidad INTEGER NOT NULL
        )
    ''')
    
    # Tabla de rendimiento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rendimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante TEXT NOT NULL,
            asignatura TEXT NOT NULL,
            nota REAL NOT NULL,
            fecha DATE NOT NULL,
            observaciones TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada con todas las tablas.")

# ------------------ APLICACIÓN FLASK ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'clave-secreta-para-desarrollo'

# Inicializar la base de datos al arrancar la app
init_db()

# ------------------ IMPORTAR FORMULARIOS ------------------
from forms.actividad_form import ActividadForm
from forms.estudiante_form import EstudianteForm
from forms.recurso_form import RecursoForm
from forms.rendimiento_form import RendimientoForm

# ------------------ RUTA PRINCIPAL ------------------
@app.route('/')
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

# ------------------ MÓDULO ACTIVIDADES ------------------
@app.route('/actividades', methods=['GET', 'POST'])
def actividades():
    form = ActividadForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO actividades (nombre, descripcion, categoria)
            VALUES (?, ?, ?)
        ''', (form.nombre.data, form.descripcion.data, form.categoria.data))
        conn.commit()
        conn.close()
        flash('Actividad agregada correctamente', 'success')
        return redirect(url_for('actividades'))
    
    conn = get_db_connection()
    lista_actividades = conn.execute('SELECT * FROM actividades ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('actividades.html', form=form, lista_actividades=lista_actividades)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_actividad(id):
    conn = get_db_connection()
    actividad = conn.execute('SELECT * FROM actividades WHERE id = ?', (id,)).fetchone()
    if not actividad:
        flash('Actividad no encontrada', 'danger')
        conn.close()
        return redirect(url_for('actividades'))
    
    form = ActividadForm(data=dict(actividad))
    if form.validate_on_submit():
        conn.execute('''
            UPDATE actividades
            SET nombre = ?, descripcion = ?, categoria = ?
            WHERE id = ?
        ''', (form.nombre.data, form.descripcion.data, form.categoria.data, id))
        conn.commit()
        conn.close()
        flash('Actividad actualizada', 'success')
        return redirect(url_for('actividades'))
    conn.close()
    return render_template('formulario_actividad.html', form=form, accion='Editar')

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_actividad(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM actividades WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Actividad eliminada', 'info')
    return redirect(url_for('actividades'))

# ------------------ MÓDULO ESTUDIANTES (COMPLETO) ------------------

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes_lista():
    form = EstudianteForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO estudiantes (nombre, email, telefono, carrera, direccion)
                VALUES (?, ?, ?, ?, ?)
            ''', (form.nombre.data, form.email.data, form.telefono.data,
                  form.carrera.data, form.direccion.data))
            conn.commit()
            flash('Estudiante agregado correctamente', 'success')
        except sqlite3.IntegrityError as e:
            flash(f'Error: El correo ya está registrado o hay un problema de integridad: {e}', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('estudiantes_lista'))
    
    conn = get_db_connection()
    lista_estudiantes = conn.execute('SELECT * FROM estudiantes ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('estudiantes.html', form=form, lista_estudiantes=lista_estudiantes)


@app.route('/estudiantes/editar/<int:id>', methods=['GET', 'POST'])
def estudiante_editar(id):
    conn = get_db_connection()
    estudiante = conn.execute('SELECT * FROM estudiantes WHERE id = ?', (id,)).fetchone()
    
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        conn.close()
        return redirect(url_for('estudiantes_lista'))
    
    form = EstudianteForm(data=dict(estudiante))
    
    if form.validate_on_submit():
        try:
            conn.execute('''
                UPDATE estudiantes
                SET nombre = ?, email = ?, telefono = ?, carrera = ?, direccion = ?
                WHERE id = ?
            ''', (form.nombre.data, form.email.data, form.telefono.data,
                  form.carrera.data, form.direccion.data, id))
            conn.commit()
            flash('Estudiante actualizado correctamente', 'success')
        except sqlite3.IntegrityError:
            flash('El correo electrónico ya está en uso por otro estudiante', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('estudiantes_lista'))
    
    conn.close()
    return render_template('formulario_estudiante.html', form=form, accion='Editar')


@app.route('/estudiantes/eliminar/<int:id>', methods=['POST'])
def estudiante_eliminar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM estudiantes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Estudiante eliminado correctamente', 'info')
    return redirect(url_for('estudiantes_lista'))
# ------------------ MÓDULO RECURSOS ------------------
@app.route('/recursos', methods=['GET', 'POST'])
def recursos_lista():
    form = RecursoForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO recursos (nombre, tipo, descripcion, cantidad)
            VALUES (?, ?, ?, ?)
        ''', (form.nombre.data, form.tipo.data, form.descripcion.data, form.cantidad.data))
        conn.commit()
        conn.close()
        flash('Recurso agregado correctamente', 'success')
        return redirect(url_for('recursos_lista'))
    
    conn = get_db_connection()
    lista_recursos = conn.execute('SELECT * FROM recursos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('recursos.html', form=form, lista_recursos=lista_recursos)

@app.route('/recursos/editar/<int:id>', methods=['GET', 'POST'])
def recurso_editar(id):
    conn = get_db_connection()
    recurso = conn.execute('SELECT * FROM recursos WHERE id = ?', (id,)).fetchone()
    if not recurso:
        flash('Recurso no encontrado', 'danger')
        conn.close()
        return redirect(url_for('recursos_lista'))
    
    form = RecursoForm(data=dict(recurso))
    if form.validate_on_submit():
        conn.execute('''
            UPDATE recursos
            SET nombre = ?, tipo = ?, descripcion = ?, cantidad = ?
            WHERE id = ?
        ''', (form.nombre.data, form.tipo.data, form.descripcion.data, form.cantidad.data, id))
        conn.commit()
        conn.close()
        flash('Recurso actualizado', 'success')
        return redirect(url_for('recursos_lista'))
    conn.close()
    return render_template('formulario_recurso.html', form=form, accion='Editar')

@app.route('/recursos/eliminar/<int:id>', methods=['POST'])
def recurso_eliminar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM recursos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Recurso eliminado', 'info')
    return redirect(url_for('recursos_lista'))

# ------------------ MÓDULO RENDIMIENTO ------------------
@app.route('/rendimiento', methods=['GET', 'POST'])
def rendimiento_lista():
    form = RendimientoForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO rendimiento (estudiante, asignatura, nota, fecha, observaciones)
            VALUES (?, ?, ?, ?, ?)
        ''', (form.estudiante.data, form.asignatura.data, form.nota.data,
              form.fecha.data, form.observaciones.data))
        conn.commit()
        conn.close()
        flash('Registro de rendimiento agregado', 'success')
        return redirect(url_for('rendimiento_lista'))
    
    conn = get_db_connection()
    lista_rendimientos = conn.execute('SELECT * FROM rendimiento ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('rendimiento.html', form=form, lista_rendimientos=lista_rendimientos)

@app.route('/rendimiento/editar/<int:id>', methods=['GET', 'POST'])
def rendimiento_editar(id):
    conn = get_db_connection()
    rend = conn.execute('SELECT * FROM rendimiento WHERE id = ?', (id,)).fetchone()
    if not rend:
        flash('Registro no encontrado', 'danger')
        conn.close()
        return redirect(url_for('rendimiento_lista'))
    
    form = RendimientoForm(data=dict(rend))
    if form.validate_on_submit():
        conn.execute('''
            UPDATE rendimiento
            SET estudiante = ?, asignatura = ?, nota = ?, fecha = ?, observaciones = ?
            WHERE id = ?
        ''', (form.estudiante.data, form.asignatura.data, form.nota.data,
              form.fecha.data, form.observaciones.data, id))
        conn.commit()
        conn.close()
        flash('Registro actualizado', 'success')
        return redirect(url_for('rendimiento_lista'))
    conn.close()
    return render_template('formulario_rendimiento.html', form=form, accion='Editar')

@app.route('/rendimiento/eliminar/<int:id>', methods=['POST'])
def rendimiento_eliminar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM rendimiento WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Registro eliminado', 'info')
    return redirect(url_for('rendimiento_lista'))

# ------------------ EJECUCIÓN ------------------
if __name__ == '__main__':
    app.run(debug=True)