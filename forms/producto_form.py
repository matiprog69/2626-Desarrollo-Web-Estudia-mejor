from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    DecimalField,
    SelectField,
    BooleanField,
    SubmitField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProductoForm(FlaskForm):
    """Formulario para crear/editar productos dentro de una categoría."""

    servicio_id = SelectField(
        'Categoría',
        coerce=int,
        validators=[DataRequired(message='Debes seleccionar una categoría.')]
    )

    nombre = StringField(
        'Nombre del producto',
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

    precio = DecimalField(
        'Precio (USD)',
        places=2,
        validators=[
            DataRequired(message='El precio es obligatorio.'),
            NumberRange(min=0.01, max=99999.99, message='El precio debe estar entre 0.01 y 99999.99.')
        ]
    )

    duracion = StringField(
        'Duración (opcional)',
        validators=[
            Optional(),
            Length(max=50, message='La duración no puede exceder los 50 caracteres.')
        ]
    )

    modalidad = StringField(
        'Modalidad (opcional)',
        validators=[
            Optional(),
            Length(max=50, message='La modalidad no puede exceder los 50 caracteres.')
        ]
    )

    imagen = StringField(
        'URL de la imagen (opcional)',
        validators=[
            Optional(),
            Length(max=500, message='La URL no puede exceder los 500 caracteres.')
        ]
    )

    activo = BooleanField(
        '¿Activo?',
        default=True
    )

    submit = SubmitField('Guardar')