import json
import csv
import re
from datetime import datetime
from pathlib import Path
from collections import Counter


class TwitterDataExporter:
    """Export Twitter archive data to various formats"""
    
    def __init__(self, archive_path, output_dir='exports'):
        self.archive_path = Path(archive_path)
        self.data_path = self.archive_path / 'data'
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
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
    
    def export_followers_csv(self):
        """Export followers to CSV"""
        followers = self.extract_js_data(self.data_path / 'follower.js')
        
        output_file = self.output_dir / 'followers.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Account ID', 'User Link'])
            
            for follower_obj in followers:
                follower = follower_obj['follower']
                writer.writerow([
                    follower['accountId'],
                    follower['userLink']
                ])
        
        print(f"✓ Exported {len(followers)} followers to {output_file}")
        return output_file
    
    def export_following_csv(self):
        """Export following to CSV"""
        following = self.extract_js_data(self.data_path / 'following.js')
        
        output_file = self.output_dir / 'following.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Account ID', 'User Link'])
            
            for following_obj in following:
                follow = following_obj['following']
                writer.writerow([
                    follow['accountId'],
                    follow['userLink']
                ])
        
        print(f"✓ Exported {len(following)} following to {output_file}")
        return output_file
    
    def export_network_analysis_csv(self):
        """Export network analysis results"""
        followers = self.extract_js_data(self.data_path / 'follower.js')
        following = self.extract_js_data(self.data_path / 'following.js')
        
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        
        mutual = follower_ids & following_ids
        not_following_back = follower_ids - following_ids
        not_followed_back = following_ids - follower_ids
        
        # Export mutual connections
        output_file = self.output_dir / 'mutual_connections.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Account ID', 'Relationship'])
            for uid in mutual:
                writer.writerow([uid, 'Mutual'])
        print(f"✓ Exported {len(mutual)} mutual connections to {output_file}")
        
        # Export not followed back
        output_file = self.output_dir / 'not_followed_back.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Account ID', 'Note'])
            for uid in not_followed_back:
                writer.writerow([uid, 'You follow them, they don\'t follow back'])
        print(f"✓ Exported {len(not_followed_back)} non-reciprocal follows to {output_file}")
        
        # Export followers not following back
        output_file = self.output_dir / 'followers_not_following_back.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Account ID', 'Note'])
            for uid in not_following_back:
                writer.writerow([uid, 'They follow you, you don\'t follow back'])
        print(f"✓ Exported {len(not_following_back)} followers you don't follow back to {output_file}")
    
    def export_tweets_csv(self):
        """Export tweets to CSV"""
        tweets = self.extract_js_data(self.data_path / 'tweets.js')
        
        output_file = self.output_dir / 'tweets.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Tweet ID', 'Created At', 'Full Text', 'Retweet Count', 
                'Favorite Count', 'Reply Count', 'Type', 'Hashtags', 'Mentions'
            ])
            
            for tweet_obj in tweets:
                tweet = tweet_obj.get('tweet', {})
                
                # Determine tweet type
                tweet_type = 'Original'
                full_text = tweet.get('full_text', '')
                if tweet.get('retweeted', False) or full_text.startswith('RT @'):
                    tweet_type = 'Retweet'
                elif 'in_reply_to_status_id' in tweet:
                    tweet_type = 'Reply'
                elif 'quoted_status_id' in tweet:
                    tweet_type = 'Quote'
                
                # Extract hashtags and mentions
                hashtags = ', '.join([f"#{tag}" for tag in re.findall(r'#(\w+)', full_text)])
                mentions = ', '.join([f"@{mention}" for mention in re.findall(r'@(\w+)', full_text)])
                
                writer.writerow([
                    tweet.get('id_str', ''),
                    tweet.get('created_at', ''),
                    full_text,
                    tweet.get('retweet_count', 0),
                    tweet.get('favorite_count', 0),
                    tweet.get('reply_count', 0),
                    tweet_type,
                    hashtags,
                    mentions
                ])
        
        print(f"✓ Exported {len(tweets)} tweets to {output_file}")
        return output_file
    
    def export_likes_csv(self):
        """Export likes to CSV"""
        likes = self.extract_js_data(self.data_path / 'like.js')
        
        output_file = self.output_dir / 'likes.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Tweet ID', 'Full Text', 'URL'])
            
            for like_obj in likes:
                like = like_obj.get('like', {})
                writer.writerow([
                    like.get('tweetId', ''),
                    like.get('fullText', ''),
                    like.get('expandedUrl', '')
                ])
        
        print(f"✓ Exported {len(likes)} likes to {output_file}")
        return output_file
    
    def export_insights_json(self):
        """Export comprehensive insights as JSON"""
        followers = self.extract_js_data(self.data_path / 'follower.js')
        following = self.extract_js_data(self.data_path / 'following.js')
        tweets = self.extract_js_data(self.data_path / 'tweets.js')
        likes = self.extract_js_data(self.data_path / 'like.js')
        
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        
        # Calculate metrics
        mutual = follower_ids & following_ids
        
        # Analyze tweets
        tweet_types = {'original': 0, 'reply': 0, 'retweet': 0, 'quote': 0}
        all_hashtags = []
        all_mentions = []
        
        for tweet_obj in tweets:
            tweet = tweet_obj.get('tweet', {})
            full_text = tweet.get('full_text', '')
            
            if tweet.get('retweeted', False) or full_text.startswith('RT @'):
                tweet_types['retweet'] += 1
            elif 'in_reply_to_status_id' in tweet:
                tweet_types['reply'] += 1
            elif 'quoted_status_id' in tweet:
                tweet_types['quote'] += 1
            else:
                tweet_types['original'] += 1
            
            all_hashtags.extend(re.findall(r'#(\w+)', full_text.lower()))
            all_mentions.extend(re.findall(r'@(\w+)', full_text.lower()))
        
        # Compile insights
        insights = {
            'timestamp': datetime.now().isoformat(),
            'network': {
                'followers': len(followers),
                'following': len(following),
                'mutual_connections': len(mutual),
                'follower_ratio': len(followers) / len(following) if following else 0,
                'engagement_rate': len(mutual) / len(following) * 100 if following else 0
            },
            'content': {
                'total_tweets': len(tweets),
                'total_likes': len(likes),
                'tweet_types': tweet_types,
                'like_to_tweet_ratio': len(likes) / len(tweets) if tweets else 0
            },
            'interests': {
                'top_hashtags': dict(Counter(all_hashtags).most_common(10)),
                'top_mentions': dict(Counter(all_mentions).most_common(10))
            }
        }
        
        output_file = self.output_dir / 'insights.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2)
        
        print(f"✓ Exported insights to {output_file}")
        return output_file
    
    def export_all(self):
        """Export all data"""
        print("\n📤 Twitter Data Exporter")
        print("=" * 60)
        print(f"\nExporting to: {self.output_dir.absolute()}\n")
        
        # Export followers and following
        self.export_followers_csv()
        self.export_following_csv()
        
        # Export network analysis
        self.export_network_analysis_csv()
        
        # Export tweets and likes
        self.export_tweets_csv()
        self.export_likes_csv()
        
        # Export insights
        self.export_insights_json()
        
        print("\n" + "=" * 60)
        print("✅ Export Complete!")
        print(f"📁 Files saved to: {self.output_dir.absolute()}")
        print("=" * 60 + "\n")


def main():
    import sys
    
    print("\n📤 Twitter Archive Data Exporter\n")
    
    # Get archive path
    if len(sys.argv) > 1:
        archive_path = sys.argv[1]
    else:
        archive_path = input("Enter path to Twitter archive folder: ").strip()
    
    if not Path(archive_path).exists():
        print(f"\n❌ Error: Path '{archive_path}' does not exist.")
        return
    
    # Get output directory
    output_dir = input("Enter output directory (default: 'exports'): ").strip() or 'exports'
    
    # Run export
    exporter = TwitterDataExporter(archive_path, output_dir)
    exporter.export_all()


if __name__ == "__main__":
    main()

