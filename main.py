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

from dotenv import load_dotenv
import os

# Load/Reload Environment Variables
load_dotenv(override=True)

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

# Detect Environment Switch logic
current_env = os.getenv('APP_ENV', 'production').lower()
if 'app_env_cache' in st.session_state:
    if st.session_state.app_env_cache != current_env:
        # Environment changed! Clear data cache.
        if 'live_tweets_cache' in st.session_state: del st.session_state.live_tweets_cache
        if 'live_user_id_cache' in st.session_state: del st.session_state.live_user_id_cache
        st.session_state.app_env_cache = current_env
        st.toast(f"Environment changed to {current_env}. Cache cleared.", icon="🔄")
        st.rerun()
else:
    st.session_state.app_env_cache = current_env

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f5f8fa; }
    .stMetric { background-color: white; padding: 10px; border-radius: 5px; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stAppViewContainer"] > div:first-child { width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

# Main Header
col1, col2, col3 = st.columns([1, 2, 1])

# Center Title
with col2:
    st.markdown("<h1 style='text-align: center;'>🐦 Twitter Analytics</h1>", unsafe_allow_html=True)

# Right Profile Section
with col3:
    if is_authenticated():
        user = get_current_user()
        if user:
            # Profile Info
            st.markdown(f"""
                <div style="text-align: right; margin-bottom: 5px;">
                    <img src="{user.get('profile_image_url', '')}" 
                         style="border-radius: 50%; width: 35px; height: 35px; vertical-align: middle; border: 2px solid #1DA1F2;">
                    <span style="margin-left: 8px; font-weight: 600; font-size: 14px;">@{user.get('username', '')}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Logout Button (Right Aligned)
            c_spacer, c_btn = st.columns([2, 1])
            with c_btn:
                if st.button("🚪 Logout", key="header_logout", use_container_width=True):
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
        
        # Refresh button logic
        force_refresh = False
        c1, c2 = st.columns([4, 1])
        with c1: st.caption("Real-time data from your Twitter account")
        with c2:
            if st.button("🔄 Refresh", help="Fetch latest data from Twitter"):
                if 'live_tweets_cache' in st.session_state: del st.session_state.live_tweets_cache
                if 'live_user_id_cache' in st.session_state: del st.session_state.live_user_id_cache
                force_refresh = True
        
        api = TwitterLiveAPI(access_token, refresh_token=user.get('refresh_token'))
        
        # Check cache
        use_cache = 'live_tweets_cache' in st.session_state and 'live_user_id_cache' in st.session_state
        
        if use_cache and not force_refresh:
            user_id = st.session_state.live_user_id_cache
            recent_tweets = st.session_state.live_tweets_cache
            st.caption("📦 Using session cache")
        else:
            with st.spinner("📡 Fetching your latest Twitter data..."):
                user_id = api.get_my_user_id()
                if user_id:
                    # Pass force_refresh to ignore DB TTL settings
                    recent_tweets = api.get_recent_tweets(user_id, max_results=50, force_refresh=force_refresh)
                    st.session_state.live_user_id_cache = user_id
                    st.session_state.live_tweets_cache = recent_tweets
                else:
                    recent_tweets = []
        
        # Try to get archive stats as a "secondary indicator" if live data is missing
        archive_stats = None
        db = get_database()
        if db.is_connected():
            uploads = db.get_user_uploads(user_id, limit=1)
            if uploads:
                archive_stats = uploads[0].get('stats', {})

        # === START DASHBOARD SKELETON ===
        st.markdown("---")
        
        # 1. PROFILE / ACCOUNT SUMMARY (Row 1)
        if not recent_tweets and archive_stats:
            st.info("💡 Note: Twitter API is currently rate-limited. Showing last known stats from your archive.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Tweets", archive_stats.get('total_tweets', 0))
            c2.metric("Followers", archive_stats.get('total_followers', 0))
            c3.metric("Following", archive_stats.get('total_following', 0))
            c4.metric("Historic Likes", archive_stats.get('total_likes', 0))
        
        # 2. ACCOUNT OVERVIEW CHART
        st.markdown("### 📈 Account Overview")
        if not recent_tweets:
            st.warning("📭 No recent live tweets found (Likely due to API Rate Limit).")
            # Show an empty/placeholder chart or message
            st.info("The chart will appear here once your Twitter API quota resets or you refresh data.")
        else:
            # Data Processing for Chart
            import plotly.express as px
            import plotly.graph_objects as go
            
            tweets_for_chart = recent_tweets 
            if tweets_for_chart:
                # Convert to DataFrame
                chart_data = []
                for t in tweets_for_chart:
                    metrics = t['public_metrics']
                    created = t['created_at'].split('T')[0] # YYYY-MM-DD
                    chart_data.append({
                        'Date': created,
                        'Impressions': metrics.get('impression_count', 0),
                        'Likes': metrics.get('like_count', 0),
                        'Retweets': metrics.get('retweet_count', 0),
                        'Replies': metrics.get('reply_count', 0),
                        'Quotes': metrics.get('quote_count', 0),
                        'Bookmarks': metrics.get('bookmark_count', 0),
                        'Engagement': (metrics.get('like_count', 0) + 
                                       metrics.get('retweet_count', 0) + 
                                       metrics.get('reply_count', 0) + 
                                       metrics.get('quote_count', 0) +
                                       metrics.get('bookmark_count', 0)),
                        'Tweets': 1
                    })
                
                df_chart = pd.DataFrame(chart_data)
                df_chart['Date'] = pd.to_datetime(df_chart['Date'])
                
                # Filters
                c_filter1, c_filter2 = st.columns([1, 4])
                with c_filter1:
                    time_range = st.radio("Time Range", ["7D", "2W"], horizontal=True, label_visibility="collapsed")
                with c_filter2:
                    available_metrics = ["Impressions", "Likes", "Retweets", "Replies", "Quotes", "Bookmarks", "Engagement"]
                    metric_choice = st.selectbox("Select Metric to Chart", available_metrics, index=0, label_visibility="collapsed")
                
                # Filter Data by Date
                days = 7 if time_range == "7D" else 14
                end_date = pd.Timestamp.now().normalize()
                start_date = end_date - pd.Timedelta(days=days-1)
                
                df_filtered = df_chart[df_chart['Date'] >= start_date]
                
                # Group by Date
                df_grouped = df_filtered.groupby('Date').sum().reset_index()
                
                # Ensure ALL dates in range are present (fill missing with 0)
                all_dates = pd.date_range(start=start_date, end=end_date)
                df_complete = pd.DataFrame({'Date': all_dates})
                df_grouped = pd.merge(df_complete, df_grouped, on='Date', how='left').fillna(0)
                
                # Format Date as String for clean X-axis (e.g., "Dec 15")
                df_grouped['DateStr'] = df_grouped['Date'].dt.strftime('%b %d')
                
                # Stats Cards Calculation
                total_tweets = int(df_grouped['Tweets'].sum())
                total_metric = int(df_grouped[metric_choice].sum())
                secondary_metric_label = "Total Likes"
                secondary_metric_value = int(df_grouped['Likes'].sum())
                
                if metric_choice == "Impressions":
                    secondary_metric_label = "Total Impressions"
                    secondary_metric_value = total_metric
                elif metric_choice == "Engagement":
                    secondary_metric_label = "Total Engagement"
                    secondary_metric_value = total_metric
                
                avg_val = df_grouped[metric_choice].mean() if not df_grouped.empty else 0
                
                # Render Stats Cards
                st.markdown("""
                    <style>
                    .live-stat-card {
                        background-color: white;
                        border: 1px solid #e1e8ed;
                        border-radius: 10px;
                        padding: 15px;
                        text-align: center;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                    }
                    .live-stat-label { font-size: 11px; color: #657786; letter-spacing: 0.5px; text-transform: uppercase; }
                    .live-stat-value { font-size: 24px; font-weight: 700; color: #14171a; }
                    </style>
                """, unsafe_allow_html=True)
                
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1: st.markdown(f'<div class="live-stat-card"><div class="live-stat-label">Tweets In Period</div><div class="live-stat-value">{total_tweets}</div></div>', unsafe_allow_html=True)
                with sc2: st.markdown(f'<div class="live-stat-card"><div class="live-stat-label">{secondary_metric_label}</div><div class="live-stat-value">{secondary_metric_value:,}</div></div>', unsafe_allow_html=True)
                with sc3: st.markdown(f'<div class="live-stat-card"><div class="live-stat-label">Total {metric_choice}</div><div class="live-stat-value">{total_metric:,}</div></div>', unsafe_allow_html=True)
                with sc4: st.markdown(f'<div class="live-stat-card"><div class="live-stat-label">Avg {metric_choice}/Day</div><div class="live-stat-value">{avg_val:.1f}</div></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Render Chart
                if not df_grouped.empty:
                    y_col = metric_choice
                    fig = px.bar(
                        df_grouped, 
                        x='DateStr', 
                        y=y_col,
                        title=f"{metric_choice} Distribution",
                        color_discrete_sequence=['#1DA1F2']
                    )
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=False, 
                            title="", 
                            type='category', # Force categorical to show every label
                            tickmode='linear'
                        ),
                        yaxis=dict(showgrid=True, gridcolor='#F5F8FA', title=metric_choice),
                        margin=dict(l=0, r=0, t=30, b=0),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for this time range.")
            else:
                st.warning("No live tweets found to display.")
            
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
            
            st.markdown("---")
            
            # === FOLLOWERS & FOLLOWING SECTION ===
            st.markdown("### 👥 Connections")
            
            tab_followers, tab_following, tab_audit = st.tabs(["Followers", "Following", "Relationship Audit"])
            
            # --- Followers Tab ---
            with tab_followers:
                if 'my_followers_list' in st.session_state and st.session_state.my_followers_list:
                    followers_data = st.session_state.my_followers_list
                    st.success(f"Loaded {len(followers_data)} followers")
                    
                    # Convert to DataFrame for display
                    df_followers = pd.DataFrame(followers_data)
                    if not df_followers.empty:
                        # Select and rename columns if they exist
                        cols_to_show = ['username', 'name', 'created_at']
                        if 'public_metrics' in df_followers.columns:
                            # Flatten metrics for clean display
                            display_data = []
                            for f in followers_data:
                                metrics = f.get('public_metrics', {})
                                display_data.append({
                                    'Username': f.get('username'),
                                    'Name': f.get('name'),
                                    'Followers': metrics.get('followers_count', 0),
                                    'Following': metrics.get('following_count', 0),
                                    'Joined': f.get('created_at', '').split('T')[0]
                                })
                            df_display = pd.DataFrame(display_data)
                            st.dataframe(df_display, use_container_width=True)
                        else:
                            st.dataframe(df_followers[cols_to_show], use_container_width=True)
                    
                    if st.button("🔄 Refresh Followers List"):
                        del st.session_state.my_followers_list
                        st.rerun()
                else:
                    st.info("Fetch your followers list from Twitter (Limit: 1000 most recent)")
                    if st.button("📥 Fetch Followers"):
                        with st.spinner("Fetching followers... This may take a moment."):
                            result = api.get_followers(user_id, max_results=1000)
                            if result and 'data' in result:
                                st.session_state.my_followers_list = result['data']
                                st.rerun()
                            elif result and 'errors' in result:
                                st.error(f"Error: {result['errors'][0].get('message')}")
                            else:
                                st.warning("No followers found or rate limit reached.")

            # --- Following Tab ---
            with tab_following:
                if 'my_following_list' in st.session_state and st.session_state.my_following_list:
                    following_data = st.session_state.my_following_list
                    st.success(f"Loaded {len(following_data)} following")
                    
                    # Display logic
                    display_data = []
                    for f in following_data:
                        metrics = f.get('public_metrics', {})
                        display_data.append({
                            'Username': f.get('username'),
                            'Name': f.get('name'),
                            'Followers': metrics.get('followers_count', 0),
                            'Following': metrics.get('following_count', 0),
                            'Joined': f.get('created_at', '').split('T')[0]
                        })
                    df_display = pd.DataFrame(display_data)
                    st.dataframe(df_display, use_container_width=True)
                    
                    if st.button("🔄 Refresh Following List"):
                        del st.session_state.my_following_list
                        st.rerun()
                else:
                    st.info("Fetch accounts you follow (Limit: 1000 most recent)")
                    if st.button("📥 Fetch Following"):
                        with st.spinner("Fetching following list..."):
                            result = api.get_following(user_id, max_results=1000)
                            if result and 'data' in result:
                                st.session_state.my_following_list = result['data']
                                st.rerun()
                            elif result and 'errors' in result:
                                st.error(f"Error: {result['errors'][0].get('message')}")
                            else:
                                st.warning("No connections found or rate limit reached.")
            
            # --- Relationship Audit Tab ---
            with tab_audit:
                st.markdown("### 🎯 Relationship Audit")
                st.caption("Identify people who don't follow you back and your fans.")
                
                has_followers = 'my_followers_list' in st.session_state and st.session_state.my_followers_list
                has_following = 'my_following_list' in st.session_state and st.session_state.my_following_list
                
                if has_followers and has_following:
                    # Perform Audit
                    followers_list = st.session_state.my_followers_list
                    following_list = st.session_state.my_following_list
                    
                    # Extract IDs
                    follower_ids = {u['id'] for u in followers_list}
                    following_ids = {u['id'] for u in following_list}
                    
                    # Create Lookup Maps for User Data
                    followers_map = {u['id']: u for u in followers_list}
                    following_map = {u['id']: u for u in following_list}
                    
                    # Set Operations
                    not_followed_back_ids = following_ids - follower_ids
                    fans_ids = follower_ids - following_ids
                    
                    # Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Not Following Back", len(not_followed_back_ids))
                    c2.metric("Fans (Not Followed)", len(fans_ids))
                    c3.metric("Mutuals", len(follower_ids & following_ids))
                    
                    st.markdown("---")
                    
                    # Not Followed Back Section
                    if not_followed_back_ids:
                        st.subheader(f"⚠️ Not Following You Back ({len(not_followed_back_ids)})")
                        st.caption("You follow these accounts, but they don't follow you back.")
                        
                        nfb_data = []
                        for uid in not_followed_back_ids:
                            user_obj = following_map.get(uid)
                            if user_obj:
                                metrics = user_obj.get('public_metrics', {})
                                nfb_data.append({
                                    'Username': user_obj.get('username'),
                                    'Name': user_obj.get('name'),
                                    'Followers': metrics.get('followers_count', 0),
                                    'Following': metrics.get('following_count', 0),
                                    'Profile': f"https://twitter.com/{user_obj.get('username')}"
                                })
                        
                        df_nfb = pd.DataFrame(nfb_data)
                        st.dataframe(
                            df_nfb, 
                            column_config={
                                "Profile": st.column_config.LinkColumn("Profile Link")
                            },
                            use_container_width=True
                        )
                    else:
                        st.success("✅ Everyone you follow follows you back!")
                        
                    st.markdown("---")
                    
                    # Fans Section
                    if fans_ids:
                        st.subheader(f"🌟 Fans You Don't Follow Back ({len(fans_ids)})")
                        fans_data = []
                        for uid in fans_ids:
                            user_obj = followers_map.get(uid)
                            if user_obj:
                                metrics = user_obj.get('public_metrics', {})
                                fans_data.append({
                                    'Username': user_obj.get('username'),
                                    'Name': user_obj.get('name'),
                                    'Followers': metrics.get('followers_count', 0),
                                    'Following': metrics.get('following_count', 0),
                                    'Profile': f"https://twitter.com/{user_obj.get('username')}"
                                })
                        
                        df_fans = pd.DataFrame(fans_data)
                        st.dataframe(
                            df_fans, 
                            column_config={
                                "Profile": st.column_config.LinkColumn("Profile Link")
                            },
                            use_container_width=True
                        )
                    
                else:
                    st.info("⚠️ Data Missing: Please fetch BOTH 'Followers' and 'Following' lists in the other tabs to perform this audit.")
                    if st.button("📥 Fetch Everything Now"):
                        with st.spinner("Fetching all connection data..."):
                            # Fetch both
                            if not has_followers:
                                res_f = api.get_followers(user_id, max_results=1000)
                                if res_f and 'data' in res_f:
                                    st.session_state.my_followers_list = res_f['data']
                            
                            if not has_following:
                                res_fol = api.get_following(user_id, max_results=1000)
                                if res_fol and 'data' in res_fol:
                                    st.session_state.my_following_list = res_fol['data']
                            
                            st.rerun()

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

# === ARCHIVE ANALYSIS LINK ===
_, col2, _ = st.columns([1, 2, 1])
if col2.button("🚀 Go to Archive Analysis & Upload", type="primary", use_container_width=True):
    st.switch_page("pages/archive_analysis.py")

st.markdown("<br><br><div style='text-align: center; color: #8899a6;'>Twitter Analytics Dashboard v2.0</div>", unsafe_allow_html=True)
