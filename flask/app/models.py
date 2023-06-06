from app import db
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, insert
from sqlalchemy.sql import text


# TODO delete unusable
# TODO refactor schema (engine_type, entity_types.lineage, entity_types.cluster)
class EntityType(db.Model):
    __tablename__ = 'entity_types'
    __table_args__ = {'schema': 'dds'}
    etid = db.Column('etid', db.BigInteger, primary_key=True)
    entity_type_name = db.Column('entity_type_name', db.String, unique=True)
    entity_type_displayed_name = db.Column('entity_type_displayed_name', db.String)
    entity_type_displayed_name_plural = db.Column('entity_type_displayed_name_plural', db.String)
    entities = db.relationship('Entity', back_populates='entity_type', lazy='dynamic', innerjoin=True)


class Relation(db.Model):
    __tablename__ = 'relation'
    __table_args__ = {'schema': 'dds'}
    rid = db.Column('rid', db.BigInteger, primary_key=True)
    loaded_by_eid = db.Column('loaded_by_eid', db.BigInteger,
                              db.ForeignKey('dds.entity.eid', ondelete='CASCADE', onupdate='CASCADE'))
    processed_dttm = db.Column('processed_dttm', db.TIMESTAMP, server_default=db.func.now())
    source = db.Column('source', db.BigInteger,
                       db.ForeignKey('dds.entity.eid', ondelete='CASCADE', onupdate='CASCADE'))
    destination = db.Column('destination', db.BigInteger,
                            db.ForeignKey('dds.entity.eid', ondelete='CASCADE', onupdate='CASCADE'))
    attribute = db.Column('attribute', db.BigInteger,
                          db.ForeignKey('dds.entity.eid', ondelete='CASCADE', onupdate='CASCADE'))
    loaded_by = db.relationship('Entity', foreign_keys=[loaded_by_eid], back_populates='relations_loaded_by_me',
                                innerjoin=True)
    source_entity = db.relationship('Entity', foreign_keys=[source], back_populates='relation_source',
                                    innerjoin=True)
    destination_entity = db.relationship('Entity', foreign_keys=[destination],
                                         back_populates='relation_destination',
                                         innerjoin=True)
    attribute_entity = db.relationship('Entity', foreign_keys=[attribute], back_populates='relation_attribute',
                                       innerjoin=True)

    @staticmethod
    def insert_on_conflict_do_nothing(**kwargs):
        db.session.execute(insert(Relation).values(kwargs).on_conflict_do_nothing(
            index_elements=['source', 'destination', 'attribute']))
        db.session.commit()

    @staticmethod
    def insert_on_conflict_do_update(**kwargs):
        db.session.execute(insert(Relation).values(kwargs).on_conflict_do_update(
            index_elements=['source', 'destination', 'attribute'], set_=kwargs))
        db.session.commit()


class Entity(db.Model):
    __tablename__ = 'entity'
    __table_args__ = {'schema': 'dds'}
    eid = db.Column('eid', db.BigInteger, primary_key=True)
    entity_type_etid = db.Column('entity_type_etid', db.BigInteger,
                                 db.ForeignKey('dds.entity_types.etid', ondelete='CASCADE', onupdate='CASCADE'),
                                 nullable=False)
    parent_eid = db.Column('parent_eid', db.BigInteger,
                           db.ForeignKey('dds.entity.eid', ondelete='CASCADE', onupdate='CASCADE'))
    loaded_by_eid = db.Column('loaded_by_eid', db.BigInteger,
                              db.ForeignKey('dds.entity.eid', ondelete='CASCADE', onupdate='CASCADE'))
    processed_ts = db.Column('processed_ts', db.TIMESTAMP, server_default=db.func.now())
    urn = db.Column('urn', db.String, unique=True, nullable=False)
    entity_name = db.Column('entity_name', db.String, nullable=False)
    entity_name_short = db.Column('entity_name_short', db.String, nullable=False)
    info = db.Column('info', db.String)
    search_data = db.Column('search_data', db.String)
    json_data = db.Column('json_data', JSONB)
    json_data_ui = db.Column('json_data_ui', JSONB)
    codes = db.Column('codes', JSONB)
    htmls = db.Column('htmls', JSONB)
    links = db.Column('links', JSONB)
    notifications = db.Column('notifications', JSONB)
    tables = db.Column('tables', JSONB)
    tags = db.Column('tags', ARRAY(db.String, dimensions=1))
    entity_type = db.relationship('EntityType', foreign_keys=[entity_type_etid], back_populates='entities',
                                  innerjoin=True)
    parent = db.relationship('Entity', foreign_keys=[parent_eid], remote_side=[eid], back_populates='children',
                             innerjoin=True)
    children = db.relationship('Entity', foreign_keys=[parent_eid], remote_side=[parent_eid], back_populates='parent',
                               innerjoin=True)
    loaded_by = db.relationship('Entity', foreign_keys=[loaded_by_eid], remote_side=[eid],
                                back_populates='entities_loaded_by_me', innerjoin=True)
    entities_loaded_by_me = db.relationship('Entity', foreign_keys=[loaded_by_eid], remote_side=[loaded_by_eid],
                                            back_populates='loaded_by', innerjoin=True)
    relations_loaded_by_me = db.relationship('Relation', foreign_keys=[Relation.loaded_by_eid],
                                             back_populates='loaded_by', innerjoin=True)
    relation_source = db.relationship('Relation', foreign_keys=[Relation.source], back_populates='source_entity',
                                      innerjoin=True)
    relation_destination = db.relationship('Relation', foreign_keys=[Relation.destination],
                                           back_populates='destination_entity', innerjoin=True)
    relation_attribute = db.relationship('Relation', foreign_keys=[Relation.attribute],
                                         back_populates='attribute_entity',
                                         innerjoin=True)

    @staticmethod
    def insert_on_conflict_do_nothing(**kwargs):
        db.session.execute(insert(Entity).values(kwargs).on_conflict_do_nothing(index_elements=['urn']))
        db.session.commit()

    @staticmethod
    def insert_on_conflict_do_nothing_by_urn(loaded_by_eid, entity_type_etid: EntityType, urn: str):
        Entity.insert_on_conflict_do_nothing(loaded_by_eid=loaded_by_eid,
                                             entity_type_etid=entity_type_etid,
                                             urn=urn,
                                             entity_name='.'.join(urn.split('.')[2:]),
                                             entity_name_short=urn.split('.')[-1],
                                             info='Table at ' + urn.split('.')[0].title() + ' ' + urn.split('.')[
                                                 1] + ' instance (Could be wrong, generated by lineage backend)',
                                             search_data=urn.split('.')[-1],
                                             json_data={'core_system': urn.split('.')[0].title()},
                                             json_data_ui={'CORE_SYSTEM': urn.split('.')[0].title()},
                                             tags=['table'])

    @staticmethod
    def destinations(**kwargs) -> list:
        return Entity.query.from_statement(text(
            "SELECT * FROM dds.entity WHERE eid IN("
            "SELECT destination FROM dds.relation WHERE source = :source_eid AND attribute = :attribute_eid"
            ")")).params(kwargs).all()

    @staticmethod
    def destination_attributes(**kwargs) -> list:
        return Entity.query.from_statement(text(
            "SELECT * FROM dds.entity WHERE eid IN("
            "SELECT attribute FROM dds.relation WHERE source = :source_eid"
            ")")).params(kwargs).all()

    @staticmethod
    def destination_destinations(**kwargs) -> list:
        return Entity.query.from_statement(text(
            "SELECT * FROM dds.entity WHERE eid IN("
            "SELECT destination FROM dds.relation WHERE source = :source_eid AND attribute = :attribute_eid"
            ")")).params(kwargs).all()

    def __repr__(self):
        return '<Entity {}>'.format(self.entity_name_short)
