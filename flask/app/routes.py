from blueprints.homepage_blueprint import homepage_bp
from blueprints.search_blueprint import search_bp
from blueprints.infocards_blueprint import infocards_bp
from blueprints.metadata_blueprint import metadata_bp
from blueprints.open_lineage_blueprint import ol_bp
from blueprints.lineage_blueprint import lineage_card_bp
from blueprints.lineage_search_blueprint import lineage_search_bp


def route(app):
    app.register_blueprint(homepage_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(infocards_bp)
    app.register_blueprint(metadata_bp)
    app.register_blueprint(ol_bp)
    app.register_blueprint(lineage_card_bp)
    app.register_blueprint(lineage_search_bp)
