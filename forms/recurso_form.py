from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class RecursoForm(FlaskForm):
    nombre = StringField('Nombre del recurso', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=80)
    ])
    tipo = SelectField('Tipo de recurso', choices=[
        ('', 'Selecciona un tipo'),
        ('Libro', 'Libro'),
        ('Video', 'Video'),
        ('Artículo', 'Artículo'),
        ('Software', 'Software'),
        ('Otro', 'Otro')
    ], validators=[DataRequired(message='Debes seleccionar un tipo')])
    descripcion = TextAreaField('Descripción', validators=[
        Optional(),
        Length(max=200)
    ])
    cantidad = IntegerField('Cantidad disponible', validators=[
        DataRequired(message='La cantidad es obligatoria'),
        NumberRange(min=0)
    ])