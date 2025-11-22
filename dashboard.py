import json
import re
from datetime import datetime
from collections import Counter
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st


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


def main():
    st.set_page_config(page_title="Twitter Analytics Dashboard", page_icon="🐦", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            background-color: #f5f8fa;
        }
        .stMetric {
            background-color: white;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🐦 Twitter Analytics Dashboard")
    st.markdown("---")
    
    # File path input
    default_path = "/Users/ajit.gupta/Desktop/HHpersonal/projects/twitter-analytics/twitter-2025-11-18-753643d946ad97c385806a0b57293cc805c30525ff3f1f515cc2d4bd40112f50"
    archive_path = st.text_input("Enter Twitter Archive Path:", value=default_path)
    
    if not Path(archive_path).exists():
        st.error("❌ Invalid path. Please enter a valid Twitter archive folder path.")
        return
    
    # Load data
    with st.spinner("Loading your Twitter data..."):
        dashboard = TwitterDashboard(archive_path)
        data = dashboard.load_all_data()
    
    # Display account info
    if 'account' in data:
        account = data['account']
        st.header(f"Welcome, @{account.get('username', 'User')}!")
        st.caption(f"Account created: {account.get('createdAt', 'N/A')[:10]}")
    
    st.markdown("---")
    
    # Key Metrics
    st.subheader("📊 Key Metrics")
    metrics = dashboard.create_engagement_metrics(data)
    
    cols = st.columns(4)
    cols[0].metric("Followers", metrics['Followers'])
    cols[1].metric("Following", metrics['Following'])
    cols[2].metric("Mutual Connections", metrics['Mutual Connections'])
    cols[3].metric("Engagement Rate", metrics['Engagement Rate'])
    
    cols2 = st.columns(3)
    cols2[0].metric("Total Tweets", metrics['Total Tweets'])
    cols2[1].metric("Total Likes", metrics['Total Likes'])
    cols2[2].metric("Follower Ratio", metrics['Follower Ratio'])
    
    st.markdown("---")
    
    # Insights Section
    st.subheader("💡 Insights & Recommendations")
    insights = dashboard.get_insights(data)
    
    for insight in insights:
        if insight['type'] == 'success':
            st.success(f"**{insight['title']}**\n\n{insight['message']}")
        elif insight['type'] == 'warning':
            st.warning(f"**{insight['title']}**\n\n{insight['message']}")
        else:
            st.info(f"**{insight['title']}**\n\n{insight['message']}")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Follower Analysis")
        fig = dashboard.create_follower_chart(data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏷️ Top Hashtags")
        fig = dashboard.create_hashtag_chart(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hashtags found in your content.")
    
    # Tweet Timeline
    st.subheader("📈 Tweet Activity Timeline")
    fig = dashboard.create_tweet_timeline(data)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tweet timeline data available.")
    
    # Activity Heatmap
    st.subheader("🔥 Activity Heatmap")
    fig = dashboard.create_activity_heatmap(data)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for activity heatmap.")
    
    st.markdown("---")
    
    # Detailed Lists
    with st.expander("📋 View Detailed Lists"):
        tab1, tab2, tab3 = st.tabs(["Followers", "Following", "Mutual Connections"])
        
        followers = data.get('followers', [])
        following = data.get('following', [])
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        mutual_ids = follower_ids & following_ids
        
        with tab1:
            st.write(f"Total Followers: {len(followers)}")
            for f in followers[:20]:  # Show first 20
                st.write(f"- User ID: {f['follower']['accountId']}")
        
        with tab2:
            st.write(f"Total Following: {len(following)}")
            for f in following[:20]:  # Show first 20
                st.write(f"- User ID: {f['following']['accountId']}")
        
        with tab3:
            st.write(f"Total Mutual Connections: {len(mutual_ids)}")
            for uid in list(mutual_ids)[:20]:  # Show first 20
                st.write(f"- User ID: {uid}")


if __name__ == "__main__":
    main()

