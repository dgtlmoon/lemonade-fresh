#!/usr/bin/python3
from wtforms import Form
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Email, ValidationError


class validateHuman(object):
    """
       Flask wtform validators wont work with basic auth
    """

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if str(field.data).lower() != "lemon":
            message = field.gettext('Wrong guess!')
            raise ValidationError(message)


class StartForm(Form):
    email = StringField("Your Email Address",
                        validators=[InputRequired("Please enter your email address."),
                                    Email("This field requires a valid email address")])
    antispam = StringField("Are you a robot?",
                           validators=[InputRequired("Please enter a valid guess."), validateHuman()])
    submit = SubmitField("Let's Go!")

class ContactForm(Form):
    email = StringField("Your Email Address",
                        validators=[InputRequired("Please enter your email address."),
                                    Email("This field requires a valid email address")])
    antispam = StringField("Are you a robot?",
                           validators=[InputRequired("Please enter a valid guess."), validateHuman()])
    body = TextAreaField("Tell us more",
                        validators=[InputRequired("Please enter your email address.")])
    submit = SubmitField("Send")
