from database import get_database
db = get_database()
if db.is_connected():
    doc = db.db.tweets_v2.find_one({})
    if doc:
        print(f"Sample tweet user_id: '{doc.get('user_id')}' (Type: {type(doc.get('user_id'))})")
    else:
        print("Collection tweets_v2 is empty!")
    
    # Check tweets collection too
    doc_old = db.db.tweets.find_one({})
    if doc_old:
        print(f"Sample OLD tweet user_id: '{doc_old.get('user_id')}' (Type: {type(doc_old.get('user_id'))})")
else:
    print("Not connected.")
