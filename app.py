from flask import Flask, render_template

app = Flask(__name__)

# Página principal
@app.route('/')
def inicio():
    return render_template('index.html')


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