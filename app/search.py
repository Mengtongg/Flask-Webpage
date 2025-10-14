from flask import current_app
import sqlalchemy as sa
from app import db

# adds/updates a document in an Elasticsearch index
def add_to_index(index, model):
    # check when Elasticsearch server not configured
    es = current_app.elasticsearch
    if not es:
        return
    payload = {}
    for field in model.__searchable__:
        # JSON document body will send to ES
        payload[field] = getattr(model, field)

    try:
        # refresh so searches see docs immediately (safe to omit)
        es.index(index=index, id=model.id, document=payload, refresh="wait_for")
    except Exception as e:   
        # same id value, link teo databases  
        current_app.logger.warning("Search indexing skipped: %s", e)

# deletes document stored under given id
def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    try:
        current_app.elasticsearch.delete(index=index, id=model.id, ignore=[404], refresh="wait_for")
    except Exception as e:
        current_app.logger.warning("Search delete skipped: %s", e)

# takes index name and text to search for
def query_index(index, query, page, per_page):
    #if not current_app.elasticsearch:
        #return [], 0
    #search = current_app.elasticsearch.search(
        #index=index,
        # search across multiple fields
        #query={'multi_match': {'query': query, 'fields': ['*']}},
        #from_=(page - 1) * per_page,
        #size=per_page)
    #ids = [int(hit['_id']) for hit in search['hits']['hits']]
    #return ids, search['hits']['total']['value']
    es = current_app.elasticsearch

    # --- Preferred path: Elasticsearch ---
    if es:
        try:
            search = es.search(
                index=index,
                # search across multiple fields
                query={'multi_match': {'query': query, 'fields': ['*']}},
                from_=(page - 1) * per_page,
                size=per_page
            )
            ids = [int(hit['_id']) for hit in search['hits']['hits']]
            return ids, search['hits']['total']['value']
        except Exception as e:
            current_app.logger.warning("ES search failed, falling back to SQL: %s", e)

    # --- Fallback path: simple SQL LIKE (posts only) ---
    try:
        from app.models import Post  # local import to avoid circulars
        # accept "post", "posts", or the model's table name
        if index not in ('post', 'posts', getattr(Post, '__tablename__', 'post')):
            return [], 0

        # ids page slice
        stmt = (sa.select(Post.id)
                  .where(Post.body.ilike(f"%{query}%"))
                  .order_by(Post.timestamp.desc())
                  .offset((page - 1) * per_page)
                  .limit(per_page))
        ids = [row[0] for row in db.session.execute(stmt)]

        # total count
        total_stmt = sa.select(sa.func.count()).select_from(
            sa.select(Post.id).where(Post.body.ilike(f"%{query}%")).subquery()
        )
        total = db.session.scalar(total_stmt) or 0

        return ids, total
    except Exception as e:
        current_app.logger.warning("SQL fallback search failed: %s", e)
        return [], 0
