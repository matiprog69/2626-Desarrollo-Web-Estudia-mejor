from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ServicioForm(FlaskForm):
    """Formulario para crear/editar categorías de servicios."""

    nombre = StringField(
        'Nombre de la categoría',
        validators=[
            DataRequired(message='El nombre es obligatorio.'),
            Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres.')
        ]
    )

    descripcion = TextAreaField(
        'Descripción',
        validators=[
            Optional(),
            Length(max=500, message='La descripción no puede exceder los 500 caracteres.')
        ]
    )

    icono = StringField(
        'Ícono (opcional)',
        validators=[
            Optional(),
            Length(max=50, message='El ícono no puede exceder los 50 caracteres.')
        ]
    )

    activo = BooleanField(
        '¿Activo?',
        default=True
    )

    submit = SubmitField('Guardar')