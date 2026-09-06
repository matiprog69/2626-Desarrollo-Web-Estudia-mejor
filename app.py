from flask import Flask, render_template

app = Flask(__name__)

# Página principal
@app.route('/')
def inicio():

    mensaje = "Bienvenido al Sistema de Gestión Académica"

    actividades = [
        {
            "nombre": "Proyecto Flask",
            "estado": True
        },
        {
            "nombre": "Examen de Base de Datos",
            "estado": False
        },
        {
            "nombre": "Tarea de Programación",
            "estado": True
        }
    ]

    estudiante = {
        "nombre": "Fernando Matías Sarango",
        "carrera": "Tecnologías de la Información"
    }

    return render_template(
        'index.html',
        mensaje=mensaje,
        actividades=actividades,
        estudiante=estudiante
    )

# Módulo Actividades
@app.route('/actividades')
def actividades():
    return render_template('actividades.html')

# Módulo Recursos
@app.route('/recursos')
def recursos():
    return render_template('recursos.html')

# Módulo Estudiantes
@app.route('/estudiantes')
def estudiantes():
    return render_template('estudiantes.html')

# Módulo Rendimiento
@app.route('/rendimiento')
def rendimiento():
    return render_template('rendimiento.html')

if __name__ == '__main__':
    app.run(debug=True)