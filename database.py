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
MONGODB_URI = os.getenv('MONGODB_URI', st.secrets.get('MONGODB_URI', ''))
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
            
            # Tweets collection indexes
            # Note: If tweets is a time-series collection, unique indexes are not supported
            # Time-series collections already have optimized indexes on timeField and metaField
            try:
                self.db.tweets.create_index([('user_id', 1), ('created_at', -1)])
            except Exception:
                # Skip if it's a time-series collection (indexes auto-created)
                pass
                
        except Exception as e:
            # Only warn if it's not a time-series collection issue
            if 'time-series' not in str(e).lower():
                st.warning(f"⚠️ Error setting up indexes: {e}")
    
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
        """Save user's tweets for growth tracking"""
        if not self.connected:
            return 0
        
        try:
            tweets_to_insert = []
            
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
                
                tweets_to_insert.append(tweet_doc)
            
            if tweets_to_insert:
                # Use ordered=False to continue on duplicate key errors
                result = self.db.tweets.insert_many(tweets_to_insert, ordered=False)
                return len(result.inserted_ids)
            
            return 0
            
        except DuplicateKeyError:
            # Some tweets already exist, that's okay
            return len(tweets_to_insert)
        except Exception as e:
            st.error(f"Error saving tweets: {e}")
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
            
            # Get tweets in date range
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
            # Twitter format: "Tue Dec 02 06:23:48 +0000 2025"
            return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        except:
            return None
    
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
