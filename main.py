import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
from twitter_utils import TwitterDashboard, fetch_usernames_from_api

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
                "title": "Step 6: Request your archive",
                "instructions for mobile": "**Mobile: Request your archive from Twitter**",
                "image": "images/step-6.png",
                "caption": "Click on the request archive button"
            },
            {
                "title": "Step 7: Wait for Email (this may take 24-48 hours)",
                "instructions for mobile": "**Mobile: Twitter will email you when your archive is ready and click on the download link**",
                "image": "images/step-7.png",
                "caption": "You'll receive an email when your archive is ready and click on the download link"
            },
            {
                "title": "Step 8: Download & Extract",
                "instructions for mobile": "**Mobile: Unzip the archive to a folder**",
                "image": "images/step-8.png",
                "caption": "Unzip the archive to a folder"
            },
            {
                "title": "Step 9: Open the data folder (this is the folder that contains all the data you need to upload)",
                "instructions for mobile": "**Mobile: Open the data folder**",
                "image": "images/step-9.png",
                "caption": "Open the data folder"
            },
            {
                "title": "Step 10: You are all set to upload your data",
                "instructions for mobile": "**Mobile: You are all set to upload your data**",
                "image": "images/step-10.png",
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
    st.set_page_config(
        page_title="Twitter Analytics Dashboard", 
        page_icon="🐦", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS - Hide sidebar completely
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
        /* Hide the sidebar */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        /* Adjust main content to full width */
        [data-testid="stAppViewContainer"] > div:first-child {
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Centered Title
    st.markdown("<h1 style='text-align: center;'>🐦 Twitter Analytics Dashboard</h1>", unsafe_allow_html=True)
    
    # File upload section - MAIN FEATURE ON TOP
    # Center the content using columns
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
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
        """)
        
        # Embedded YouTube video
        st.markdown("### 📹 Watch Video Tutorial")
        st.markdown("**Need help? Watch this step-by-step video guide:**")
        
        # Extract video ID from URL
        video_id = "PviI7er6MaA"  # From https://youtu.be/PviI7er6MaA
        
        # Embed YouTube video
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <iframe 
                width="100%" 
                height="315" 
                src="https://www.youtube.com/embed/{video_id}" 
                title="Twitter Archive Upload Tutorial" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen
                style="border-radius: 10px; margin: 0 auto; display: block;">
            </iframe>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        # Placeholder for demo data alert
        demo_alert = st.empty()
        
        uploaded_files = st.file_uploader(
            "📂 Browse and select all files from the data/ folder",
            type=['js'],
            accept_multiple_files=True,
            help="Select all files from the data folder - we'll automatically use what's needed",
            label_visibility="visible"
        )
    
    # Initialize data and dashboard
    data = None
    dashboard = None

    if not uploaded_files:
        # Show animated arrow pointing to upload button
        with demo_alert:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 15px; animation: fadeIn 1s;">
                    <div style="
                        display: inline-block;
                        color: #0f1419; 
                        font-weight: 600; 
                        margin-bottom: 5px; 
                        padding: 12px 20px;
                        background-color: #e8f5fe;
                        border-radius: 20px;
                        border: 2px solid #1DA1F2;
                        box-shadow: 0 4px 6px rgba(29, 161, 242, 0.2);
                    ">
                        👀 You are viewing <b>DEMO DATA</b>. Upload your own archive below!
                    </div>
                    <div style="
                        font-size: 40px; 
                        animation: bounce 1.5s infinite; 
                        color: #1DA1F2; 
                        margin-top: -10px;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        👇
                    </div>
                    <style>
                        @keyframes bounce {
                            0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
                            40% {transform: translateY(10px);}
                            60% {transform: translateY(5px);}
                        }
                        @keyframes fadeIn {
                            from {opacity: 0; transform: translateY(-10px);}
                            to {opacity: 1; transform: translateY(0);}
                        }
                    </style>
                </div>
            """, unsafe_allow_html=True)
            
        st.info("ℹ️ **Viewing Demo Data**: Upload your own Twitter archive above to see your analytics!")
        
        # Show guide section for those who want to know how to get data
        guide_section()
        
        try:
            # Use current directory where main.py is located
            current_dir = Path(__file__).parent
            dashboard = TwitterDashboard(current_dir)
            data = dashboard.load_all_data()
            
        except Exception as e:
            st.error(f"❌ Error loading demo data: {e}")
            return
            
    else:
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
                
                # Store data in session state
                st.session_state.temp_dir = temp_dir
                
                # Celebration!
                if 'balloons_shown' not in st.session_state:
                    st.balloons()
                    st.session_state.balloons_shown = True
                    
                st.success("🎉 **Data loaded successfully! See your analysis below...**")
                
            except Exception as e:
                st.error(f"❌ Error loading data: {e}")
                return

    # Store data in session state
    if data:
        st.session_state.twitter_data = data
        st.session_state.dashboard = dashboard
    
    # Display User Greeting
    account = data.get('account', {})
    if account:
        username = account.get('username', '')
        display_name = account.get('accountDisplayName', '')
        
        st.markdown(f"""
            # 👋 Hello, @{display_name}!
            ### Welcome to your analytics dashboard, {username}
        """)
    
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
                    user_data = usernames_data[uid]
                    username = user_data['username']
                    display_name = user_data['name']
                    is_verified = user_data.get('verified', False)
                    verified_badge = " ☑️" if is_verified else ""
                    
                    username_display = f"{username}\n{display_name}{verified_badge}" if display_name else f"{username}{verified_badge}"
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
                    user_data = usernames_data[uid]
                    username = user_data['username']
                    display_name = user_data['name']
                    is_verified = user_data.get('verified', False)
                    verified_badge = " ☑️" if is_verified else ""
                    
                    username_display = f"{username}\n{display_name}{verified_badge}" if display_name else f"{username}{verified_badge}"
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
    
    st.markdown("---")
    
    # Account Overview Dashboard
    st.subheader("Account overview")
    
    # Filters
    # Filters
    col_filters1, col_filters2 = st.columns([2, 1])
    
    with col_filters1:
        # Time range selector - Moved to wider column for better visibility
        time_ranges = {'7D': 7, '2W': 14, '4W': 28, '3M': 90, '1Y': 365, 'All': 3650}
        selected_range_label = st.radio(
            "Time Range",
            options=list(time_ranges.keys()),
            index=4,
            horizontal=True,
            label_visibility="collapsed",
            key="time_range"
        )
        selected_days = time_ranges[selected_range_label]
    
    with col_filters2:
        # Metric selector - Moved to narrower column
        metric_options = {'Likes': 'likes', 'Retweets': 'retweets', 'Total Engagement': 'engagement'}
        selected_metric_label = st.radio(
            "Select Metric", 
            options=list(metric_options.keys()), 
            horizontal=True,
            label_visibility="collapsed",
            key="metric_select"
        )
        selected_metric = metric_options[selected_metric_label]
    
    # Generate Chart & Stats
    overview_fig, overview_stats = dashboard.create_account_overview_chart(
        data, 
        metric=selected_metric, 
        days=selected_days
    )
    
    # Display Stats Cards
    st.markdown("""
        <style>
        .stat-card {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
            border: 1px solid #e1e8ed;
        }
        .stat-label {
            font-size: 12px;
            color: #657786;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #14171a;
        }
        </style>
    """, unsafe_allow_html=True)
    
    stat_cols = st.columns(4)
    
    with stat_cols[0]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Total Tweets</div>
                <div class="stat-value">{overview_stats['tweets']:,}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with stat_cols[1]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Total Likes</div>
                <div class="stat-value">{overview_stats['likes']:,}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with stat_cols[2]:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Total Retweets</div>
                <div class="stat-value">{overview_stats['retweets']:,}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with stat_cols[3]:
        avg_eng = (overview_stats['likes'] + overview_stats['retweets']) / overview_stats['tweets'] if overview_stats['tweets'] > 0 else 0
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Avg Engagement</div>
                <div class="stat-value">{avg_eng:.1f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display Chart
    if overview_fig:
        st.plotly_chart(overview_fig, use_container_width=True)
    else:
        st.info(f"No data available for the selected time range ({selected_range_label}).")
    
    # Second Row: Follows over time & Posts vs Replies
    # col_row2_1, col_row2_2 = st.columns(2)
    
    # with col_row2_1:
    #     st.markdown("### Follows over time")
    #     st.info("ℹ️ **Data Not Available**\n\nTwitter archive exports do not include timestamps for when followers started following you. This chart cannot be generated from archive data.")
        
    # with col_row2_2:
    posts_replies_fig = dashboard.create_posts_replies_chart(data, days=selected_days)
    if posts_replies_fig:
        st.plotly_chart(posts_replies_fig, use_container_width=True)
    else:
        st.info("No posts or replies found in this time range.")
    
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
    
    # Footer with credits and copyright
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 20px; color: #666;'>
            <p>Made with ❤️ by Ajit Gupta (@unfiltered_ajit)</p>
            <p style='font-size: 0.9em;'>© 2025 All rights reserved</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

