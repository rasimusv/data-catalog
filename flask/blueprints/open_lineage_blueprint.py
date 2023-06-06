from flask import Blueprint, request, redirect, render_template, abort, jsonify
from app.models import Entity, EntityType, Relation

ol_bp = Blueprint('openlineage', __name__)


def url_to_urn(namespace, name):
    return namespace.replace('.', '-').replace('://', '.').split(':')[0] + '.' + name


def urn_with_producer(namespace, producer, name):
    return namespace + ('.airflow.etl.' if producer == 'https://github.com/OpenLineage/OpenLineage/tree/0.26.0/integration/airflow' else '.') + name.split('.')[0]


# TODO rewrite queries using best-practice solutions
@ol_bp.route('/api/v1/lineage', methods=["POST"])
def lineage():
    if not request.json:
        abort(400)

    if request.json['eventType'] == 'COMPLETE' and len(request.json['inputs']) > 0:
        processed_dttm = request.json['eventTime']
        sources = [url_to_urn(inpt['namespace'], inpt['name']) for inpt in request.json['inputs']]
        destinations = [url_to_urn(otpt['namespace'], otpt['name']) for otpt in request.json['outputs'] if
                        url_to_urn(otpt['namespace'], otpt['name']) not in sources]
        attribute_urn = urn_with_producer(namespace=request.json['job']['namespace'], producer=request.json['producer'],
                                          name=request.json['job']['name'])

        if len(destinations) > 0:
            producer = Entity.query.filter(Entity.urn == 'datacatalog.openlineage_backend').first_or_404()
            entity_type = EntityType.query.filter(EntityType.entity_type_name == 'table').first_or_404()
            attribute_entity = Entity.query.filter(Entity.urn == attribute_urn).first_or_404()
            for source_urn in sources:
                Entity.insert_on_conflict_do_nothing_by_urn(loaded_by_eid=producer.eid,
                                                            entity_type_etid=entity_type.etid,
                                                            urn=source_urn)
                source_table = Entity.query.filter(Entity.urn == source_urn).first_or_404()
                for destination_urn in destinations:
                    Entity.insert_on_conflict_do_nothing_by_urn(loaded_by_eid=producer.eid,
                                                                entity_type_etid=entity_type.etid,
                                                                urn=destination_urn)
                    destination_table = Entity.query.filter(Entity.urn == destination_urn).first_or_404()
                    Relation.insert_on_conflict_do_update(loaded_by_eid=producer.eid,
                                                          processed_dttm=processed_dttm,
                                                          source=source_table.eid,
                                                          destination=destination_table.eid,
                                                          attribute=attribute_entity.eid)
    return jsonify(success=True), 200
