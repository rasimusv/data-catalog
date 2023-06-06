from flask import Blueprint, request, redirect, render_template
from app.forms import SearchForm

from app.models import Entity, EntityType, Relation

metadata_bp = Blueprint('metadata', __name__)


# TODO rewrite queries using best-practice solutions
@metadata_bp.route('/infocards/<urn>', methods=['GET', "POST"])
def infocards(urn):
    urn = urn if urn is not None else ''
    form = SearchForm()
    if form.validate_on_submit():
        return redirect('/search?query={}'.format(form.search.data))

    entity = Entity.query.filter(Entity.urn == urn).first_or_404()

    children_dictionary = {}
    if entity.children is not None:
        entity_types = EntityType.query.all()
        for children_type in entity_types:
            children = Entity.query.filter(Entity.entity_type == children_type, Entity.parent == entity).all()
            children_list = [{"entity_name": child.entity_name,
                              "core_system": dict(child.json_data)['core_system'],
                              "info": child.info,
                              "urn": child.urn} for child in children]
            if len(children) > 0:
                children_dictionary.update({children_type.entity_type_displayed_name_plural: children_list})

    relations = Relation.query.filter((Relation.attribute_entity == entity) | (Relation.source_entity == entity) | (Relation.destination_entity == entity)).all()

    prepared_relations = [{"rid": relation.rid,
                           "relation": relation.source_entity.entity_name_short + ' -> ' + relation.attribute_entity.entity_name_short + ' -> ' + relation.destination_entity.entity_name_short,
                           "core_system": dict(relation.attribute_entity.json_data)['core_system'],
                           "last_time": relation.processed_dttm} for relation in relations]

    codes = []
    if entity.codes is not None:
        codes_dicts = [dict(value) for value in dict(entity.codes)['codes']]
        for code in codes_dicts:
            codes.append({'code_name': code['code_name'],
                          'code_block': code['code_block'],
                          'code_style': ('highlight-' + code['code_language'].lower()) if code[
                              'highlight'] else 'nohighlight'})

    static_metadata = {"entity_type": entity.entity_type.entity_type_displayed_name,
                       "entity_name": entity.entity_name,
                       "entity_name_short": entity.entity_name_short,
                       "info": entity.info,
                       "parent_entity_type": entity.parent.entity_type.entity_type_displayed_name if entity.parent is not None else None,
                       "parent_entity_name": entity.parent.entity_name if entity.parent is not None else None,
                       "parent_core_system": dict(entity.parent.json_data)[
                           "core_system"] if entity.parent is not None else None,
                       "parent_info": entity.parent.info if entity.parent is not None else None,
                       "parent_urn": entity.parent.urn if entity.parent is not None else None}

    if entity.tags:
        tags = ", ".join(str(tag) for tag in entity.tags)

    return render_template('metadata_card.html', form=form, backlink=request.referrer, data=static_metadata,
                           children=children_dictionary.items(), ui_data=dict(entity.json_data_ui).items(),
                           codes=codes, tags=tags, relations=prepared_relations)
