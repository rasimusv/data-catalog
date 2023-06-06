from flask import Blueprint, request, redirect, render_template, json
from app.forms import SearchForm

from app.models import Entity, Relation

# TODO rename bp
lineage_card_bp = Blueprint('lineage_card', __name__)


# TODO rewrite queries using best-practice solutions
# TODO refactor to js script
def read_recursive(urn, entity_name, core_system, info, children):
    return {'innerHTML': f"""<a href="/infocards/{urn}">
                        <div class="d-flex card-title mb-1 justify-content-between">
                            <h5>{entity_name}</h5>
                            <small class="text-muted">{core_system}</small>
                        </div>
                        <p class="card-subtitle mb-1">{info}</p>
                        <small class="card-text text-muted">{urn}</small></a>""",
            'children': [
                read_recursive(urn=child['urn'], entity_name=child['entity_name'], core_system=child['core_system'],
                               info=child['info'], children=child['children']) for child in children]}


@lineage_card_bp.route('/lineage/<rid>', methods=['GET', "POST"])
def infocards(rid):
    form = SearchForm()
    if form.validate_on_submit():
        return redirect('/search?query={}'.format(form.search.data))

    relation = Relation.query.filter(Relation.rid == rid).first_or_404()
    s = relation.source_entity

    static_metadata = {'what': 'Data Lineage',
                       'core_system': relation.attribute_entity.json_data['core_system'],
                       'source': s.entity_name_short,
                       'last_time': relation.processed_dttm}

    s_parent = Relation.query.filter(Relation.destination_entity == s).all()
    attributes = Relation.query.filter(Relation.source_entity == s).all()

    hierarchy = {'urn': s.urn,
                 'entity_name': s.entity_name,
                 'core_system': s.json_data['core_system'],
                 'info': s.info,
                 'children': [
                     {'urn': a.attribute_entity.urn,
                      'entity_name': a.attribute_entity.entity_name,
                      'core_system': a.attribute_entity.json_data['core_system'],
                      'info': a.attribute_entity.info,
                      'children': [
                          {'urn': d.urn,
                           'entity_name': d.entity_name,
                           'core_system': d.json_data['core_system'],
                           'info': d.info,
                           'children': [
                               {'urn': da.urn,
                                'entity_name': da.entity_name,
                                'core_system': da.json_data['core_system'],
                                'info': da.info,
                                'children': [
                                    {'urn': dd.urn,
                                     'entity_name': dd.entity_name,
                                     'core_system': dd.json_data['core_system'],
                                     'info': dd.info,
                                     'children': []} for dd in Entity.destination_destinations(source_eid=d.eid,
                                                                                               attribute_eid=da.eid)]}
                               for da in Entity.destination_attributes(source_eid=d.eid)]}
                          for d in Entity.destinations(source_eid=s.eid, attribute_eid=a.attribute_entity.eid)]} for a
                     in attributes]}

    if len(s_parent) == 1:
        ss = s_parent.source_entity
        sa = s_parent.attribute_entity

        hierarchy = {'urn': ss.urn,
                     'entity_name': ss.entity_name,
                     'core_system': ss.json_data['core_system'],
                     'info': ss.info,
                     'children': [
                         {'urn': sa.urn,
                          'entity_name': sa.entity_name,
                          'core_system': sa.json_data['core_system'],
                          'info': sa.info,
                          'children': [hierarchy]}]}

    rendered_hierarchy = read_recursive(urn=hierarchy['urn'], entity_name=hierarchy['entity_name'],
                                        core_system=hierarchy['core_system'], info=hierarchy['info'],
                                        children=hierarchy['children'])

    return render_template('lineage_card.html', form=form, backlink=request.referrer, data=static_metadata,
                           hierarchy=rendered_hierarchy)
