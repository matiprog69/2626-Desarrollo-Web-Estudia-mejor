from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class PagoForm(FlaskForm):
    """Formulario para registrar un pago parcial o total de una cuota."""

    monto = DecimalField(
        'Monto a pagar (USD)',
        places=2,
        validators=[
            DataRequired(message='El monto es obligatorio.'),
            NumberRange(min=0.01, max=99999.99, message='El monto debe ser mayor a 0.')
        ]
    )

    metodo_pago = SelectField(
        'Método de pago',
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia bancaria'),
            ('tarjeta', 'Tarjeta de crédito/débito'),
            ('otro', 'Otro')
        ],
        validators=[DataRequired(message='Selecciona un método de pago.')]
    )

    submit = SubmitField('Registrar pago')