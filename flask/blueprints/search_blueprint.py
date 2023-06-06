from flask import Blueprint, request, redirect, render_template
from app.forms import SearchForm
from sqlalchemy.sql import text

from app.models import Entity, EntityType

search_bp = Blueprint('search', __name__)


# TODO move query to model
# TODO rewrite queries using best-practice solutions
@search_bp.route('/search', methods=['GET', "POST"])
def search():
    search_query = request.args.get('query')
    filter_list = request.args.getlist('filter')
    if search_query is None:
        search_query = ''
    form = SearchForm()
    if form.validate_on_submit():
        return redirect('/search?query={}'.format(form.search.data))

    entity_types = EntityType.query.all()

    entities_dictionary = {}
    filter_dictionary = {}
    for entity_type in entity_types:
        entities = Entity.query.from_statement(
            text("SELECT * FROM dds.entity "
                 "WHERE entity.entity_type_etid = :entity_type_etid "
                 "AND entity ==> dsl.query_string(:query);")
        ).params(entity_type_etid=entity_type.etid, query=('*' + search_query + '*~')).all()
        entities_list = []
        for e in entities:
            entities_list.append({"entity_name": e.entity_name,
                                  "core_system": dict(e.json_data)['core_system'],
                                  "info": e.info,
                                  "urn": e.urn})
        if len(entities_list) > 0:
            filter_dictionary.update({entity_type.entity_type_displayed_name_plural: {
                "entity_type_name": entity_type.entity_type_name,
                "state": entity_type.entity_type_name in filter_list}})
            if len(filter_list) == 0 or entity_type.entity_type_name in filter_list:
                entities_dictionary.update({entity_type.entity_type_displayed_name_plural: entities_list})

    return render_template('search_result.html', form=form, backlink=request.referrer, search_query=search_query,
                           results=entities_dictionary.items(), filter=filter_dictionary.items())
