import json
import re
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path
import statistics


class AdvancedTwitterAnalytics:
    """Advanced analytics engine for Twitter data"""
    
    def __init__(self, archive_path):
        self.archive_path = Path(archive_path)
        self.data_path = self.archive_path / 'data'
        self.data = {}
        
    def extract_js_data(self, file_path):
        """Extract data from .js files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'window\.YTD\.\w+\.part\d+\s*=\s*(\[.*\])', content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return []
    
    def load_data(self):
        """Load all data"""
        print("🔄 Loading data...")
        
        files = {
            'followers': 'follower.js',
            'following': 'following.js',
            'tweets': 'tweets.js',
            'likes': 'like.js',
            'account': 'account.js',
            'profile': 'profile.js',
            'blocks': 'block.js',
            'mutes': 'mute.js',
            'lists_created': 'lists-created.js',
            'direct_messages': 'direct-messages.js',
        }
        
        for key, filename in files.items():
            file_path = self.data_path / filename
            if file_path.exists():
                self.data[key] = self.extract_js_data(file_path)
                print(f"  ✓ Loaded {key}: {len(self.data[key])} items")
        
        # Handle nested account/profile data
        if 'account' in self.data and self.data['account']:
            self.data['account'] = self.data['account'][0].get('account', {})
        if 'profile' in self.data and self.data['profile']:
            self.data['profile'] = self.data['profile'][0].get('profile', {})
        
        print("✅ Data loaded successfully!\n")
    
    def analyze_network_quality(self):
        """Analyze the quality of your network"""
        print("=" * 70)
        print("🌐 NETWORK QUALITY ANALYSIS")
        print("=" * 70)
        
        followers = self.data.get('followers', [])
        following = self.data.get('following', [])
        
        if not followers and not following:
            print("\n⚠️  No network data available")
            return
        
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        
        mutual = follower_ids & following_ids
        not_following_back = follower_ids - following_ids
        not_followed_back = following_ids - follower_ids
        
        # Calculate network metrics
        total_connections = len(follower_ids | following_ids)
        reciprocity_rate = len(mutual) / len(following) * 100 if following else 0
        follower_ratio = len(followers) / len(following) if following else 0
        
        print(f"\n📊 Network Metrics:")
        print(f"   Total unique connections: {total_connections}")
        print(f"   Network reciprocity rate: {reciprocity_rate:.1f}%")
        print(f"   Follower/Following ratio: {follower_ratio:.2f}")
        
        # Network quality score (0-100)
        quality_score = 0
        quality_score += min(reciprocity_rate, 50)  # Up to 50 points
        quality_score += min(follower_ratio * 20, 30)  # Up to 30 points
        quality_score += min(len(mutual) / 10 * 20, 20)  # Up to 20 points
        
        print(f"\n⭐ Network Quality Score: {quality_score:.0f}/100")
        
        if quality_score >= 80:
            print("   🎉 Excellent! You have a highly engaged network.")
        elif quality_score >= 60:
            print("   👍 Good! Your network is fairly well-connected.")
        elif quality_score >= 40:
            print("   📈 Fair. There's room for improvement in engagement.")
        else:
            print("   ⚠️  Low engagement. Focus on building mutual connections.")
        
        print(f"\n🔍 Connection Breakdown:")
        print(f"   Mutual connections: {len(mutual)} ({len(mutual)/total_connections*100:.1f}%)")
        print(f"   One-sided followers: {len(not_following_back)} ({len(not_following_back)/total_connections*100:.1f}%)")
        print(f"   One-sided following: {len(not_followed_back)} ({len(not_followed_back)/total_connections*100:.1f}%)")
        
        return {
            'quality_score': quality_score,
            'reciprocity_rate': reciprocity_rate,
            'mutual': list(mutual),
            'not_followed_back': list(not_followed_back)
        }
    
    def analyze_content_patterns(self):
        """Analyze content creation patterns"""
        print("\n" + "=" * 70)
        print("📝 CONTENT PATTERN ANALYSIS")
        print("=" * 70)
        
        tweets = self.data.get('tweets', [])
        
        if not tweets:
            print("\n⚠️  No tweet data available")
            return
        
        # Analyze tweet types
        original = 0
        retweets = 0
        replies = 0
        quotes = 0
        
        # Tweet metadata
        tweet_lengths = []
        hashtag_counts = []
        mention_counts = []
        media_counts = []
        url_counts = []
        
        # Time analysis
        hours = []
        days = []
        months = []
        
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            full_text = tweet.get('full_text', '')
            
            # Classify tweet type
            if tweet.get('retweeted', False) or full_text.startswith('RT @'):
                retweets += 1
            elif 'in_reply_to_status_id' in tweet:
                replies += 1
            elif 'quoted_status_id' in tweet:
                quotes += 1
            else:
                original += 1
            
            # Content analysis
            tweet_lengths.append(len(full_text))
            hashtag_counts.append(len(re.findall(r'#\w+', full_text)))
            mention_counts.append(len(re.findall(r'@\w+', full_text)))
            
            # Media and URLs
            entities = tweet.get('entities', {})
            media_counts.append(len(entities.get('media', [])))
            url_counts.append(len(entities.get('urls', [])))
            
            # Time analysis
            created_at = tweet.get('created_at')
            if created_at:
                try:
                    dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    hours.append(dt.hour)
                    days.append(dt.strftime('%A'))
                    months.append(dt.strftime('%B %Y'))
                except:
                    pass
        
        total = len(tweets)
        
        print(f"\n📊 Content Mix:")
        print(f"   Original tweets: {original} ({original/total*100:.1f}%)")
        print(f"   Replies: {replies} ({replies/total*100:.1f}%)")
        print(f"   Retweets: {retweets} ({retweets/total*100:.1f}%)")
        print(f"   Quote tweets: {quotes} ({quotes/total*100:.1f}%)")
        
        print(f"\n📏 Content Metrics (Average):")
        if tweet_lengths:
            print(f"   Tweet length: {statistics.mean(tweet_lengths):.0f} characters")
        if hashtag_counts:
            print(f"   Hashtags per tweet: {statistics.mean(hashtag_counts):.1f}")
        if mention_counts:
            print(f"   Mentions per tweet: {statistics.mean(mention_counts):.1f}")
        if media_counts:
            print(f"   Media per tweet: {statistics.mean(media_counts):.1f}")
        if url_counts:
            print(f"   URLs per tweet: {statistics.mean(url_counts):.1f}")
        
        if hours:
            # Find peak activity times
            hour_counts = Counter(hours)
            top_hours = hour_counts.most_common(3)
            print(f"\n⏰ Peak Posting Hours:")
            for hour, count in top_hours:
                print(f"   {hour:02d}:00 - {count} tweets ({count/len(hours)*100:.1f}%)")
        
        if days:
            day_counts = Counter(days)
            top_days = day_counts.most_common(3)
            print(f"\n📅 Most Active Days:")
            for day, count in top_days:
                print(f"   {day} - {count} tweets ({count/len(days)*100:.1f}%)")
        
        if months:
            month_counts = Counter(months)
            top_months = month_counts.most_common(3)
            print(f"\n📆 Most Active Months:")
            for month, count in top_months:
                print(f"   {month} - {count} tweets")
    
    def analyze_interests(self):
        """Analyze interests based on content"""
        print("\n" + "=" * 70)
        print("🎯 INTEREST & TOPIC ANALYSIS")
        print("=" * 70)
        
        tweets = self.data.get('tweets', [])
        likes = self.data.get('likes', [])
        
        all_hashtags = []
        all_mentions = []
        all_words = []
        
        # Common stop words to filter
        stop_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 
                      'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 
                      'do', 'at', 'this', 'but', 'his', 'by', 'from', 'is', 'are',
                      'was', 'my', 'me', 'so', 'if', 'just', 'like', 'get', 'can'}
        
        # Analyze tweets
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            full_text = tweet.get('full_text', '')
            
            all_hashtags.extend(re.findall(r'#(\w+)', full_text.lower()))
            all_mentions.extend(re.findall(r'@(\w+)', full_text.lower()))
            
            # Extract words (excluding hashtags, mentions, URLs)
            text = re.sub(r'http\S+|www.\S+', '', full_text)
            text = re.sub(r'[@#]\w+', '', text)
            words = [w.lower() for w in re.findall(r'\b\w{4,}\b', text) 
                    if w.lower() not in stop_words]
            all_words.extend(words)
        
        # Analyze likes
        for like_obj in likes:
            like = like_obj.get('like', {})
            full_text = like.get('fullText', '')
            
            all_hashtags.extend(re.findall(r'#(\w+)', full_text.lower()))
            all_mentions.extend(re.findall(r'@(\w+)', full_text.lower()))
        
        if all_hashtags:
            print(f"\n🏷️  Top Hashtags:")
            for tag, count in Counter(all_hashtags).most_common(10):
                print(f"   #{tag}: {count} times")
        
        if all_mentions:
            print(f"\n👤 Most Mentioned/Liked Accounts:")
            for mention, count in Counter(all_mentions).most_common(10):
                print(f"   @{mention}: {count} times")
        
        if all_words:
            print(f"\n💬 Top Keywords:")
            for word, count in Counter(all_words).most_common(15):
                print(f"   {word}: {count} times")
    
    def analyze_behavior_patterns(self):
        """Analyze user behavior patterns"""
        print("\n" + "=" * 70)
        print("🧠 BEHAVIOR PATTERN ANALYSIS")
        print("=" * 70)
        
        tweets = self.data.get('tweets', [])
        likes = self.data.get('likes', [])
        blocks = self.data.get('blocks', [])
        mutes = self.data.get('mutes', [])
        
        print(f"\n📊 Engagement Metrics:")
        print(f"   Total tweets: {len(tweets)}")
        print(f"   Total likes: {len(likes)}")
        print(f"   Like/Tweet ratio: {len(likes)/len(tweets):.2f}" if tweets else "   No tweets")
        
        if blocks or mutes:
            print(f"\n🔒 Privacy Actions:")
            print(f"   Blocked accounts: {len(blocks)}")
            print(f"   Muted accounts: {len(mutes)}")
        
        # Account age analysis
        if 'account' in self.data and isinstance(self.data['account'], dict):
            created_at = self.data['account'].get('createdAt', '')
            if created_at:
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    account_age = (datetime.now(created_date.tzinfo) - created_date).days
                    years = account_age / 365.25
                    
                    print(f"\n📆 Account History:")
                    print(f"   Account age: {years:.1f} years ({account_age} days)")
                    
                    if tweets:
                        tweets_per_day = len(tweets) / account_age
                        tweets_per_month = tweets_per_day * 30
                        print(f"   Average activity: {tweets_per_day:.2f} tweets/day")
                        print(f"   Monthly average: {tweets_per_month:.0f} tweets/month")
                    
                    if likes:
                        likes_per_day = len(likes) / account_age
                        print(f"   Like frequency: {likes_per_day:.2f} likes/day")
                except Exception as e:
                    print(f"   Could not parse account creation date")
    
    def generate_recommendations(self):
        """Generate personalized recommendations"""
        print("\n" + "=" * 70)
        print("💡 PERSONALIZED RECOMMENDATIONS")
        print("=" * 70)
        
        followers = self.data.get('followers', [])
        following = self.data.get('following', [])
        tweets = self.data.get('tweets', [])
        
        recommendations = []
        
        # Network recommendations
        if len(followers) < len(following) * 0.5:
            recommendations.append({
                'category': '👥 Network Growth',
                'tip': 'Your follower count is low compared to following.',
                'action': 'Focus on creating more engaging original content to attract followers.'
            })
        
        if following and len(followers):
            follower_ids = {f['follower']['accountId'] for f in followers}
            following_ids = {f['following']['accountId'] for f in following}
            mutual = len(follower_ids & following_ids)
            
            if mutual / len(following) < 0.2:
                recommendations.append({
                    'category': '🤝 Engagement',
                    'tip': 'Low mutual connection rate detected.',
                    'action': 'Engage more with accounts you follow (reply, retweet, like) to build relationships.'
                })
        
        # Content recommendations
        if tweets:
            original = sum(1 for t in tweets if not t.get('tweet', {}).get('retweeted', False) 
                          and 'in_reply_to_status_id' not in t.get('tweet', {}))
            if original / len(tweets) < 0.3:
                recommendations.append({
                    'category': '📝 Content Strategy',
                    'tip': 'Most of your tweets are replies or retweets.',
                    'action': 'Create more original content to establish your unique voice.'
                })
        
        # Display recommendations
        if recommendations:
            print()
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['category']}")
                print(f"   💡 Insight: {rec['tip']}")
                print(f"   ✅ Action: {rec['action']}")
        else:
            print("\n✨ Great job! Your Twitter usage looks healthy.")
            print("   Keep engaging with your community and creating quality content.")
    
    def generate_full_report(self):
        """Generate comprehensive analytics report"""
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "TWITTER ARCHIVE ANALYTICS REPORT" + " " * 20 + "║")
        print("╚" + "═" * 68 + "╝")
        
        # Display account info
        if 'account' in self.data and isinstance(self.data['account'], dict):
            account = self.data['account']
            print(f"\n👤 Account: @{account.get('username', 'Unknown')}")
            print(f"📧 Email: {account.get('email', 'N/A')}")
            print(f"📅 Created: {account.get('createdAt', 'N/A')[:10]}")
        
        if 'profile' in self.data and isinstance(self.data['profile'], dict):
            profile = self.data['profile']
            desc = profile.get('description', {})
            if desc.get('bio'):
                print(f"📝 Bio: {desc.get('bio')}")
        
        print("\n")
        
        # Run all analyses
        self.analyze_network_quality()
        self.analyze_content_patterns()
        self.analyze_interests()
        self.analyze_behavior_patterns()
        self.generate_recommendations()
        
        print("\n" + "=" * 70)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 70)
        print("\nThank you for using Twitter Archive Analytics!")
        print("For more insights, try the interactive dashboard: streamlit run main.py")
        print()


def main():
    import sys
    
    print("\n🐦 Twitter Archive Advanced Analytics\n")
    
    # Get archive path
    if len(sys.argv) > 1:
        archive_path = sys.argv[1]
    else:
        archive_path = input("Enter path to Twitter archive folder: ").strip()
    
    if not Path(archive_path).exists():
        print(f"\n❌ Error: Path '{archive_path}' does not exist.")
        return
    
    # Run analysis
    analyzer = AdvancedTwitterAnalytics(archive_path)
    analyzer.load_data()
    analyzer.generate_full_report()


if __name__ == "__main__":
    main()

