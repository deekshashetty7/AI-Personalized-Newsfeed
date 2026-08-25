"""
Shared MongoDB connection for the app's actual data (articles, users' app-level
profiles, interactions, recommendations, etc).

Django's own DATABASES setting (in settings.py) uses SQLite only for Django's
internal tables — auth, sessions, admin, migrations. Everything else — your
news articles, interactions, recommendations — should read/write through
`db` from this module instead of Django's ORM.

Usage in views.py or elsewhere:

    from api.mongo_client import db

    # Read
    article = db.news_articles.find_one({"_id": some_id})
    articles = list(db.news_articles.find({"category": "technology"}).limit(20))

    # Write
    db.news_articles.insert_one({"title": "...", "content": "...", ...})
    db.interactions.update_one(
        {"user_id": user_id, "article_id": article_id},
        {"$set": {"liked": True}},
        upsert=True,
    )
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

_MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
_MONGODB_NAME = os.getenv("MONGODB_NAME", "ai_newsfeed")

# A single shared client is reused across requests — pymongo's MongoClient
# is thread-safe and manages its own connection pool internally, so this
# should NOT be recreated per-request.
_client = MongoClient(_MONGODB_URI, serverSelectionTimeoutMS=10000)

# The actual database handle your code should import and use.
db = _client[_MONGODB_NAME]


def check_connection():
    """
    Call this at startup (e.g. in an AppConfig.ready() hook, or manually)
    to confirm MongoDB is reachable before serving requests. Raises
    ConnectionFailure if it can't reach Atlas.
    """
    try:
        _client.admin.command("ping")
        return True
    except ConnectionFailure as exc:
        raise ConnectionFailure(
            f"Could not connect to MongoDB at {_MONGODB_NAME}: {exc}"
        ) from exc
