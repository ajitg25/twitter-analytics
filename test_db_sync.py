import os
import pandas as pd
from database import get_database
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_sync():
    print("🚀 Starting DB Sync Test...")
    db = get_database()
    if not db.is_connected():
        print("❌ DB not connected. Check .env")
        return

    # Aggressive Cleanup: Drop tweets_v2 if it exists to ensure standard collection
    try:
        collections = db.db.list_collection_names()
        if 'tweets_v2' in collections:
            print("🗑️ Dropping existing tweets_v2 to ensure Standard (non-timeseries) status...")
            db.db.tweets_v2.drop()
            print("✅ Dropped.")
        else:
            print("ℹ️ tweets_v2 does not exist, will be created as standard.")
    except Exception as e:
        print(f"❓ Error clearing collection: {e}")

    # Load data from export
    csv_file = "exports/tweets_export_1274417026493276160_20251221_134808.csv"
    if not os.path.exists(csv_file):
        # Find any csv in exports if exact one not found
        import glob
        exports = glob.glob("exports/*.csv")
        if exports:
            csv_file = exports[0]
        else:
            print(f"❌ No CSV files found in exports/")
            return

    print(f"📖 Reading {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df)} tweets.")

    # Convert dataframe rows back to the format save_live_tweets expects
    test_tweets = []
    for _, row in df.iterrows():
        # Reconstruct public_metrics from flattened CSV columns
        metrics = {
            'like_count': int(row.get('metric_like_count', 0)),
            'retweet_count': int(row.get('metric_retweet_count', 0)),
            'reply_count': int(row.get('metric_reply_count', 0)),
            'quote_count': int(row.get('metric_quote_count', 0)),
            'impression_count': int(row.get('metric_impression_count', 0))
        }
        
        test_tweets.append({
            'id': str(row['id']),
            'text': row['text'],
            'created_at': row['created_at'],
            'public_metrics': metrics
        })

    # Get user_id from filename if possible
    try:
        user_id = os.path.basename(csv_file).split('_')[2]
    except:
        user_id = '1274417026493276160'
        
    print(f"👤 Detected User ID: {user_id}")
    print(f"💾 Attempting to save {len(test_tweets)} tweets to DB...")
    
    count = db.save_live_tweets(user_id, test_tweets)
    print(f"📊 Result: Saved/Updated {count} tweets.")
    print(f"🔍 Database in use: {db.db.name}")
    
    # Verify
    all_docs = list(db.db.tweets_v2.find({}))
    print(f"🧪 Total documents in tweets_v2: {len(all_docs)}")
    if all_docs:
        print(f"📌 Sample document user_id: '{all_docs[0].get('user_id')}' (Type: {type(all_docs[0].get('user_id'))})")
        print(f"🕵️ Searched for user_id: '{user_id}' (Type: {type(user_id)})")
    
    saved = list(db.db.tweets_v2.find({'user_id': user_id}))
    print(f"🧪 Verification: Found {len(saved)} documents specifically for user {user_id}.")

if __name__ == "__main__":
    test_sync()
