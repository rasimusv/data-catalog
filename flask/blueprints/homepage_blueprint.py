from flask import Blueprint, render_template, flash, redirect
from app.forms import SearchForm

homepage_bp = Blueprint('home', __name__)


@homepage_bp.route('/', methods=['GET', 'POST'])
@homepage_bp.route('/index', methods=['GET', 'POST'])
@homepage_bp.route('/home', methods=['GET', 'POST'])
@homepage_bp.route('/homepage', methods=['GET', 'POST'])
def home():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect('/search?query={}'.format(form.search.data))
    return render_template('home.html', form=form)
