import os
from flask import Flask, render_template, redirect, url_for, flash, request
from forms.actividad_form import ActividadForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'clave-secreta-para-desarrollo'

# Datos en memoria (para el CRUD)
actividades_crud = []
id_counter = 1

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

@app.route('/actividades', methods=['GET', 'POST'])
def actividades():
    global id_counter
    form = ActividadForm()
    
    if form.validate_on_submit():
        nueva = {
            'id': id_counter,
            'nombre': form.nombre.data,
            'descripcion': form.descripcion.data,
            'categoria': form.categoria.data
        }
        actividades_crud.append(nueva)
        id_counter += 1
        flash('Actividad agregada correctamente', 'success')
        return redirect(url_for('actividades'))
    
    return render_template('actividades.html', form=form, lista_actividades=actividades_crud)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_actividad(id):
    actividad = next((a for a in actividades_crud if a['id'] == id), None)
    if not actividad:
        flash('Actividad no encontrada', 'danger')
        return redirect(url_for('actividades'))
    
    form = ActividadForm(data=actividad)
    if form.validate_on_submit():
        actividad['nombre'] = form.nombre.data
        actividad['descripcion'] = form.descripcion.data
        actividad['categoria'] = form.categoria.data
        flash('Actividad actualizada correctamente', 'success')
        return redirect(url_for('actividades'))
    
    return render_template('formulario_actividad.html', form=form, accion='Editar')

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_actividad(id):
    global actividades_crud
    actividades_crud = [a for a in actividades_crud if a['id'] != id]
    flash('Actividad eliminada', 'info')
    return redirect(url_for('actividades'))


# Módulo Recursos
from forms import RecursoForm

recursos = []
id_recurso = 1

@app.route('/recursos', methods=['GET', 'POST'])
def recursos_lista():
    global id_recurso
    form = RecursoForm()
    if form.validate_on_submit():
        nuevo = {
            'id': id_recurso,
            'titulo': form.titulo.data,
            'tipo': form.tipo.data,
            'enlace': form.enlace.data,
            'descripcion': form.descripcion.data
        }
        recursos.append(nuevo)
        id_recurso += 1
        flash('Recurso agregado correctamente', 'success')
        return redirect(url_for('recursos_lista'))
    return render_template('recursos.html', form=form, lista_recursos=recursos)

@app.route('/recursos/editar/<int:id>', methods=['GET', 'POST'])
def recurso_editar(id):
    recurso = next((r for r in recursos if r['id'] == id), None)
    if not recurso:
        flash('Recurso no encontrado', 'danger')
        return redirect(url_for('recursos_lista'))
    form = RecursoForm(data=recurso)
    if form.validate_on_submit():
        recurso.update({
            'titulo': form.titulo.data,
            'tipo': form.tipo.data,
            'enlace': form.enlace.data,
            'descripcion': form.descripcion.data
        })
        flash('Recurso actualizado', 'success')
        return redirect(url_for('recursos_lista'))
    return render_template('formulario_recurso.html', form=form, accion='Editar')

@app.route('/recursos/eliminar/<int:id>', methods=['POST'])
def recurso_eliminar(id):
    global recursos
    recursos = [r for r in recursos if r['id'] != id]
    flash('Recurso eliminado', 'info')
    return redirect(url_for('recursos_lista'))

# Módulo Estudiantes
from forms import EstudianteForm

estudiantes = []
id_estudiante = 1

@app.route('/estudiantes', methods=['GET', 'POST'])
def estudiantes_lista():
    global id_estudiante
    form = EstudianteForm()
    if form.validate_on_submit():
        nuevo = {
            'id': id_estudiante,
            'nombre': form.nombre.data,
            'email': form.email.data,
            'telefono': form.telefono.data,
            'carrera': form.carrera.data,
            'direccion': form.direccion.data
        }
        estudiantes.append(nuevo)
        id_estudiante += 1
        flash('Estudiante agregado correctamente', 'success')
        return redirect(url_for('estudiantes_lista'))
    return render_template('estudiantes.html', form=form, lista_estudiantes=estudiantes)

@app.route('/estudiantes/editar/<int:id>', methods=['GET', 'POST'])
def estudiante_editar(id):
    estudiante = next((e for e in estudiantes if e['id'] == id), None)
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('estudiantes_lista'))
    form = EstudianteForm(data=estudiante)
    if form.validate_on_submit():
        estudiante.update({
            'nombre': form.nombre.data,
            'email': form.email.data,
            'telefono': form.telefono.data,
            'carrera': form.carrera.data,
            'direccion': form.direccion.data
        })
        flash('Estudiante actualizado', 'success')
        return redirect(url_for('estudiantes_lista'))
    return render_template('formulario_estudiante.html', form=form, accion='Editar')

@app.route('/estudiantes/eliminar/<int:id>', methods=['POST'])
def estudiante_eliminar(id):
    global estudiantes
    estudiantes = [e for e in estudiantes if e['id'] != id]
    flash('Estudiante eliminado', 'info')
    return redirect(url_for('estudiantes_lista'))

# Módulo Rendimiento
from forms import RendimientoForm

rendimientos = []
id_rendimiento = 1

@app.route('/rendimiento', methods=['GET', 'POST'])
def rendimiento_lista():
    global id_rendimiento
    form = RendimientoForm()
    if form.validate_on_submit():
        nuevo = {
            'id': id_rendimiento,
            'estudiante': form.estudiante.data,
            'materia': form.materia.data,
            'nota': form.nota.data,
            'fecha': form.fecha.data,
            'observaciones': form.observaciones.data
        }
        rendimientos.append(nuevo)
        id_rendimiento += 1
        flash('Registro de rendimiento agregado', 'success')
        return redirect(url_for('rendimiento_lista'))
    return render_template('rendimiento.html', form=form, lista_rendimientos=rendimientos)

@app.route('/rendimiento/editar/<int:id>', methods=['GET', 'POST'])
def rendimiento_editar(id):
    rend = next((r for r in rendimientos if r['id'] == id), None)
    if not rend:
        flash('Registro no encontrado', 'danger')
        return redirect(url_for('rendimiento_lista'))
    form = RendimientoForm(data=rend)
    if form.validate_on_submit():
        rend.update({
            'estudiante': form.estudiante.data,
            'materia': form.materia.data,
            'nota': form.nota.data,
            'fecha': form.fecha.data,
            'observaciones': form.observaciones.data
        })
        flash('Registro actualizado', 'success')
        return redirect(url_for('rendimiento_lista'))
    return render_template('formulario_rendimiento.html', form=form, accion='Editar')

@app.route('/rendimiento/eliminar/<int:id>', methods=['POST'])
def rendimiento_eliminar(id):
    global rendimientos
    rendimientos = [r for r in rendimientos if r['id'] != id]
    flash('Registro eliminado', 'info')
    return redirect(url_for('rendimiento_lista'))

if __name__ == '__main__':
    app.run(debug=True)