from flask_wtf import FlaskForm
from wtforms import SelectField, RadioField, SubmitField
from wtforms.validators import DataRequired


class FacturaForm(FlaskForm):
    """Formulario para emitir una nueva factura."""

    estudiante_id = SelectField(
        'Estudiante',
        coerce=int,
        validators=[DataRequired(message='Debes seleccionar un estudiante.')]
    )

    tipo_pago = RadioField(
        'Tipo de pago',
        choices=[
            ('contado', 'Contado (1 solo pago)'),
            ('cuotas', 'Cuotas')
        ],
        default='contado',
        validators=[DataRequired(message='Selecciona un tipo de pago.')]
    )

    num_cuotas = SelectField(
        'Número de cuotas',
        choices=[
            (2, '2 cuotas'),
            (3, '3 cuotas'),
            (6, '6 cuotas'),
            (12, '12 cuotas')
        ],
        coerce=int,
        default=2
    )

    submit = SubmitField('Emitir factura')