from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateTimeLocalField


class ResearchTypeForm(FlaskForm):
    """ Форма создания типа исследования """
    name = StringField("Наименование", validators=[DataRequired()])
    description = TextAreaField("Описание", validators=[DataRequired()])
    submit = SubmitField("Создать")


class ResearchForm(ResearchTypeForm):
    """ Форма создания исследования """
    url = StringField("url", validators=[DataRequired()])
    typeResearch = SelectMultipleField(u'Категория исследования')


class ResearchTypeServiceForm(ResearchTypeForm):
    """ Форма типа сервиса (Юла, Авито)"""
    host = StringField("url", validators=[DataRequired()])


class DeleteResearch(FlaskForm):
    """ Форма для удаления исследования"""
    submit = SubmitField()


class DateTimeForm(FlaskForm):
    """ Форма управления планировщиком """
    dateCrawl = DateTimeLocalField('Start Date:', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Change')



