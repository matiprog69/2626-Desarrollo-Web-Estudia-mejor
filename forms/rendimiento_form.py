from flask_wtf import FlaskForm
from wtforms import (
    SelectField, DecimalField, DateField,
    TextAreaField, SubmitField, StringField
)
from wtforms.validators import DataRequired, NumberRange, Optional


class RendimientoForm(FlaskForm):
    """Formulario para registrar el rendimiento académico."""

    estudiante_id = SelectField(
        'Estudiante',
        coerce=int,
        validators=[DataRequired(message='Debes seleccionar un estudiante.')]
    )

    asignatura = StringField(
        'Asignatura',
        validators=[DataRequired(message='La asignatura es obligatoria.')]
    )

    nota = DecimalField(
        'Nota (0-20)',
        places=2,
        validators=[
            DataRequired(message='La nota es obligatoria.'),
            NumberRange(min=0, max=20, message='La nota debe estar entre 0 y 20.')
        ]
    )

    fecha = DateField(
        'Fecha',
        validators=[DataRequired(message='La fecha es obligatoria.')]
    )

    observaciones = TextAreaField(
        'Observaciones',
        validators=[Optional()]
    )

    submit = SubmitField('Guardar')