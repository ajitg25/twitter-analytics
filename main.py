import streamlit as st
import pandas as pd
from pathlib import Path
from auth import (
    init_auth_state, 
    handle_oauth_callback, 
    is_authenticated, 
    get_current_user,
    logout,
    get_twitter_auth_url
)
from database import get_database

# Page config (Must be first)
st.set_page_config(
    page_title="Twitter Analytics Dashboard", 
    page_icon="🐦", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize authentication state
init_auth_state()
handle_oauth_callback()

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f5f8fa; }
    .stMetric { background-color: white; padding: 10px; border-radius: 5px; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stAppViewContainer"] > div:first-child { width: 100% !important; }
    
    /* CTA Box */
    .cta-box {
        background: white;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #e1e8ed;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Main Header
col1, col2, col3 = st.columns([2, 3, 2])
with col1:
    st.markdown("<h1 style='text-align: left;'>🐦 Twitter Analytics</h1>", unsafe_allow_html=True)

with col3:
    if is_authenticated():
        user = get_current_user()
        if user:
            st.markdown(f"""
                <div style="text-align: right; padding: 10px;">
                    <img src="{user.get('profile_image_url', '')}" 
                         style="border-radius: 50%; width: 40px; height: 40px; vertical-align: middle;">
                    <span style="margin-left: 10px; font-weight: 600;">@{user.get('username', '')}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Logout", key="header_logout"):
                logout()
                st.rerun()
    else:
        auth_url = get_twitter_auth_url()
        if auth_url:
            st.markdown(f"""
                <div style="text-align: right; padding: 10px;">
                    <a href="{auth_url}" target="_self" style="
                        background: linear-gradient(135deg, #1DA1F2 0%, #0d8bd9 100%);
                        color: white; padding: 10px 20px; border-radius: 25px;
                        text-decoration: none; font-weight: 600; display: inline-block;
                        box-shadow: 0 4px 6px rgba(29, 161, 242, 0.3);
                    ">🐦 Sign in with X</a>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# === LIVE METRICS SECTION ===
if is_authenticated():
    user = get_current_user()
    access_token = user.get('access_token')
    
    if access_token:
        from twitter_live_api import TwitterLiveAPI
        
        st.markdown("## 📊 Your Live Twitter Analytics")
        
        # Refresh button
        c1, c2 = st.columns([4, 1])
        with c1: st.caption("Real-time data from your Twitter account")
        with c2:
            if st.button("🔄 Refresh", help="Fetch latest data from Twitter"):
                if 'live_tweets_cache' in st.session_state: del st.session_state.live_tweets_cache
                if 'live_user_id_cache' in st.session_state: del st.session_state.live_user_id_cache
                st.rerun()
        
        api = TwitterLiveAPI(access_token)
        
        # Check cache
        use_cache = 'live_tweets_cache' in st.session_state and 'live_user_id_cache' in st.session_state
        
        if use_cache:
            user_id = st.session_state.live_user_id_cache
            recent_tweets = st.session_state.live_tweets_cache
            st.caption("📦 Using cached data")
        else:
            with st.spinner("📡 Fetching your latest Twitter data..."):
                user_id = api.get_my_user_id()
                if user_id:
                    recent_tweets = api.get_recent_tweets(user_id, max_results=50)
                    st.session_state.live_user_id_cache = user_id
                    st.session_state.live_tweets_cache = recent_tweets
                else:
                    recent_tweets = []
        
        if user_id and recent_tweets:
            # Calculate metrics
            metrics = api.get_tweet_metrics_summary(recent_tweets)
            
            # Weekly data logic
            from datetime import datetime, timedelta
            seven_days_ago = datetime.now() - timedelta(days=7)
            weekly_tweets = [t for t in recent_tweets if datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ') >= seven_days_ago]
            weekly_metrics = api.get_tweet_metrics_summary(weekly_tweets)
            
            # Overview
            st.markdown("### 📈 Overview (Last 50 Tweets)")
            cols = st.columns(5)
            cols[0].metric("Total Tweets", f"{metrics['total_tweets']:,}")
            cols[1].metric("Total Likes", f"{metrics['total_likes']:,}")
            cols[2].metric("Total Retweets", f"{metrics['total_retweets']:,}")
            cols[3].metric("Total Replies", f"{metrics['total_replies']:,}")
            avg_eng = (metrics['total_likes'] + metrics['total_retweets']) // metrics['total_tweets'] if metrics['total_tweets'] > 0 else 0
            cols[4].metric("Avg Engagement", f"{avg_eng}")
            
            st.markdown("---")
            
            # Weekly
            if weekly_metrics['total_tweets'] > 0:
                st.markdown("### 📅 Last 7 Days Performance")
                cols = st.columns(4)
                cols[0].metric("Tweets This Week", f"{weekly_metrics['total_tweets']:,}")
                cols[1].metric("Weekly Engagement", f"{weekly_metrics['total_likes'] + weekly_metrics['total_retweets'] + weekly_metrics['total_replies']:,}")
                cols[2].metric("Likes This Week", f"{weekly_metrics['total_likes']:,}")
                cols[3].metric("Retweets This Week", f"{weekly_metrics['total_retweets']:,}")
                st.markdown("---")

            # Top Tweets
            st.markdown("### 🔥 Top Performing Tweets")
            sorted_tweets = sorted(recent_tweets, key=lambda t: sum([t['public_metrics'][k] for k in ['like_count', 'retweet_count', 'reply_count']]), reverse=True)
            
            for idx, tweet in enumerate(sorted_tweets[:3], 1):
                m = tweet['public_metrics']
                total = m['like_count'] + m['retweet_count'] + m['reply_count']
                with st.expander(f"#{idx} - {tweet['text'][:60]}... ({total} engagements)"):
                    st.info(tweet['text'])
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Likes", m['like_count'])
                    c2.metric("Retweets", m['retweet_count'])
                    c3.metric("Replies", m['reply_count'])
                    if tweet.get('id') and user.get('username'):
                        st.markdown(f"[🔗 View on Twitter](https://twitter.com/{user['username']}/status/{tweet['id']})")

else:
    # Not authenticated landing
    st.info("👋 Sign in above to see your live Twitter stats instantly!")
    st.markdown("""
    ### ✨ What you get:
    - **Real-time Metrics**: Likes, retweets, and engagement rates.
    - **Weekly Performance**: Track your growth over the last 7 days.
    - **Top Tweets**: Identify your best performing content.
    """)

st.markdown("---")

# === ARCHIVE ANALYSIS CTA ===
st.markdown("""
    <div class="cta-box">
        <h2>📂 Want Deeper Insights?</h2>
        <p style="color: #657786; font-size: 16px;">
            Upload your Twitter Archive to analyze your complete history, 
            find out who doesn't follow you back, and visualize your growth over years.
        </p>
    </div>
""", unsafe_allow_html=True)

_, col2, _ = st.columns([1, 2, 1])
if col2.button("🚀 Go to Archive Analysis & Upload", type="primary", use_container_width=True):
    st.switch_page("pages/archive_analysis.py")

st.markdown("<br><br><div style='text-align: center; color: #8899a6;'>Twitter Analytics Dashboard v2.0</div>", unsafe_allow_html=True)
