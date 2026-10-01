from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import DataRequired, NumberRange, Optional, Length


class RecursoForm(FlaskForm):
    """Formulario para crear/editar recursos."""

    nombre = StringField(
        'Nombre del recurso',
        validators=[
            DataRequired(message='El nombre es obligatorio.'),
            Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres.')
        ]
    )

    tipo = StringField(
        'Tipo',
        validators=[
            DataRequired(message='El tipo es obligatorio.'),
            Length(max=50)
        ]
    )

    descripcion = TextAreaField(
        'Descripción',
        validators=[Optional(), Length(max=500)]
    )

    cantidad = IntegerField(
        'Cantidad',
        validators=[
            DataRequired(message='La cantidad es obligatoria.'),
            NumberRange(min=0, message='La cantidad debe ser mayor o igual a 0.')
        ]
    )

    servicio_id = SelectField(
        'Servicio asociado (opcional)',
        coerce=int,
        validators=[Optional()]
    )

    submit = SubmitField('Guardar')