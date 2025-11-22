import json
import re
from datetime import datetime
from collections import Counter
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

class TwitterArchiveAnalyzer:
    """Analyze Twitter Archive Data and provide insights"""
    
    def __init__(self, archive_path):
        self.archive_path = Path(archive_path)
        self.data_path = self.archive_path / 'data'
        self.followers = []
        self.following = []
        self.tweets = []
        self.likes = []
        self.account = None
        self.profile = None
        
    def extract_js_data(self, file_path):
        """Extract data from .js files in Twitter archive format"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract the JSON part from window.YTD.*.part0 = [...]
                match = re.search(r'window\.YTD\.\w+\.part\d+\s*=\s*(\[.*\])', content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return []
    
    def load_data(self):
        """Load all relevant data from archive"""
        print("📂 Loading Twitter archive data...")
        
        # Load followers
        follower_file = self.data_path / 'follower.js'
        if follower_file.exists():
            self.followers = self.extract_js_data(follower_file)
            print(f"✓ Loaded {len(self.followers)} followers")
        
        # Load following
        following_file = self.data_path / 'following.js'
        if following_file.exists():
            self.following = self.extract_js_data(following_file)
            print(f"✓ Loaded {len(self.following)} following")
        
        # Load tweets
        tweets_file = self.data_path / 'tweets.js'
        if tweets_file.exists():
            self.tweets = self.extract_js_data(tweets_file)
            print(f"✓ Loaded {len(self.tweets)} tweets")
        
        # Load likes
        likes_file = self.data_path / 'like.js'
        if likes_file.exists():
            self.likes = self.extract_js_data(likes_file)
            print(f"✓ Loaded {len(self.likes)} likes")
        
        # Load account info
        account_file = self.data_path / 'account.js'
        if account_file.exists():
            account_data = self.extract_js_data(account_file)
            if account_data:
                self.account = account_data[0].get('account', {})
                print(f"✓ Loaded account info")
        
        # Load profile
        profile_file = self.data_path / 'profile.js'
        if profile_file.exists():
            profile_data = self.extract_js_data(profile_file)
            if profile_data:
                self.profile = profile_data[0].get('profile', {})
                print(f"✓ Loaded profile info")
        
        print("✅ Data loading complete!\n")
    
    def get_follower_following_insights(self):
        """Analyze followers vs following"""
        print("=" * 60)
        print("👥 FOLLOWER & FOLLOWING INSIGHTS")
        print("=" * 60)
        
        num_followers = len(self.followers)
        num_following = len(self.following)
        
        print(f"\n📊 Basic Stats:")
        print(f"   Followers: {num_followers}")
        print(f"   Following: {num_following}")
        print(f"   Follower/Following Ratio: {num_followers/num_following if num_following > 0 else 0:.2f}")
        
        # Find mutual follows
        follower_ids = {f['follower']['accountId'] for f in self.followers}
        following_ids = {f['following']['accountId'] for f in self.following}
        
        mutual_follows = follower_ids & following_ids
        not_following_back = follower_ids - following_ids
        not_followed_back = following_ids - follower_ids
        
        print(f"\n🤝 Mutual Connections:")
        print(f"   Mutual follows (friends): {len(mutual_follows)}")
        print(f"   Followers you don't follow back: {len(not_following_back)}")
        print(f"   Following who don't follow back: {len(not_followed_back)}")
        
        if len(mutual_follows) > 0:
            print(f"\n   Engagement rate: {len(mutual_follows)/num_following*100:.1f}% of people you follow also follow you back")
        
        return {
            'followers': num_followers,
            'following': num_following,
            'mutual': len(mutual_follows),
            'not_following_back': list(not_following_back),
            'not_followed_back': list(not_followed_back)
        }
    
    def get_tweet_insights(self):
        """Analyze tweet patterns"""
        print("\n" + "=" * 60)
        print("📱 TWEET INSIGHTS")
        print("=" * 60)
        
        if not self.tweets:
            print("\nNo tweets found in archive.")
            return
        
        print(f"\n📊 Basic Stats:")
        print(f"   Total tweets: {len(self.tweets)}")
        
        # Analyze tweet timing
        tweet_dates = []
        tweet_hours = []
        tweet_days = []
        retweets = 0
        replies = 0
        original_tweets = 0
        
        for tweet_obj in self.tweets:
            tweet = tweet_obj.get('tweet', {})
            
            # Check tweet type
            if tweet.get('retweeted', False) or tweet.get('full_text', '').startswith('RT @'):
                retweets += 1
            elif 'in_reply_to_status_id' in tweet or tweet.get('full_text', '').startswith('@'):
                replies += 1
            else:
                original_tweets += 1
            
            # Parse date
            created_at = tweet.get('created_at')
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    tweet_dates.append(dt)
                    tweet_hours.append(dt.hour)
                    tweet_days.append(dt.strftime('%A'))
                except:
                    pass
        
        print(f"\n📝 Tweet Types:")
        print(f"   Original tweets: {original_tweets}")
        print(f"   Replies: {replies}")
        print(f"   Retweets: {retweets}")
        
        if tweet_hours:
            most_active_hour = Counter(tweet_hours).most_common(1)[0]
            print(f"\n⏰ Most Active Hour: {most_active_hour[0]}:00 ({most_active_hour[1]} tweets)")
        
        if tweet_days:
            most_active_day = Counter(tweet_days).most_common(1)[0]
            print(f"📅 Most Active Day: {most_active_day[0]} ({most_active_day[1]} tweets)")
        
        if tweet_dates:
            first_tweet = min(tweet_dates)
            last_tweet = max(tweet_dates)
            print(f"\n📆 Activity Period:")
            print(f"   First tweet: {first_tweet.strftime('%Y-%m-%d')}")
            print(f"   Last tweet: {last_tweet.strftime('%Y-%m-%d')}")
    
    def get_likes_insights(self):
        """Analyze liked tweets"""
        print("\n" + "=" * 60)
        print("❤️  LIKES INSIGHTS")
        print("=" * 60)
        
        if not self.likes:
            print("\nNo likes found in archive.")
            return
        
        print(f"\n📊 Basic Stats:")
        print(f"   Total likes: {len(self.likes)}")
        
        # Analyze liked content
        hashtags = []
        mentions = []
        
        for like_obj in self.likes:
            like = like_obj.get('like', {})
            full_text = like.get('fullText', '')
            
            # Extract hashtags
            hashtags.extend(re.findall(r'#(\w+)', full_text))
            
            # Extract mentions
            mentions.extend(re.findall(r'@(\w+)', full_text))
        
        if hashtags:
            top_hashtags = Counter(hashtags).most_common(5)
            print(f"\n🏷️  Top Hashtags in Liked Tweets:")
            for tag, count in top_hashtags:
                print(f"   #{tag}: {count} times")
        
        if mentions:
            top_mentions = Counter(mentions).most_common(5)
            print(f"\n👤 Most Liked Accounts:")
            for mention, count in top_mentions:
                print(f"   @{mention}: {count} times")
    
    def get_account_overview(self):
        """Display account overview"""
        print("=" * 60)
        print("👤 ACCOUNT OVERVIEW")
        print("=" * 60)
        
        if self.account:
            print(f"\n📝 Account Details:")
            print(f"   Username: @{self.account.get('username', 'N/A')}")
            print(f"   Display Name: {self.account.get('accountDisplayName', 'N/A')}")
            print(f"   Account ID: {self.account.get('accountId', 'N/A')}")
            print(f"   Created: {self.account.get('createdAt', 'N/A')[:10]}")
        
        if self.profile:
            desc = self.profile.get('description', {})
            print(f"\n📍 Profile:")
            print(f"   Bio: {desc.get('bio', 'N/A')}")
            print(f"   Location: {desc.get('location', 'N/A')}")
            print(f"   Website: {desc.get('website', 'N/A')}")
    
    def generate_report(self):
        """Generate complete analysis report"""
        self.load_data()
        self.get_account_overview()
        follower_insights = self.get_follower_following_insights()
        self.get_tweet_insights()
        self.get_likes_insights()
        
        print("\n" + "=" * 60)
        print("💡 KEY INSIGHTS & RECOMMENDATIONS")
        print("=" * 60)
        
        # Provide actionable insights
        if self.following and self.followers:
            if len(self.followers) < len(self.following):
                print("\n📈 Growth Opportunity:")
                print("   You follow more people than follow you back.")
                print("   Consider creating more engaging content to grow your follower base.")
            
            if follower_insights['not_followed_back']:
                print(f"\n🔍 Engagement Tip:")
                print(f"   {len(follower_insights['not_followed_back'])} accounts you follow don't follow back.")
                print("   You might want to review if these connections are still valuable.")
        
        print("\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 60)


def main():
    # Path to the Twitter archive
    archive_path = input("Enter the path to your Twitter archive folder: ").strip()
    
    if not Path(archive_path).exists():
        print(f"❌ Error: Path '{archive_path}' does not exist.")
        return
    
    # Create analyzer and generate report
    analyzer = TwitterArchiveAnalyzer(archive_path)
    analyzer.generate_report()


if __name__ == "__main__":
    main()

