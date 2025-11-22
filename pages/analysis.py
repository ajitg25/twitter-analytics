import streamlit as st
import pandas as pd
from pathlib import Path
import os
from main import TwitterDashboard, fetch_usernames_from_api

# Page config
st.set_page_config(page_title="Twitter Analytics - Analysis", page_icon="📊", layout="wide")

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

st.title("📊 Twitter Analytics Dashboard")

# Check if data is loaded
if 'twitter_data' not in st.session_state or 'dashboard' not in st.session_state:
    st.error("❌ No data found. Please upload your Twitter archive first.")
    st.info("👆 Go back to the main page to upload your data.")
    if st.button("🔙 Go to Upload Page"):
        # Use os.path.relpath for cross-platform compatibility
        main_page_path = os.path.relpath("main.py")
        st.switch_page(main_page_path)
    st.stop()

# Get data from session state
data = st.session_state.twitter_data
dashboard = st.session_state.dashboard

# Display account info
if 'account' in data:
    account = data['account']
    st.header(f"Welcome, @{account.get('username', 'User')}!")
    st.caption(f"Account created: {account.get('createdAt', 'N/A')[:10]}")

# ⚡ FOCUS: Follow-Back Analysis Buttons
st.markdown("### 🎯 Quick Actions")
st.caption("✨ Real @usernames will be fetched automatically from Twitter API")

followers = data.get('followers', [])
following = data.get('following', [])
follower_ids = {f['follower']['accountId'] for f in followers}
following_ids = {f['following']['accountId'] for f in following}

not_followed_back = following_ids - follower_ids  # You follow, they don't
followers_not_following_back = follower_ids - following_ids  # They follow, you don't

col1, col2 = st.columns(2)

with col1:
    if st.button(f"🔍 Not Following Back ({len(not_followed_back)})", use_container_width=True, type="primary"):
        st.session_state.show_not_followed_back = True
        st.session_state.show_followers_not_following = False

with col2:
    if st.button(f"👥 Followers You Don't Follow ({len(followers_not_following_back)})", use_container_width=True):
        st.session_state.show_followers_not_following = True
        st.session_state.show_not_followed_back = False

# Display selected list
if st.session_state.get('show_not_followed_back', False):
    st.markdown("---")
    st.subheader(f"🔍 Accounts That Don't Follow You Back ({len(not_followed_back)})")
    st.caption("These are accounts you follow, but they don't follow you back")
    
    if len(not_followed_back) > 0:
        # Fetch usernames from Twitter API
        with st.spinner("🔄 Fetching usernames from Twitter API..."):
            usernames_data = fetch_usernames_from_api(
                list(not_followed_back)[:50]
            )
        
        accounts_list = []
        for idx, uid in enumerate(list(not_followed_back)[:50], 1):  # Show first 50
            profile_url = f'https://twitter.com/intent/user?user_id={uid}'
            
            # Get username from API if available
            if uid in usernames_data:
                username = usernames_data[uid]['username']
                display_name = usernames_data[uid]['name']
                username_display = f"{username}\n{display_name}" if display_name else username
            else:
                username_display = '👆 Click profile to view'
            
            accounts_list.append({
                '#': idx,
                'Account ID': uid,
                'Username': username_display,
                'Profile URL': profile_url
            })
        
        df = pd.DataFrame(accounts_list)
        
        # Display dataframe with clickable links
        st.dataframe(
            df,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Account ID": st.column_config.TextColumn("Account ID", width="medium"),
                "Username": st.column_config.TextColumn("Username", width="medium", help="Real usernames fetched from Twitter API"),
                "Profile URL": st.column_config.LinkColumn("View Profile", display_text="Open Profile 🔗", width="medium")
            },
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Download button
            csv_data = pd.DataFrame([
                {'Account ID': uid, 'Profile URL': f'https://twitter.com/intent/user?user_id={uid}'}
                for uid in not_followed_back
            ])
            csv = csv_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full List (CSV)",
                data=csv,
                file_name="not_followed_back.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Copy all URLs button
            all_urls = '\n'.join([f'https://twitter.com/intent/user?user_id={uid}' for uid in not_followed_back])
            st.download_button(
                label="📋 Copy All URLs",
                data=all_urls,
                file_name="profile_urls.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.info(f"💡 **Tip**: Click 'Open Profile 🔗' to view each account. Consider unfollowing inactive accounts to improve your follower ratio.")
        
        if len(not_followed_back) > 50:
            st.warning(f"⚠️ Showing first 50 of {len(not_followed_back)} accounts. Download CSV for the full list.")
    else:
        st.success("✅ Great! Everyone you follow also follows you back!")

if st.session_state.get('show_followers_not_following', False):
    st.markdown("---")
    st.subheader(f"👥 Followers You Don't Follow Back ({len(followers_not_following_back)})")
    st.caption("These accounts follow you, but you don't follow them back")
    
    if len(followers_not_following_back) > 0:
        # Fetch usernames from Twitter API
        with st.spinner("🔄 Fetching usernames from Twitter API..."):
            usernames_data = fetch_usernames_from_api(
                list(followers_not_following_back)[:50]
            )
        
        accounts_list = []
        for idx, uid in enumerate(list(followers_not_following_back)[:50], 1):  # Show first 50
            profile_url = f'https://twitter.com/intent/user?user_id={uid}'
            
            # Get username from API if available
            if uid in usernames_data:
                username = usernames_data[uid]['username']
                display_name = usernames_data[uid]['name']
                username_display = f"{username}\n{display_name}" if display_name else username
            else:
                username_display = '👆 Click profile to view'
            
            accounts_list.append({
                '#': idx,
                'Account ID': uid,
                'Username': username_display,
                'Profile URL': profile_url
            })
        
        df = pd.DataFrame(accounts_list)
        
        # Display dataframe with clickable links
        st.dataframe(
            df,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Account ID": st.column_config.TextColumn("Account ID", width="medium"),
                "Username": st.column_config.TextColumn("Username", width="medium", help="Real usernames fetched from Twitter API"),
                "Profile URL": st.column_config.LinkColumn("View Profile", display_text="Open Profile 🔗", width="medium")
            },
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Download button
            csv_data = pd.DataFrame([
                {'Account ID': uid, 'Profile URL': f'https://twitter.com/intent/user?user_id={uid}'}
                for uid in followers_not_following_back
            ])
            csv = csv_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full List (CSV)",
                data=csv,
                file_name="followers_not_following_back.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Copy all URLs button
            all_urls = '\n'.join([f'https://twitter.com/intent/user?user_id={uid}' for uid in followers_not_following_back])
            st.download_button(
                label="📋 Copy All URLs",
                data=all_urls,
                file_name="profile_urls.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.info(f"💡 **Tip**: Click 'Open Profile 🔗' to view each account. Consider following back engaged followers to build mutual connections.")
        
        if len(followers_not_following_back) > 50:
            st.warning(f"⚠️ Showing first 50 of {len(followers_not_following_back)} accounts. Download CSV for the full list.")
    else:
        st.success("✅ You follow all your followers back!")

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

# Navigation back to upload
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Upload New Archive", use_container_width=True):
        # Clear session state
        if 'twitter_data' in st.session_state:
            del st.session_state.twitter_data
        if 'dashboard' in st.session_state:
            del st.session_state.dashboard
        # Use os.path.relpath for cross-platform compatibility
        main_page_path = os.path.relpath("main.py")
        st.switch_page(main_page_path)

