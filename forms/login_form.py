from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    """Formulario para iniciar sesión."""

    usuario = StringField(
        'Usuario',
        validators=[
            DataRequired(message='El nombre de usuario es obligatorio.'),
            Length(min=3, max=50, message='El usuario debe tener entre 3 y 50 caracteres.')
        ]
    )

    password = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='La contraseña es obligatoria.'),
            Length(min=6, max=100, message='La contraseña debe tener al menos 6 caracteres.')
        ]
    )

    submit = SubmitField('Iniciar sesión')