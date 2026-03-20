from MongoDB.db import connect_db


def get_model_client(app):
    if not hasattr(app.state, "client"):
        from Model.load_model import get_model
        app.state.client = get_model()
    return app.state.client


def get_mongo(app):
    if not hasattr(app.state, "mongo_client"):
        client = connect_db()
        app.state.mongo_client = client
        app.state.zensky_db = client["ZenskyDatabase"]
    return app.state.zensky_db


def get_qdrant(app):
    if not hasattr(app.state, "qdrant_client"):
        from Qdrant.db import instantiate_chroma

        app.state.qdrant_client = instantiate_chroma()
    return app.state.qdrant_client
