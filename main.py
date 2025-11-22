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
import requests
from urllib.parse import unquote
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

def guide_section():
    """Show collapsible guide section"""
    st.markdown("---")
    
    # Eye-catching banner that's always visible
    st.markdown("""
        <div style='background: linear-gradient(135deg, #1DA1F2 0%, #0d8bd9 100%); padding: 20px 25px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(29, 161, 242, 0.3);'>
            <h3 style='color: white; margin: 0; font-size: 22px; font-weight: 700;'>📖 First Time? Learn How to Get Your Twitter Archive</h3>
            <p style='color: white; margin: 10px 0 0 0; font-size: 16px; opacity: 0.95;'>Follow these simple steps to download your Twitter data and start analyzing!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Collapsible guide section with slide feature
    with st.expander("👇 **Click here to see step-by-step instructions**", expanded=False):
        
        # Initialize step counter in session state
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 1
        
        # Define all steps
        steps = [
            {
                "title": "Step 1: Go to More",
                "instructions for mobile": "**Mobile: Click on your profile and go to settings and support**",
                "image": "images/step-1.png",
                "caption": "Click on More from your profile menu"
            },
            {
                "title": "Step 2: Click on settings and privacy",
                "instructions for mobile": "**Mobile: Click on settings and privacy**",
                "image": "images/step-2.png",
                "caption": "Navigate to settings and privacy from your profile menu"
            },
            {
                "title": "Step 3: Click on your account and then Download an archive of your data",
                "instructions for mobile": "**Mobile: Click on your account and then Download an archive of your data**",
                "image": "images/step-3.png",
                "caption": "Click on your account and then Download an archive of your data"
            },
            {
                "title": "Step 4: Verify Your Identity",
                "instructions for mobile": "**Mobile: Twitter will ask you to verify - click 'Send code'**",
                "image": "images/step-4.png",
                "caption": "Verify your identity by sending a code to your email"
            },
            {
                "title": "Step 5: Enter Verification Code",
                "instructions for mobile": "**Mobile: Check your email and enter the code Twitter sent you**",
                "image": "images/step-5.png",
                "caption": "Enter the verification code from your email"
            },
            {
                "title": "Step 6: Wait for Email (this may take 24-48 hours)",
                "instructions for mobile": "**Mobile: Twitter will email you when your archive is ready and click on the download link**",
                "image": "images/step-6.png",
                "caption": "You'll receive an email when your archive is ready and click on the download link"
            },
            {
                "title": "Step 7: Download & Extract",
                "instructions for mobile": "**Mobile: Unzip the archive to a folder**",
                "image": "images/step-7.png",
                "caption": "Unzip the archive to a folder"
            },
            {
                "title": "Step 8: Open the data folder (this is the folder that contains all the data you need to upload)",
                "instructions for mobile": "**Mobile: Open the data folder**",
                "image": "images/step-8.png",
                "caption": "Open the data folder"
            },
            {
                "title": "Step 9: You are all set to upload your data",
                "instructions for mobile": "**Mobile: You are all set to upload your data**",
                "image": "images/step-9.png",
                "caption": "You are all set to upload your data"
            }
        ]
        
        total_steps = len(steps)
        current_step = st.session_state.current_step
        
        # Get current step data
        step_data = steps[current_step - 1]
        
        # Step indicator
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <span style='background-color: #1DA1F2; color: white; padding: 8px 16px; border-radius: 20px; font-weight: 600;'>
                Step {current_step} of {total_steps}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Display current step
        st.markdown(f"### {step_data['title']}")
        st.markdown(step_data['instructions for mobile'])
        
        # Fixed-size container CSS to prevent window resizing between steps
        st.markdown("""
        <style>
        /* Fix image container height based on step 1 to prevent layout shift */
        div[data-testid="stImage"] {
            min-height: 500px !important;
            max-height: 500px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stImage"] img {
            max-height: 480px !important;
            max-width: 100% !important;
            object-fit: contain !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display image with fixed container size (centered, fits in window)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(step_data['image'], caption=step_data['caption'], use_container_width=True)
        
        # Navigation buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=(current_step == 1), use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", disabled=(current_step == 1), use_container_width=True):
                st.session_state.current_step -= 1
                st.rerun()
        
        with col4:
            if st.button("Next ▶️", disabled=(current_step == total_steps), use_container_width=True):
                st.session_state.current_step += 1
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", disabled=(current_step == total_steps), use_container_width=True):
                st.session_state.current_step = total_steps
                st.rerun()
        
        # Step dots indicator
        dots_html = '<div style="text-align: center; margin-top: 20px;">'
        for i in range(1, total_steps + 1):
            if i == current_step:
                dots_html += f'<span style="color: #1DA1F2; font-size: 20px; margin: 0 5px;">●</span>'
            else:
                dots_html += f'<span style="color: #ccc; font-size: 20px; margin: 0 5px;">○</span>'
        dots_html += '</div>'
        st.markdown(dots_html, unsafe_allow_html=True)
        
        # Final message on last step
        if current_step == total_steps:
            st.markdown("---")
            st.success("✨ **Ready to upload!** Use the upload section above to get started!")

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
    
    # File upload section - MAIN FEATURE ON TOP
    st.subheader("📂 Upload Your Twitter Archive Data")
    
    st.markdown("""
    **📤 How to upload:**
    
    1. Extract your Twitter archive ZIP file received in your email
    2. Unzip the archive to a folder
    3. Open the **data/** folder inside the archive
    4. Click "Browse files" below
    5. Select **ALL files** (Press Cmd/Ctrl + A to select all) Refer to step 8 in the guide section for more details.
    6. Click "Browse files" below"
    7. Select all files from the data folder and click "open"
    8. Watch this Youtube video for more details: https://youtu.be/PviI7er6MaA
    """)
    
    # Custom CSS to hide the file list
    st.markdown("""
        <style>
        /* Hide the file list/viewer that shows after upload */
        [data-testid="stFileUploader"] section[data-testid="stFileUploaderDeleteBtn"] {
            display: none;
        }
        [data-testid="stFileUploader"] section > button {
            display: none;
        }
        div[data-testid="stFileUploadDropzone"] {
            padding: 30px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "📂 Browse and select all files from the data/ folder",
        type=['js'],
        accept_multiple_files=True,
        help="Select all files from the data folder - we'll automatically use what's needed",
        label_visibility="visible"
    )
    
    if not uploaded_files:
        st.info("👆 Click 'Browse files' above to get started")
        
        # Show guide section below upload (when no files uploaded yet)
        guide_section()
        return
    
    # Silently filter to only the files we need
    needed_files = ['follower.js', 'following.js', 'account.js', 'profile.js', 'tweets.js', 'like.js', 
                    'block.js', 'mute.js', 'lists-created.js', 'direct-messages.js']
    
    filtered_files = [f for f in uploaded_files if f.name in needed_files]
    
    if not filtered_files:
        st.error("❌ Required files not found. Please make sure you're uploading files from the data/ folder")
        return
    
    # Just show simple success message
    st.success(f"✅ Archive loaded successfully! Found {len(filtered_files)} data files.")
    
    # Create temporary directory to store uploaded files
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / 'data'
    data_dir.mkdir()
    
    # Save only filtered files
    for uploaded_file in filtered_files:
        file_path = data_dir / uploaded_file.name
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
    
    # Load data
    with st.spinner("🔄 Loading your Twitter data..."):
        try:
            dashboard = TwitterDashboard(temp_dir)
            data = dashboard.load_all_data()
            st.success(f"🎉 Successfully loaded your Twitter archive!")
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            return
    
    # Show guide section below upload (for reference, collapsed by default)
    guide_section()
    
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
            # Create dataframe for better display with clickable links
            import pandas as pd
            
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
            # Create dataframe for better display with clickable links
            import pandas as pd
            
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
    
    # # Key Metrics
    # st.subheader("📊 Key Metrics")
    # metrics = dashboard.create_engagement_metrics(data)
    
    # cols = st.columns(4)
    # cols[0].metric("Followers", metrics['Followers'])
    # cols[1].metric("Following", metrics['Following'])
    # cols[2].metric("Mutual Connections", metrics['Mutual Connections'])
    # cols[3].metric("Engagement Rate", metrics['Engagement Rate'])
    
    # cols2 = st.columns(3)
    # cols2[0].metric("Total Tweets", metrics['Total Tweets'])
    # cols2[1].metric("Total Likes", metrics['Total Likes'])
    # cols2[2].metric("Follower Ratio", metrics['Follower Ratio'])
    
    # st.markdown("---")
    
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
    
    # # Detailed Lists
    # with st.expander("📋 View Detailed Lists"):
    #     tab1, tab2, tab3 = st.tabs(["Followers", "Following", "Mutual Connections"])
        
    #     followers = data.get('followers', [])
    #     following = data.get('following', [])
    #     follower_ids = {f['follower']['accountId'] for f in followers}
    #     following_ids = {f['following']['accountId'] for f in following}
    #     mutual_ids = follower_ids & following_ids
        
    #     with tab1:
    #         st.write(f"Total Followers: {len(followers)}")
    #         for f in followers[:20]:  # Show first 20
    #             st.write(f"- User ID: {f['follower']['accountId']}")
        
    #     with tab2:
    #         st.write(f"Total Following: {len(following)}")
    #         for f in following[:20]:  # Show first 20
    #             st.write(f"- User ID: {f['following']['accountId']}")
        
    #     with tab3:
    #         st.write(f"Total Mutual Connections: {len(mutual_ids)}")
    #         for uid in list(mutual_ids)[:20]:  # Show first 20
    #             st.write(f"- User ID: {uid}")

if __name__ == "__main__":
    main()

