from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from datetime import date

class RendimientoForm(FlaskForm):
    estudiante = StringField('Nombre del estudiante', validators=[
        DataRequired(message='El nombre es obligatorio'),
        Length(min=3, max=100)
    ])
    asignatura = StringField('Asignatura', validators=[
        DataRequired(message='La asignatura es obligatoria'),
        Length(min=3, max=80)
    ])
    nota = FloatField('Nota', validators=[
        DataRequired(message='La nota es obligatoria'),
        NumberRange(min=0, max=10)
    ])
    fecha = DateField('Fecha de evaluación', validators=[
        DataRequired(message='La fecha es obligatoria')
    ], default=date.today)
    observaciones = TextAreaField('Observaciones', validators=[
        Optional(),
        Length(max=200)
    ])
