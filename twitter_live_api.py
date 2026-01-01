"""Twitter Live API - Fetch real-time data using OAuth access token or Rettiwt-API

Supports two modes controlled by TWITTER_OFFICIAL environment variable:
- TWITTER_OFFICIAL=true  -> Use official Twitter API (paid, requires OAuth)
- TWITTER_OFFICIAL=false -> Use Rettiwt-API (free, requires rettiwt-service running)
"""

import requests
import os
from datetime import datetime, timedelta
import streamlit as st
from database import get_database
from twitter_api_adapter import get_twitter_api, get_api_mode, TwitterAPIBase


class TwitterLiveAPI:
    """Fetch live Twitter data using OAuth 2.0 access token or Rettiwt-API"""
    
    def __init__(self, access_token=None, refresh_token=None, username=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.username = username
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            'Authorization': f'Bearer {access_token}'
        } if access_token else {}
        
        # Check environment
        self.env = os.getenv('APP_ENV', 'production').lower()
        self.use_official_api = os.getenv('TWITTER_OFFICIAL', 'false').lower() == 'true'
        
        # Initialize the appropriate API adapter
        self._api: TwitterAPIBase = get_twitter_api(
            access_token=access_token,
            refresh_token=refresh_token,
            username=username
        )

    def _refresh_token(self):
        """Internal helper to refresh the access token (Official API only)"""
        if not self.refresh_token or not self.use_official_api:
            return False
            
        try:
            from auth import refresh_access_token
            new_tokens = refresh_access_token(self.refresh_token)
            
            if new_tokens:
                self.access_token = new_tokens.get('access_token')
                self.refresh_token = new_tokens.get('refresh_token', self.refresh_token)
                self.headers['Authorization'] = f'Bearer {self.access_token}'
                
                # Update session state
                if 'user_info' in st.session_state:
                    st.session_state.user_info['access_token'] = self.access_token
                    st.session_state.user_info['refresh_token'] = self.refresh_token
                
                # Update DB
                from database import get_database
                db = get_database()
                if db.is_connected() and 'user_info' in st.session_state:
                    db.create_or_update_user(st.session_state.user_info)
                
                return True
        except Exception as e:
            print(f"Token Refresh Exception: {e}")
        return False

    def get_my_user_id(self):
        """Get the authenticated user's Twitter ID - Cache First"""
        # 1. Check Session Cache
        if 'live_user_id_cache' in st.session_state:
            return st.session_state.live_user_id_cache
            
        # 2. Check user_info from auth if available
        if 'user_info' in st.session_state and st.session_state.user_info.get('id'):
            return st.session_state.user_info.get('id')

        if self.env == 'development':
            return "1234567890"

        # 3. Use the API adapter to get user info
        try:
            user_info = self._api.get_my_user_info()
            
            if user_info:
                user_id = user_info.get('id')
                if user_id:
                    st.session_state.live_user_id_cache = user_id
                return user_id
            return None
        except Exception as e:
            st.error(f"Error getting user ID: {e}")
            return None
    
    def get_recent_tweets(self, user_id, max_results=100, force_refresh=False):
        """
        Get user's tweets from the last 90 days - Cache First with Pagination
        """
        from datetime import datetime, timedelta, timezone
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        start_time_str = ninety_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ')

        if self.env == 'development':
            import pandas as pd
            from pathlib import Path
            export_dir = Path("exports")
            csvs = list(export_dir.glob("tweets_export_*.csv")) if export_dir.exists() else []
            
            if csvs:
                latest_csv = max(csvs, key=lambda p: p.stat().st_mtime)
                try:
                    df = pd.read_csv(latest_csv)
                    tweets = []
                    for _, row in df.iterrows():
                        tweet = {
                            'id': str(row.get('id', '')),
                            'text': str(row.get('text', '')),
                            'created_at': str(row.get('created_at', '')),
                            'author_id': str(row.get('author_id', '')),
                            'public_metrics': {
                                'impression_count': int(row.get('metric_impression_count', 0)),
                                'like_count': int(row.get('metric_like_count', 0)),
                                'retweet_count': int(row.get('metric_retweet_count', 0)),
                                'reply_count': int(row.get('metric_reply_count', 0)),
                                'quote_count': int(row.get('metric_quote_count', 0)),
                                'bookmark_count': int(row.get('metric_bookmark_count', 0))
                            }
                        }
                        tweets.append(tweet)
                    st.caption(f"🧪 Development Mode: Loaded {len(tweets)} tweets from {latest_csv.name}")
                    return tweets
                except Exception as e:
                    st.warning(f"Failed to load export CSV: {e}")

            # Fallback to Mock Data
            import random
            mock_tweets = []
            now = datetime.now()
            for i in range(150):
                created_at = now - timedelta(hours=i*14)
                if created_at.timestamp() < (now - timedelta(days=90)).timestamp(): continue
                mock_tweets.append({
                    'id': f'tweet_{i}',
                    'text': f"Mock Tweet {i+1}",
                    'created_at': created_at.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'author_id': user_id,
                    'public_metrics': {
                        'impression_count': random.randint(100, 5000), 'like_count': random.randint(10, 500),
                        'retweet_count': random.randint(0, 100), 'reply_count': random.randint(0, 50),
                        'quote_count': random.randint(0, 20), 'bookmark_count': random.randint(0, 30)
                    }
                })
            return mock_tweets

        db = get_database()
        if not force_refresh and db.is_connected():
            age = db.get_cache_age(user_id, 'recent_tweets')
            if age < 15:
                cached = db.get_saved_tweets(user_id, limit=3200) 
                if cached:
                    api_mode = get_api_mode()
                    st.caption(f"💾 Using database data (Checked {int(age)}m ago) | Mode: {api_mode}")
                    return cached

        # Use the API adapter to fetch tweets
        try:
            all_tweets = self._api.get_recent_tweets(user_id, max_results=max_results)

            if all_tweets:
                # 1. Save to Database
                if db.is_connected():
                     db.save_live_tweets(user_id, all_tweets)
                     db.save_live_api_response(user_id, 'recent_tweets', {'count': len(all_tweets)})
                
                # Use all_tweets for the rest of progress
                tweets = all_tweets
                
                # 2. Export to Local CSV for Manual Analysis (development only)
                try:
                    import pandas as pd
                    from pathlib import Path
                    
                    if self.env == "development":
                        export_dir = Path("exports")
                        export_dir.mkdir(exist_ok=True)
                        
                        # Flatten metrics for CSV compatibility
                        flat_tweets = []
                        for t in tweets:
                            item = t.copy()
                            metrics = item.pop('public_metrics', {})
                            for k, v in metrics.items():
                                item[f'metric_{k}'] = v
                            flat_tweets.append(item)
                            
                        df = pd.DataFrame(flat_tweets)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = export_dir / f"tweets_export_{user_id}_{timestamp}.csv"
                        df.to_csv(filename, index=False)
                        st.sidebar.info(f"📁 Local CSV Exported: {filename.name}")
                except Exception as export_error:
                    print(f"CSV Export Exception: {export_error}")

                return tweets
            
            # Fallback to DB if all_tweets is empty but we reached here
            return db.get_saved_tweets(user_id, limit=max_results) if db.is_connected() else []
                
        except Exception as e:
            st.error(f"Error fetching tweets: {e}")
            return db.get_saved_tweets(user_id, limit=max_results) if db.is_connected() else []

    def get_tweet_metrics_summary(self, tweets):
        """
        Calculate summary metrics from tweets (Logic is identical for real/mock)
        """
        if not tweets:
            return {
                'total_tweets': 0, 'total_impressions': 0, 'total_likes': 0,
                'total_retweets': 0, 'total_replies': 0, 'total_quotes': 0,
                'avg_impressions': 0, 'avg_engagement_rate': 0
            }
        
        total_impressions = sum(t.get('public_metrics', {}).get('impression_count', 0) for t in tweets)
        total_likes = sum(t.get('public_metrics', {}).get('like_count', 0) for t in tweets)
        total_retweets = sum(t.get('public_metrics', {}).get('retweet_count', 0) for t in tweets)
        total_replies = sum(t.get('public_metrics', {}).get('reply_count', 0) for t in tweets)
        total_quotes = sum(t.get('public_metrics', {}).get('quote_count', 0) for t in tweets)
        
        total_engagements = total_likes + total_retweets + total_replies + total_quotes
        avg_engagement_rate = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
        
        return {
            'total_tweets': len(tweets),
            'total_impressions': total_impressions,
            'total_likes': total_likes,
            'total_retweets': total_retweets,
            'total_replies': total_replies,
            'total_quotes': total_quotes,
            'avg_impressions': total_impressions // len(tweets) if tweets else 0,
            'avg_engagement_rate': round(avg_engagement_rate, 2)
        }
    
    def get_weekly_performance(self):
        """Get performance metrics for the last 7 days"""
        user_id = self.get_my_user_id()
        if not user_id:
            return None
            
        tweets = self.get_recent_tweets(user_id, max_results=100)
        
        if not tweets:
             return None

        # Logic is shared, just reusing the fetched tweets
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_tweets = []
        for tweet in tweets:
            try:
                # Handle possible formats
                dt_str = tweet['created_at']
                if 'T' in dt_str:
                    created_at = datetime.strptime(dt_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                else:
                    created_at = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                
                if created_at >= seven_days_ago:
                    recent_tweets.append(tweet)
            except:
                recent_tweets.append(tweet) # Fallback if parse fails
        
        metrics = self.get_tweet_metrics_summary(recent_tweets)
        return {
            'period': 'Last 7 days',
            'tweets_count': metrics['total_tweets'],
            'total_impressions': metrics['total_impressions'],
            'total_engagement': metrics['total_likes'] + metrics['total_retweets'] + 
                               metrics['total_replies'] + metrics['total_quotes'],
            'avg_engagement_rate': metrics['avg_engagement_rate'],
            'breakdown': {
                'likes': metrics['total_likes'],
                'retweets': metrics['total_retweets'],
                'replies': metrics['total_replies'],
                'quotes': metrics['total_quotes']
            }
        }

    def get_top_performing_tweet(self, tweets):
        if not tweets: return None
        return max(tweets, key=lambda t: (
            t.get('public_metrics', {}).get('like_count', 0) +
            t.get('public_metrics', {}).get('retweet_count', 0) +
            t.get('public_metrics', {}).get('reply_count', 0)
        ))

    def get_followers(self, user_id, max_results=100, pagination_token=None, force_refresh=False):
        """Get user's followers - Cache First"""
        if self.env == 'development':
            import random
            from datetime import timedelta
            
            mock_users = []
            now = datetime.now()
            for i in range(20):
                mock_users.append({
                    'id': f'follower_{i}',
                    'username': f'mock_follower_{i}',
                    'name': f'Fan Number {i}',
                    'created_at': (now - timedelta(days=i*10)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'public_metrics': {
                        'followers_count': random.randint(100, 10000),
                        'following_count': random.randint(100, 5000),
                        'tweet_count': random.randint(50, 2000),
                        'listed_count': random.randint(0, 50)
                    },
                    'verified': random.choice([True, False])
                })
            return {'data': mock_users, 'meta': {'result_count': 20}}

        # PRODUCTION LOGIC - Cache First
        db = get_database()
        
        if not force_refresh and not pagination_token and db.is_connected():
            age = db.get_cache_age(user_id, 'followers')
            if age < 60: # 60 minutes TTL
                cached = db.get_saved_connections(user_id, 'followers')
                if cached:
                    st.caption(f"👥 Using database followers (Checked {int(age)}m ago)")
                    return {'data': cached, 'meta': {'result_count': len(cached)}}

        # Use the API adapter to fetch followers
        try:
            result = self._api.get_followers(user_id, max_results=max_results)
            
            if result and 'data' in result:
                # Save to database
                if db.is_connected() and not pagination_token:
                    db.save_live_connections(user_id, result['data'], 'followers')
                    db.save_live_api_response(user_id, 'followers', {'count': len(result['data'])})
                return result
            
            # Fallback to database
            if db.is_connected():
                cached = db.get_saved_connections(user_id, 'followers')
                if cached:
                    st.info(f"📦 Loaded {len(cached)} followers from database.")
                    return {'data': cached, 'meta': {'result_count': len(cached)}}
            return None
            
        except Exception as e:
            st.error(f"Error fetching followers: {e}")
            if db.is_connected():
                cached = db.get_saved_connections(user_id, 'followers')
                if cached:
                    return {'data': cached, 'meta': {'result_count': len(cached)}}
            return None

    def get_following(self, user_id, max_results=100, pagination_token=None, force_refresh=False):
        """Get accounts the user is following - Cache First"""
        if self.env == 'development':
            import random
            from datetime import timedelta
            
            mock_users = []
            now = datetime.now()
            for i in range(15): # Mock 15 following
                mock_users.append({
                    'id': f'following_{i}',
                    'username': f'tech_guru_{i}',
                    'name': f'Tech Influencer {i}',
                    'created_at': (now - timedelta(days=i*20)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'public_metrics': {
                        'followers_count': random.randint(5000, 500000),
                        'following_count': random.randint(100, 1000),
                        'tweet_count': random.randint(1000, 20000),
                        'listed_count': random.randint(50, 500)
                    },
                    'verified': True
                })
            return {'data': mock_users, 'meta': {'result_count': 15}}

        # PRODUCTION LOGIC - Cache First
        db = get_database()
        
        if not force_refresh and not pagination_token and db.is_connected():
            age = db.get_cache_age(user_id, 'following')
            if age < 60: # 60 minutes TTL
                cached = db.get_saved_connections(user_id, 'following')
                if cached:
                    st.caption(f"👥 Using database following (Checked {int(age)}m ago)")
                    return {'data': cached, 'meta': {'result_count': len(cached)}}

        # Use the API adapter to fetch following
        try:
            result = self._api.get_following(user_id, max_results=max_results)
            
            if result and 'data' in result:
                # Save to database
                if db.is_connected() and not pagination_token:
                    db.save_live_connections(user_id, result['data'], 'following')
                    db.save_live_api_response(user_id, 'following', {'count': len(result['data'])})
                return result
            
            # Fallback to database
            if db.is_connected():
                cached = db.get_saved_connections(user_id, 'following')
                if cached:
                    st.info(f"📦 Loaded {len(cached)} following from database.")
                    return {'data': cached, 'meta': {'result_count': len(cached)}}
            return None
            
        except Exception as e:
            st.error(f"Error fetching following: {e}")
            if db.is_connected():
                cached = db.get_saved_connections(user_id, 'following')
                if cached:
                    return {'data': cached, 'meta': {'result_count': len(cached)}}
            return None


def display_live_metrics(user_info):
    """
    Display live metrics for authenticated user
    
    Args:
        user_info: User information with access_token and/or username
    """
    access_token = user_info.get('access_token')
    username = user_info.get('username')
    use_official = os.getenv('TWITTER_OFFICIAL', 'false').lower() == 'true'
    
    # For official API, we need access_token
    # For Rettiwt API, we need username
    if use_official and not access_token:
        st.warning("⚠️ No access token available. Please sign in again.")
        return
    
    if not use_official and not username:
        st.warning("⚠️ Username required for Rettiwt API mode.")
        return
    
    api = TwitterLiveAPI(access_token=access_token, username=username)
    
    # Show current API mode
    api_mode = get_api_mode()
    st.sidebar.info(f"🔌 API Mode: {api_mode}")
    
    st.subheader("📊 Live Twitter Metrics")
    
    with st.spinner("Fetching your latest data from Twitter..."):
        # Get weekly performance
        weekly_data = api.get_weekly_performance()
        
        if weekly_data:
            st.markdown("### 📈 Last 7 Days Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Tweets Posted",
                    f"{weekly_data['tweets_count']:,}",
                    help="Number of tweets in the last 7 days"
                )
            
            with col2:
                st.metric(
                    "Total Impressions",
                    f"{weekly_data['total_impressions']:,}",
                    help="Total views on your tweets"
                )
            
            with col3:
                st.metric(
                    "Total Engagement",
                    f"{weekly_data['total_engagement']:,}",
                    help="Likes + Retweets + Replies + Quotes"
                )
            
            with col4:
                st.metric(
                    "Engagement Rate",
                    f"{weekly_data['avg_engagement_rate']}%",
                    help="Engagement / Impressions"
                )
            
            # Engagement breakdown
            st.markdown("### 💬 Engagement Breakdown")
            
            breakdown = weekly_data.get('breakdown', {})
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("❤️ Likes", f"{breakdown.get('likes', 0):,}")
            with col2:
                st.metric("🔄 Retweets", f"{breakdown.get('retweets', 0):,}")
            with col3:
                st.metric("💬 Replies", f"{breakdown.get('replies', 0):,}")
            with col4:
                st.metric("📝 Quotes", f"{breakdown.get('quotes', 0):,}")
        
        # Get recent tweets
        user_id = api.get_my_user_id()
        if user_id:
            recent_tweets = api.get_recent_tweets(user_id, max_results=5)
            
            if recent_tweets:
                st.markdown("### 🐦 Your Latest Tweets")
                
                for tweet in recent_tweets[:5]:
                    metrics = tweet.get('public_metrics', {})
                    
                    with st.expander(f"📝 {tweet.get('text', '')[:100]}..."):
                        st.markdown(f"**Full Text:** {tweet.get('text', '')}")
                        st.markdown(f"**Posted:** {tweet.get('created_at', '')}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("👁️ Impressions", f"{metrics.get('impression_count', 0):,}")
                        with col2:
                            st.metric("❤️ Likes", f"{metrics.get('like_count', 0):,}")
                        with col3:
                            st.metric("🔄 Retweets", f"{metrics.get('retweet_count', 0):,}")
                        with col4:
                            st.metric("💬 Replies", f"{metrics.get('reply_count', 0):,}")
