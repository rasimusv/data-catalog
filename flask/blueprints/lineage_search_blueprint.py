from flask import Blueprint, request, redirect, render_template
from app.forms import SearchForm
from sqlalchemy.sql import text

from app.models import Entity, EntityType, Relation

lineage_search_bp = Blueprint('lineage_search', __name__)


# TODO move query to model
# TODO rewrite queries using best-practice solutions

@lineage_search_bp.route('/lineage', methods=['GET', "POST"])
def search():
    search_query = request.args.get('query')
    if search_query is None:
        search_query = ''
    form = SearchForm()
    if form.validate_on_submit():
        return redirect('/lineage?query={}'.format(form.search.data))

    entity_types = EntityType.query.filter(
        EntityType.entity_type_name.not_in(['cluster', 'instance', 'cloud', 'geo-scope'])).all()
    prepared_relations = []
    for entity_type in entity_types:
        entities = Entity.query.from_statement(text("SELECT * FROM dds.entity WHERE eid IN ("
                                                    "(SELECT source FROM dds.relation) UNION ALL "
                                                    "(SELECT destination FROM dds.relation) UNION ALL "
                                                    "(SELECT attribute FROM dds.relation)) "
                                                    "AND entity_type_etid = :entity_type_etid AND entity ==> dsl.query_string(:query)")).params(
            entity_type_etid=entity_type.etid,
            query=('*' + search_query + '*~')).all()
        for entity in entities:
            relations = Relation.query.filter(
                (Relation.attribute_entity == entity) | (Relation.source_entity == entity) | (
                            Relation.destination_entity == entity)).all()

            prepared_relations += [{"rid": relation.rid,
                                    "relation": relation.source_entity.entity_name_short + ' -> ' + relation.attribute_entity.entity_name_short + ' -> ' + relation.destination_entity.entity_name_short,
                                    "core_system": dict(relation.attribute_entity.json_data)['core_system'],
                                    "last_time": relation.processed_dttm} for relation in relations]

    return render_template('lineage_search_result.html', form=form, backlink=request.referrer,
                           search_query=search_query,
                           results=prepared_relations)
