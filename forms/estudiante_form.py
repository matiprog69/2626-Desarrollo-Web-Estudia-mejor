from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Optional

class EstudianteForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=100)
    ])
    email = EmailField('Correo electrónico', validators=[
        DataRequired(message='El correo es obligatorio'),
        Email(message='Ingrese un correo válido')
    ])
    telefono = TelField('Teléfono', validators=[
        Optional(),
        Length(max=20)
    ])
    carrera = SelectField('Carrera', choices=[
        ('', 'Selecciona una carrera'),
        ('Tecnologías de la Información', 'Tecnologías de la Información'),
        ('Administración', 'Administración'),
        ('Diseño Gráfico', 'Diseño Gráfico'),
        ('Otra', 'Otra')
    ], validators=[
        DataRequired(message='Debes seleccionar una carrera')
    ])
    direccion = TextAreaField('Dirección', validators=[
        Optional(),
        Length(max=150)
    ])