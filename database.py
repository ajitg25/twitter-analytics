"""MongoDB Database Module for User Data Storage"""

import os
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import streamlit as st

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# MongoDB Configuration
def _get_mongodb_uri():
    """Get MongoDB URI from environment or Streamlit secrets"""
    uri = os.getenv('MONGODB_URI', '')
    if not uri:
        try:
            uri = st.secrets.get('MONGODB_URI', '')
        except:
            pass
    return uri

MONGODB_URI = _get_mongodb_uri()
DATABASE_NAME = os.getenv('DATABASE_NAME', 'twitter_analytics')


class Database:
    """MongoDB database handler"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        
        if MONGODB_URI:
            try:
                self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client[DATABASE_NAME]
                self.connected = True
                self._setup_indexes()
            except ConnectionFailure as e:
                st.warning(f"⚠️ MongoDB connection failed: {e}")
                self.connected = False
            except Exception as e:
                st.warning(f"⚠️ Database initialization error: {e}")
                self.connected = False
    
    def _setup_indexes(self):
        """Setup database indexes for better performance"""
        if not self.connected:
            return
        
        try:
            # Users collection indexes
            self.db.users.create_index('twitter_id', unique=True)
            self.db.users.create_index('username')
            
            # User data collection indexes
            self.db.user_data.create_index('user_id')
            self.db.user_data.create_index('upload_date')
            
            # Connections
            self.db.connections.create_index([('user_id', 1), ('type', 1), ('connection_id', 1)], unique=True)
            
            # Standard Tweets Collection
            # Unique index on (user_id, tweet_id) to support upserts
            self.db.tweets.create_index([('user_id', 1), ('tweet_id', 1)], unique=True)
            self.db.tweets.create_index([('user_id', 1), ('created_at', -1)])
                
        except Exception as e:
                st.warning(f"⚠️ Error setting up indexes: {e}")

    # ... (skipping methods until save_tweets) ...

    def save_tweets(self, user_id, tweets_data):
        """Save user's tweets for growth tracking (Archive Upload)"""
        if not self.connected:
            return 0
        
        from pymongo import UpdateOne
        
        try:
            operations = []
            
            for tweet_obj in tweets_data:
                tweet = tweet_obj.get('tweet', {})
                
                tweet_doc = {
                    'user_id': user_id,
                    'tweet_id': tweet.get('id_str'),
                    'created_at': self._parse_twitter_date(tweet.get('created_at')),
                    'full_text': tweet.get('full_text', ''),
                    'favorite_count': int(tweet.get('favorite_count', 0)),
                    'retweet_count': int(tweet.get('retweet_count', 0)),
                    'is_reply': 'in_reply_to_status_id' in tweet,
                    'is_retweet': tweet.get('retweeted', False),
                    'uploaded_at': datetime.now()
                }
                
                # Upsert to prevent duplicates
                op = UpdateOne(
                    {'user_id': user_id, 'tweet_id': tweet.get('id_str')},
                    {'$set': tweet_doc},
                    upsert=True
                )
                operations.append(op)
            
            if operations:
                result = self.db.tweets.bulk_write(operations, ordered=False)
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            st.warning(f"⚠️ Error saving archive tweets: {e}")
            return 0

    # ... (skipping methods until get_growth_data) ...
    
    def get_growth_data(self, user_id, days=30):
        """Get growth trajectory data for user"""
        if not self.connected:
            return None
        
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get tweets in date range from tweets collection
            tweets = self.db.tweets.find({
                'user_id': user_id,
                'created_at': {'$gte': cutoff_date}
            }).sort('created_at', 1)
            
            return list(tweets)
        except Exception as e:
            st.error(f"Error fetching growth data: {e}")
            return None

    # ... (skipping methods until save_live_tweets) ...

    def save_live_tweets(self, user_id, tweets_data):
        """
        Save NEW tweets from Live API (skip existing ones).
        Only inserts tweets that don't already exist in DB.
        Maps Live API format to internal DB schema.
        """
        if not self.connected or not tweets_data:
            return 0
        
        from pymongo import UpdateOne
        
        try:
            operations = []
            for t in tweets_data:
                # Map Live API fields to DB Schema (compatible with Archive)
                # Live: id, text, created_at, public_metrics
                
                metrics = t.get('public_metrics', {})
                created_at = self._parse_twitter_date(t.get('created_at'))
                
                tweet_doc = {
                    'user_id': user_id,
                    'tweet_id': t.get('id'),
                    'created_at': created_at,
                    'full_text': t.get('text'),
                    'favorite_count': metrics.get('like_count', 0),
                    'retweet_count': metrics.get('retweet_count', 0),
                    'reply_count': metrics.get('reply_count', 0),
                    'quote_count': metrics.get('quote_count', 0),
                    'bookmark_count': metrics.get('bookmark_count', 0),
                    'impression_count': metrics.get('impression_count', 0),
                    'is_start_reply': t.get('text', '').startswith('@'), # Approximation
                    'inserted_at': datetime.now()
                }
                
                # Use $setOnInsert - only sets values when inserting NEW documents
                # If tweet already exists, this operation does nothing
                op = UpdateOne(
                    {'user_id': user_id, 'tweet_id': t.get('id')},
                    {'$setOnInsert': tweet_doc},
                    upsert=True
                )
                operations.append(op)
            
            if operations:
                result = self.db.tweets.bulk_write(operations, ordered=False)
                # Only count newly inserted tweets (not matched/modified)
                return result.upserted_count
            return 0
            
        except Exception as e:
            st.warning(f"⚠️ Error saving tweets: {e}")
            return 0

    def get_saved_tweets(self, user_id, limit=100):
        """Get latest tweets from DB"""
        if not self.connected: 
            return []
        try:
            # Sort by created_at desc
            docs = self.db.tweets.find({'user_id': user_id}).sort('created_at', -1).limit(limit)
            
            # Map back to Live API format for UI compatibility
            mapped_tweets = []
            for d in docs:
                mapped_tweets.append({
                    'id': d.get('tweet_id'),
                    'text': d.get('full_text'),
                    'created_at': d.get('created_at').strftime('%Y-%m-%dT%H:%M:%S.000Z') if d.get('created_at') else None,
                    'public_metrics': {
                        'like_count': d.get('favorite_count', 0),
                        'retweet_count': d.get('retweet_count', 0),
                        'reply_count': d.get('reply_count', 0),
                        'quote_count': d.get('quote_count', 0),
                        'impression_count': d.get('impression_count', 0)
                    }
                })
            return mapped_tweets
        except Exception as e:
            st.error(f"Error retrieving saved tweets: {e}")
            return []
    
    def is_connected(self):
        """Check if database is connected"""
        return self.connected
    
    def create_or_update_user(self, user_info):
        """Create or update user in database"""
        if not self.connected:
            return None
        
        try:
            user_data = {
                'twitter_id': user_info.get('id'),
                'username': user_info.get('username'),
                'name': user_info.get('name'),
                'profile_image_url': user_info.get('profile_image_url'),
                'verified': user_info.get('verified', False),
                'access_token': user_info.get('access_token'),
                'refresh_token': user_info.get('refresh_token'),
                'last_login': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Upsert user (update if exists, insert if not)
            result = self.db.users.update_one(
                {'twitter_id': user_info.get('id')},
                {
                    '$set': user_data,
                    '$setOnInsert': {'created_at': datetime.now()}
                },
                upsert=True
            )
            
            # Get the user document
            user = self.db.users.find_one({'twitter_id': user_info.get('id')})
            return user
            
        except Exception as e:
            st.error(f"Error creating/updating user: {e}")
            return None
    
    def get_user_by_twitter_id(self, twitter_id):
        """Get user by Twitter ID"""
        if not self.connected:
            return None
        
        try:
            return self.db.users.find_one({'twitter_id': twitter_id})
        except Exception as e:
            st.error(f"Error fetching user: {e}")
            return None
    
    def save_user_upload(self, user_id, data):
        """Save user's Twitter archive upload"""
        if not self.connected:
            return None
        
        try:
            upload_data = {
                'user_id': user_id,
                'upload_date': datetime.now(),
                'stats': {
                    'total_tweets': len(data.get('tweets', [])),
                    'total_followers': len(data.get('followers', [])),
                    'total_following': len(data.get('following', [])),
                    'total_likes': len(data.get('likes', []))
                },
                'account_info': data.get('account', {}),
                'profile_info': data.get('profile', {})
            }
            
            result = self.db.user_data.insert_one(upload_data)
            return result.inserted_id
            
        except Exception as e:
            st.error(f"Error saving upload: {e}")
            return None
    
    def save_tweets(self, user_id, tweets_data):
        """Save user's tweets for growth tracking (Archive Upload)"""
        if not self.connected:
            return 0
        
        from pymongo import UpdateOne
        
        try:
            operations = []
            
            for tweet_obj in tweets_data:
                tweet = tweet_obj.get('tweet', {})
                
                tweet_doc = {
                    'user_id': user_id,
                    'tweet_id': tweet.get('id_str'),
                    'created_at': self._parse_twitter_date(tweet.get('created_at')),
                    'full_text': tweet.get('full_text', ''),
                    'favorite_count': int(tweet.get('favorite_count', 0)),
                    'retweet_count': int(tweet.get('retweet_count', 0)),
                    'is_reply': 'in_reply_to_status_id' in tweet,
                    'is_retweet': tweet.get('retweeted', False),
                    'uploaded_at': datetime.now()
                }
                
                # Upsert to prevent duplicates
                op = UpdateOne(
                    {'user_id': user_id, 'tweet_id': tweet.get('id_str')},
                    {'$set': tweet_doc},
                    upsert=True
                )
                operations.append(op)
            
            if operations:
                result = self.db.tweets.bulk_write(operations, ordered=False)
                return result.upserted_count + result.modified_count
            
            return 0
            
        except Exception as e:
            st.warning(f"⚠️ Error saving archive tweets: {e}")
            return 0
    
    def get_user_uploads(self, user_id, limit=10):
        """Get user's upload history"""
        if not self.connected:
            return []
        
        try:
            uploads = self.db.user_data.find(
                {'user_id': user_id}
            ).sort('upload_date', -1).limit(limit)
            
            return list(uploads)
        except Exception as e:
            st.error(f"Error fetching uploads: {e}")
            return []
    
    def get_growth_data(self, user_id, days=30):
        """Get growth trajectory data for user"""
        if not self.connected:
            return None
        
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get tweets in date range from tweets collection
            tweets = self.db.tweets.find({
                'user_id': user_id,
                'created_at': {'$gte': cutoff_date}
            }).sort('created_at', 1)
            
            return list(tweets)
        except Exception as e:
            st.error(f"Error fetching growth data: {e}")
            return None
    
    def _parse_twitter_date(self, date_str):
        """Parse Twitter date format to datetime"""
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            # Check if it's the V2 format (2023-12-01T10:00:00.000Z) or Archive format
            if 'T' in date_str and date_str.endswith('Z'):
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            
            # Twitter Archive format: "Tue Dec 02 06:23:48 +0000 2025"
            return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        except:
            return None
    
    # === LIVE API CACHING ===
    def save_live_api_response(self, user_id, endpoint, data):
        """
        Save a response from the live API to cache.
        endpoint: 'followers', 'following', 'recent_tweets'
        """
        if not self.connected:
            return None
        
        try:
            # Ensure unique index exists for (user_id, endpoint)
            # created loosely here or in setup
            
            cache_doc = {
                'user_id': user_id,
                'endpoint': endpoint,
                'data': data,
                'updated_at': datetime.now()
            }
            
            # Upsert
            result = self.db.api_cache.update_one(
                {'user_id': user_id, 'endpoint': endpoint},
                {'$set': cache_doc},
                upsert=True
            )
            return True
        except Exception as e:
            st.warning(f"⚠️ Cache Save Error: {e}")
            return False

    def get_cache_age(self, user_id, endpoint):
        """Get minutes since last update for specific data in DB"""
        if not self.connected:
            return 999999
        
        try:
            latest_doc = None
            if endpoint == 'recent_tweets':
                latest_doc = self.db.tweets.find_one(
                    {'user_id': user_id},
                    sort=[('updated_at', -1)]
                )
            elif endpoint in ['followers', 'following']:
                latest_doc = self.db.connections.find_one(
                    {'user_id': user_id, 'type': endpoint},
                    sort=[('updated_at', -1)]
                )
            
            if latest_doc and 'updated_at' in latest_doc:
                delta = datetime.now() - latest_doc['updated_at']
                return delta.total_seconds() / 60
            
            # Fallback to metadata if direct check fails
            meta = self.db.api_cache.find_one({'user_id': user_id, 'endpoint': endpoint})
            if meta:
                delta = datetime.now() - meta.get('updated_at', datetime.min)
                return delta.total_seconds() / 60
                
            return 999999
        except:
            return 999999

    def get_live_api_response(self, user_id, endpoint):
        """Retrieve cached API response"""
        if not self.connected:
            return None
        
        try:
            doc = self.db.api_cache.find_one({'user_id': user_id, 'endpoint': endpoint})
            if doc:
                return doc.get('data')
            return None
        except Exception as e:
            return None

    # === INCREMENTAL LIVE DATA SAVING ===
    # Note: save_live_tweets is defined above - this is a duplicate that should be removed
    # Keeping as alias for backwards compatibility
    # def save_live_tweets(self, user_id, tweets_data):
    #     See the method defined earlier in this class

    def get_saved_tweets(self, user_id, limit=100):
        """Get latest tweets from DB"""
        if not self.connected: 
            return []
        try:
            # Sort by created_at desc
            docs = self.db.tweets.find({'user_id': user_id}).sort('created_at', -1).limit(limit)
            
            # Map back to Live API format for UI compatibility
            mapped_tweets = []
            for d in docs:
                mapped_tweets.append({
                    'id': d.get('tweet_id'),
                    'text': d.get('full_text'),
                    'created_at': d.get('created_at').strftime('%Y-%m-%dT%H:%M:%S.000Z') if d.get('created_at') else None,
                    'public_metrics': {
                        'like_count': d.get('favorite_count', 0),
                        'retweet_count': d.get('retweet_count', 0),
                        'reply_count': d.get('reply_count', 0),
                        'quote_count': d.get('quote_count', 0),
                        'impression_count': d.get('impression_count', 0)
                    }
                })
            return mapped_tweets
        except Exception as e:
            st.error(f"Error retrieving saved tweets: {e}")
            return []

    def save_live_connections(self, user_id, users_list, connection_type):
        """
        Incrementally save followers/following.
        connection_type: 'followers' or 'following'
        """
        if not self.connected or not users_list:
            return 0
            
        from pymongo import UpdateOne
        
        try:
            operations = []
            for u in users_list:
                # Connection Doc
                conn_doc = {
                    'user_id': user_id,
                    'connection_id': u.get('id'),
                    'type': connection_type,
                    'username': u.get('username'),
                    'name': u.get('name'),
                    'joined_at': u.get('created_at'), # Twitter created_at
                    'public_metrics': u.get('public_metrics', {}),
                    'profile_image_url': u.get('profile_image_url'),
                    'verified': u.get('verified', False),
                    'updated_at': datetime.now()
                }
                
                # Upsert based on composite key
                op = UpdateOne(
                    {
                        'user_id': user_id, 
                        'connection_id': u.get('id'),
                        'type': connection_type
                    },
                    {'$set': conn_doc},
                    upsert=True
                )
                operations.append(op)
            
            if operations:
                # Use 'connections' collection
                result = self.db.connections.bulk_write(operations, ordered=False)
                return result.upserted_count + result.modified_count
            return 0
        except Exception as e:
            st.warning(f"⚠️ Error saving {connection_type}: {e}")
            return 0

    def get_saved_connections(self, user_id, connection_type, limit=1000):
        """Get connected users from DB"""
        if not self.connected: return []
        try:
            docs = self.db.connections.find(
                {'user_id': user_id, 'type': connection_type}
            ).limit(limit)
            
            # Map back to API format
            mapped = []
            for d in docs:
                mapped.append({
                    'id': d.get('connection_id'),
                    'username': d.get('username'),
                    'name': d.get('name'),
                    'created_at': d.get('joined_at'),
                    'public_metrics': d.get('public_metrics'),
                    'profile_image_url': d.get('profile_image_url'),
                    'verified': d.get('verified')
                })
            return mapped
        except Exception as e:
            return []

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()


# Global database instance
_db_instance = None

def get_database():
    """Get or create database instance"""
    global _db_instance
    
    if _db_instance is None:
        _db_instance = Database()
    
    return _db_instance
