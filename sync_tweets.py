#!/usr/bin/env python3
"""
Sync Tweets Script
Fetches all tweets from the last 30 days and stores them in MongoDB

Usage:
    python sync_tweets.py <username> [--days 30]
"""

import os
import sys
import argparse
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Suppress Streamlit import warnings
os.environ['STREAMLIT_SUPPRESS_DEPRECATION_WARNING'] = 'true'

from twitter_api_adapter import RettiwtAPI
from database import Database


def sync_tweets(username: str, days: int = 30):
    """
    Fetch all tweets from the last N days and store in MongoDB
    
    Args:
        username: Twitter username to sync
        days: Number of days to look back (default 30)
    """
    print(f"\n{'='*60}")
    print(f"  Twitter Sync - @{username}")
    print(f"{'='*60}")
    print(f"📅 Fetching tweets from last {days} days")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize API and DB
    api = RettiwtAPI(username=username)
    db = Database()
    
    # Check connections
    if not db.is_connected():
        print("❌ MongoDB not connected. Check MONGODB_URI in .env")
        return False
    
    print("✅ MongoDB connected")
    
    # Get user info first
    print(f"\n📊 Fetching user info for @{username}...")
    user_info = api.get_user_by_username(username)
    
    if not user_info:
        print(f"❌ Could not find user @{username}")
        return False
    
    user_id = user_info.get('id')
    print(f"   User ID: {user_id}")
    print(f"   Name: {user_info.get('name')}")
    print(f"   Followers: {user_info.get('public_metrics', {}).get('followers_count', 0):,}")
    print(f"   Total Tweets: {user_info.get('public_metrics', {}).get('tweet_count', 0):,}")
    
    # Fetch all tweets from last N days
    print(f"\n📥 Fetching tweets from last {days} days...")
    print("   (This may take a moment for accounts with many tweets)")
    
    tweets = api.get_all_tweets_since(user_id, days=days)
    
    if not tweets:
        print("📭 No tweets found in the specified period")
        return True
    
    print(f"\n✅ Fetched {len(tweets)} tweets")
    
    # Display sample tweets
    print("\n📝 Sample tweets:")
    for i, tweet in enumerate(tweets[:3]):
        metrics = tweet.get('public_metrics', {})
        text = tweet.get('text', '')[:50]
        print(f"   [{i+1}] \"{text}...\"")
        print(f"       👁️ {metrics.get('impression_count', 0):,} views | "
              f"❤️ {metrics.get('like_count', 0):,} | "
              f"🔁 {metrics.get('retweet_count', 0):,}")
    
    # Save to MongoDB (only new tweets, skip existing)
    print(f"\n💾 Checking {len(tweets)} tweets against MongoDB...")
    saved_count = db.save_live_tweets(user_id, tweets)
    
    if saved_count > 0:
        print(f"✅ Inserted {saved_count} NEW tweets")
    else:
        print(f"✅ All tweets already exist in database (0 new tweets)")
    
    # Summary
    skipped = len(tweets) - saved_count
    
    print(f"\n{'='*60}")
    print(f"  Sync Complete!")
    print(f"{'='*60}")
    print(f"   User: @{username} ({user_id})")
    print(f"   Tweets Fetched: {len(tweets)}")
    print(f"   New Tweets Saved: {saved_count}")
    print(f"   Already in DB (skipped): {skipped}")
    print(f"   Period: Last {days} days")
    print(f"   Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Sync Twitter tweets to MongoDB')
    parser.add_argument('username', help='Twitter username to sync')
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back (default: 30)')
    
    args = parser.parse_args()
    
    # Remove @ if present
    username = args.username.lstrip('@')
    
    success = sync_tweets(username, args.days)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

