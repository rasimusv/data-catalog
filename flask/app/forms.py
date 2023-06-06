from flask_wtf import FlaskForm
from wtforms import SubmitField, SearchField


class SearchForm(FlaskForm):
    search = SearchField('Поиск')
    submit = SubmitField('Search')
