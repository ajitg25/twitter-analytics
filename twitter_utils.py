"""Shared utilities for Twitter Analytics Dashboard"""

import json
import re
from datetime import datetime
from collections import Counter
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
import requests
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass  # In Streamlit Cloud, use secrets instead

# Twitter API Configuration - Try Streamlit secrets first, then env var
try:
    TWITTER_BEARER_TOKEN = st.secrets.get("TWITTER_BEARER_TOKEN", os.getenv('TWITTER_BEARER_TOKEN'))
except:
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')


def fetch_usernames_from_api(user_ids, bearer_token=None):
    """Fetch usernames from Twitter API v2"""
    # Use provided token or fall back to configured token
    token = bearer_token or TWITTER_BEARER_TOKEN
    
    if not token:
        return {}
    
    usernames = {}
    
    # Twitter API allows up to 100 user IDs per request
    batch_size = 100
    user_id_list = list(user_ids)
    
    for i in range(0, len(user_id_list), batch_size):
        batch = user_id_list[i:i + batch_size]
        ids_param = ','.join(batch)
        
        url = f"https://api.twitter.com/2/users?ids={ids_param}&user.fields=username,name"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for user in data['data']:
                        usernames[user['id']] = {
                            'username': f"@{user['username']}",
                            'name': user.get('name', '')
                        }
            elif response.status_code == 401:
                st.error("🔑 API Error 401: Invalid Bearer Token. Please regenerate your token in Twitter Developer Portal.")
                st.info("Go to https://developer.twitter.com/en/portal/dashboard and regenerate your Bearer Token")
                break
            elif response.status_code == 429:
                st.warning("⚠️ Rate limit reached. Showing partial results.")
                break
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
                break
                
        except Exception as e:
            st.error(f"Error fetching usernames: {str(e)}")
            break
    
    return usernames


class TwitterDashboard:
    """Interactive Twitter Analytics Dashboard"""
    
    def __init__(self, archive_path):
        self.archive_path = Path(archive_path)
        self.data_path = self.archive_path / 'data'
        
    def extract_js_data(self, file_path):
        """Extract data from .js files in Twitter archive format"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'window\.YTD\.\w+\.part\d+\s*=\s*(\[.*\])', content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
        except Exception as e:
            st.error(f"Error reading {file_path}: {e}")
        return []
    
    def load_all_data(self):
        """Load all data from archive"""
        data = {}
        
        # Load followers
        follower_file = self.data_path / 'follower.js'
        if follower_file.exists():
            data['followers'] = self.extract_js_data(follower_file)
        
        # Load following
        following_file = self.data_path / 'following.js'
        if following_file.exists():
            data['following'] = self.extract_js_data(following_file)
        
        # Load tweets
        tweets_file = self.data_path / 'tweets.js'
        if tweets_file.exists():
            data['tweets'] = self.extract_js_data(tweets_file)
        
        # Load likes
        likes_file = self.data_path / 'like.js'
        if likes_file.exists():
            data['likes'] = self.extract_js_data(likes_file)
        
        # Load account info
        account_file = self.data_path / 'account.js'
        if account_file.exists():
            account_data = self.extract_js_data(account_file)
            if account_data:
                data['account'] = account_data[0].get('account', {})
        
        # Load profile
        profile_file = self.data_path / 'profile.js'
        if profile_file.exists():
            profile_data = self.extract_js_data(profile_file)
            if profile_data:
                data['profile'] = profile_data[0].get('profile', {})
        
        return data
    
    def create_follower_chart(self, data):
        """Create follower/following comparison chart"""
        followers = data.get('followers', [])
        following = data.get('following', [])
        
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        mutual = len(follower_ids & following_ids)
        
        # Create pie chart for follower breakdown
        fig = go.Figure(data=[go.Pie(
            labels=['Mutual Follows', 'Followers Only', 'Following Only'],
            values=[
                mutual,
                len(follower_ids) - mutual,
                len(following_ids) - mutual
            ],
            hole=.3,
            marker_colors=['#1DA1F2', '#14171A', '#657786']
        )])
        
        fig.update_layout(
            title='Follower/Following Relationship',
            height=400
        )
        
        return fig
    
    def create_engagement_metrics(self, data):
        """Create key metrics cards"""
        followers = data.get('followers', [])
        following = data.get('following', [])
        tweets = data.get('tweets', [])
        likes = data.get('likes', [])
        
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        mutual = len(follower_ids & following_ids)
        
        ratio = len(followers) / len(following) if len(following) > 0 else 0
        
        return {
            'Followers': len(followers),
            'Following': len(following),
            'Mutual Connections': mutual,
            'Follower Ratio': f"{ratio:.2f}",
            'Total Tweets': len(tweets),
            'Total Likes': len(likes),
            'Engagement Rate': f"{(mutual/len(following)*100 if len(following) > 0 else 0):.1f}%"
        }
    
    def create_tweet_timeline(self, data):
        """Create tweet activity timeline"""
        tweets = data.get('tweets', [])
        
        if not tweets:
            return None
        
        dates = []
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            created_at = tweet.get('created_at')
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    dates.append(dt.date())
                except:
                    pass
        
        if not dates:
            return None
        
        # Count tweets per date
        date_counts = Counter(dates)
        df = pd.DataFrame(list(date_counts.items()), columns=['Date', 'Tweets'])
        df = df.sort_values('Date')
        
        fig = px.line(df, x='Date', y='Tweets', 
                      title='Tweet Activity Over Time',
                      labels={'Tweets': 'Number of Tweets'})
        fig.update_traces(line_color='#1DA1F2')
        
        return fig
    
    def create_activity_heatmap(self, data):
        """Create hourly/daily activity heatmap"""
        tweets = data.get('tweets', [])
        
        if not tweets:
            return None
        
        hours = []
        days = []
        
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            created_at = tweet.get('created_at')
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    hours.append(dt.hour)
                    days.append(dt.strftime('%A'))
                except:
                    pass
        
        if not hours or not days:
            return None
        
        # Create day-hour matrix
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hour_day_counts = Counter(zip(days, hours))
        
        # Create matrix
        matrix = []
        for day in day_order:
            row = [hour_day_counts.get((day, hour), 0) for hour in range(24)]
            matrix.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=list(range(24)),
            y=day_order,
            colorscale='Blues',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title='Tweet Activity Heatmap (Day vs Hour)',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            height=400
        )
        
        return fig
    
    def create_hashtag_chart(self, data):
        """Create top hashtags chart"""
        likes = data.get('likes', [])
        tweets = data.get('tweets', [])
        
        hashtags = []
        
        # Extract from likes
        for like_obj in likes:
            like = like_obj.get('like', {})
            full_text = like.get('fullText', '')
            hashtags.extend(re.findall(r'#(\w+)', full_text))
        
        # Extract from tweets
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            full_text = tweet.get('full_text', '')
            hashtags.extend(re.findall(r'#(\w+)', full_text))
        
        if not hashtags:
            return None
        
        top_hashtags = Counter(hashtags).most_common(10)
        df = pd.DataFrame(top_hashtags, columns=['Hashtag', 'Count'])
        
        fig = px.bar(df, x='Count', y='Hashtag', orientation='h',
                     title='Top 10 Hashtags',
                     labels={'Count': 'Usage Count'})
        fig.update_traces(marker_color='#1DA1F2')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        return fig
    
    def get_insights(self, data):
        """Generate actionable insights"""
        insights = []
        
        followers = data.get('followers', [])
        following = data.get('following', [])
        tweets = data.get('tweets', [])
        
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        mutual = len(follower_ids & following_ids)
        not_followed_back = len(following_ids - follower_ids)
        
        # Insight 1: Follower/Following ratio
        if len(followers) < len(following):
            insights.append({
                'type': 'warning',
                'title': '📉 Low Follower Ratio',
                'message': f'You follow {len(following)} accounts but only have {len(followers)} followers. Consider creating more engaging content.'
            })
        else:
            insights.append({
                'type': 'success',
                'title': '📈 Great Follower Ratio',
                'message': f'You have {len(followers)} followers and follow {len(following)} accounts. Keep up the great content!'
            })
        
        # Insight 2: Unfollowed back
        if not_followed_back > 0:
            insights.append({
                'type': 'info',
                'title': '🔍 One-sided Follows',
                'message': f'{not_followed_back} accounts you follow don\'t follow you back ({(not_followed_back/len(following)*100):.1f}%). You might want to review these connections.'
            })
        
        # Insight 3: Mutual follows
        if mutual > 0:
            insights.append({
                'type': 'success',
                'title': '🤝 Strong Connections',
                'message': f'You have {mutual} mutual connections! These are your most engaged relationships.'
            })
        
        # Insight 4: Tweet activity
        if tweets and len(tweets) > 0:
            insights.append({
                'type': 'info',
                'title': '📝 Content Creation',
                'message': f'You\'ve posted {len(tweets)} tweets. Consistent posting helps grow your audience.'
            })
        
        return insights
    
    def create_account_overview_chart(self, data, metric='likes', days=365):
        """Create account overview bar chart with filters"""
        tweets = data.get('tweets', [])
        
        if not tweets:
            return None, {}
        
        # Filter by date
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days)
        
        processed_data = []
        total_stats = {'tweets': 0, 'likes': 0, 'retweets': 0}
        
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            created_at = tweet.get('created_at')
            
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    date = dt.date()
                    
                    if date >= cutoff_date:
                        likes = int(tweet.get('favorite_count', 0))
                        retweets = int(tweet.get('retweet_count', 0))
                        
                        processed_data.append({
                            'Date': date,
                            'Likes': likes,
                            'Retweets': retweets,
                            'Total Engagement': likes + retweets
                        })
                        
                        total_stats['tweets'] += 1
                        total_stats['likes'] += likes
                        total_stats['retweets'] += retweets
                except:
                    pass
        
        if not processed_data:
            return None, total_stats
            
        df = pd.DataFrame(processed_data)
        
        # Aggregate by date
        daily_df = df.groupby('Date').sum().reset_index()
        
        # Determine y-axis column based on metric
        y_col = 'Likes'
        if metric == 'retweets':
            y_col = 'Retweets'
        elif metric == 'engagement':
            y_col = 'Total Engagement'
            
        # Create bar chart
        fig = px.bar(daily_df, x='Date', y=y_col,
                     title=f'{y_col} Over Time',
                     labels={'Date': '', y_col: ''})
        
        fig.update_traces(marker_color='#1DA1F2', hovertemplate='%{x}<br>%{y}')
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#8899a6',
            title_font_color='white',
            title_font_size=18,
            xaxis=dict(
                showgrid=False,
                tickformat='%b %d'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                zeroline=False
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
            bargap=0.2
        )
        
        return fig, total_stats

    def create_posts_replies_chart(self, data, days=365):
        """Create grouped bar chart for Posts vs Replies"""
        tweets = data.get('tweets', [])
        
        if not tweets:
            return None
        
        # Filter by date
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days)
        
        processed_data = []
        
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            created_at = tweet.get('created_at')
            
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    date = dt.date()
                    
                    if date >= cutoff_date:
                        # Determine type
                        is_reply = 'in_reply_to_status_id' in tweet or tweet.get('full_text', '').startswith('@')
                        is_retweet = tweet.get('retweeted', False) or tweet.get('full_text', '').startswith('RT @')
                        
                        # We only want original posts vs replies (excluding retweets for this specific chart if desired, 
                        # or counting non-replies as posts)
                        if not is_retweet:
                            type_label = 'Replies' if is_reply else 'Posts'
                            
                            processed_data.append({
                                'Date': date,
                                'Type': type_label,
                                'Count': 1
                            })
                except:
                    pass
        
        if not processed_data:
            return None
            
        df = pd.DataFrame(processed_data)
        
        # Aggregate by Date and Type
        daily_df = df.groupby(['Date', 'Type']).count().reset_index()
        
        # Create grouped bar chart
        fig = px.bar(daily_df, x='Date', y='Count', color='Type',
                     barmode='group',
                     title='Posts vs Replies',
                     color_discrete_map={'Posts': '#1DA1F2', 'Replies': '#17BF63'})
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#8899a6',
            title_font_color='white',
            title_font_size=18,
            xaxis=dict(
                showgrid=False,
                tickformat='%b %d',
                title=''
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                zeroline=False,
                title=''
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title=''
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
            bargap=0.2
        )
        
        return fig

