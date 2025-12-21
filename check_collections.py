from database import get_database
db = get_database()
if db.is_connected():
    print(f"Collections: {db.db.list_collection_names()}")
    for coll in db.db.list_collection_names():
        info = db.db.command("listCollections", filter={"name": coll})
        options = info['cursor']['firstBatch'][0].get('options', {})
        if 'timeseries' in options:
            print(f"⚠️ {coll} is a TIME-SERIES collection.")
        else:
            print(f"✅ {coll} is a standard collection.")
else:
    print("Failed to connect.")
