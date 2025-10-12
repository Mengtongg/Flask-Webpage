from flask import current_app

# adds/updates a document in an Elasticsearch index
def add_to_index(index, model):
    # check when Elasticsearch server not configured
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        # JSON document body will send to ES
        payload[field] = getattr(model, field)
    # same id value, link teo databases  
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)

# deletes document stored under given id
def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)

# takes index name and text to search for
def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        # search across multiple fields
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']