from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, Optional

class EstudianteForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=100, message='Mínimo 3, máximo 100 caracteres')
    ])
    email = EmailField('Correo electrónico', validators=[
        DataRequired(message='El correo es obligatorio'),
        Email(message='Ingrese un correo válido')
    ])
    telefono = TelField('Teléfono', validators=[
        Optional(),
        Length(max=20, message='Máximo 20 caracteres')
    ])
    carrera = SelectField('Carrera', choices=[
        ('', 'Selecciona una carrera'),
        ('Tecnologías de la Información', 'Tecnologías de la Información'),
        ('Administración', 'Administración'),
        ('Contabilidad', 'Contabilidad'),
        ('Otro', 'Otro')
    ], validators=[
        DataRequired(message='Debes seleccionar una carrera')
    ])
    direccion = TextAreaField('Dirección', validators=[
        Optional(),
        Length(max=150, message='Máximo 150 caracteres')
    ])