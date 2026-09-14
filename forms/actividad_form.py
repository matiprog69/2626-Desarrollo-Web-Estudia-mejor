from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

class ActividadForm(FlaskForm):
    nombre = StringField('Nombre de la actividad', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=80, message='Debe tener entre 3 y 80 caracteres')
    ])
    descripcion = TextAreaField('Descripción', validators=[
        DataRequired(message='La descripción es obligatoria'),
        Length(max=200, message='Máximo 200 caracteres')
    ])
    categoria = SelectField('Categoría', choices=[
        ('', 'Selecciona una categoría'),
        ('Estudio', 'Estudio'),
        ('Tarea', 'Tarea'),
        ('Examen', 'Examen'),
        ('Proyecto', 'Proyecto'),
        ('Otro', 'Otro')
    ], validators=[
        DataRequired(message='Debes seleccionar una categoría')
    ])
    
    # NUEVO CAMPO: Relación con la tabla estudiantes
    # El coerce=int es vital para que el id se envíe como número
    estudiante_id = SelectField('Estudiante Asignado', coerce=int, validators=[
        DataRequired(message='Debes seleccionar un estudiante')
    ])