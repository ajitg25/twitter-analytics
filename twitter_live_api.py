"""Twitter Live API - Fetch real-time data using OAuth access token"""

import requests
from datetime import datetime, timedelta
import streamlit as st


class TwitterLiveAPI:
    """Fetch live Twitter data using OAuth 2.0 access token"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            'Authorization': f'Bearer {access_token}'
        }
    
    def get_my_user_id(self):
        """Get the authenticated user's Twitter ID"""
        url = f"{self.base_url}/users/me"
        params = {'user.fields': 'id,username,name'}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get('data', {}).get('id')
            else:
                st.error(f"Failed to get user ID: {response.text}")
                return None
        except Exception as e:
            st.error(f"Error getting user ID: {e}")
            return None
    
    def get_recent_tweets(self, user_id, max_results=10):
        """
        Get user's recent tweets
        
        Args:
            user_id: Twitter user ID
            max_results: Number of tweets to fetch (5-100)
        
        Returns:
            List of tweet objects with metrics
        """
        url = f"{self.base_url}/users/{user_id}/tweets"
        
        params = {
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,public_metrics,text,author_id',
            'expansions': 'author_id',
            'user.fields': 'username,name,profile_image_url'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            elif response.status_code == 401:
                st.error("🔑 Access token expired or invalid. Please sign in again.")
                return []
            elif response.status_code == 429:
                st.warning("⚠️ Rate limit reached. Please try again later.")
                return []
            else:
                st.error(f"Failed to fetch tweets: {response.text}")
                return []
                
        except Exception as e:
            st.error(f"Error fetching tweets: {e}")
            return []
    
    def get_tweet_metrics_summary(self, tweets):
        """
        Calculate summary metrics from tweets
        
        Args:
            tweets: List of tweet objects
        
        Returns:
            Dictionary with summary metrics
        """
        if not tweets:
            return {
                'total_tweets': 0,
                'total_impressions': 0,
                'total_likes': 0,
                'total_retweets': 0,
                'total_replies': 0,
                'total_quotes': 0,
                'avg_impressions': 0,
                'avg_engagement_rate': 0
            }
        
        total_impressions = 0
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_quotes = 0
        
        for tweet in tweets:
            metrics = tweet.get('public_metrics', {})
            total_impressions += metrics.get('impression_count', 0)
            total_likes += metrics.get('like_count', 0)
            total_retweets += metrics.get('retweet_count', 0)
            total_replies += metrics.get('reply_count', 0)
            total_quotes += metrics.get('quote_count', 0)
        
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
        """
        Get performance metrics for the last 7 days
        
        Returns:
            Dictionary with weekly metrics
        """
        user_id = self.get_my_user_id()
        if not user_id:
            return None
        
        # Fetch recent tweets (up to 100)
        tweets = self.get_recent_tweets(user_id, max_results=100)
        
        if not tweets:
            return {
                'period': 'Last 7 days',
                'tweets_count': 0,
                'total_impressions': 0,
                'total_engagement': 0,
                'avg_engagement_rate': 0
            }
        
        # Filter tweets from last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_tweets = []
        
        for tweet in tweets:
            created_at = datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if created_at >= seven_days_ago:
                recent_tweets.append(tweet)
        
        # Calculate metrics
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
        """
        Find the top performing tweet by engagement
        
        Args:
            tweets: List of tweet objects
        
        Returns:
            Top performing tweet object
        """
        if not tweets:
            return None
        
        top_tweet = max(tweets, key=lambda t: (
            t.get('public_metrics', {}).get('like_count', 0) +
            t.get('public_metrics', {}).get('retweet_count', 0) +
            t.get('public_metrics', {}).get('reply_count', 0)
        ))
        
        return top_tweet


def display_live_metrics(user_info):
    """
    Display live metrics for authenticated user
    
    Args:
        user_info: User information with access_token
    """
    access_token = user_info.get('access_token')
    
    if not access_token:
        st.warning("⚠️ No access token available. Please sign in again.")
        return
    
    api = TwitterLiveAPI(access_token)
    
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
