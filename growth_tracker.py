import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter


class TwitterGrowthTracker:
    """Track Twitter account growth over time by comparing archives"""
    
    def __init__(self):
        self.archives = []
        
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
    
    def analyze_archive(self, archive_path, label=None):
        """Analyze a single archive and return metrics"""
        archive_path = Path(archive_path)
        data_path = archive_path / 'data'
        
        if not archive_path.exists():
            print(f"❌ Path does not exist: {archive_path}")
            return None
        
        # Extract timestamp from archive folder name or use label
        if not label:
            # Try to extract date from folder name
            match = re.search(r'twitter-(\d{4}-\d{2}-\d{2})-', str(archive_path))
            if match:
                label = match.group(1)
            else:
                label = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n📊 Analyzing archive: {label}")
        
        # Load data
        followers = self.extract_js_data(data_path / 'follower.js')
        following = self.extract_js_data(data_path / 'following.js')
        tweets = self.extract_js_data(data_path / 'tweets.js')
        likes = self.extract_js_data(data_path / 'like.js')
        
        # Calculate metrics
        follower_ids = {f['follower']['accountId'] for f in followers}
        following_ids = {f['following']['accountId'] for f in following}
        mutual = follower_ids & following_ids
        
        metrics = {
            'label': label,
            'timestamp': datetime.now().isoformat(),
            'followers': len(followers),
            'following': len(following),
            'mutual': len(mutual),
            'tweets': len(tweets),
            'likes': len(likes),
            'follower_ratio': len(followers) / len(following) if following else 0,
            'engagement_rate': len(mutual) / len(following) * 100 if following else 0,
            'like_tweet_ratio': len(likes) / len(tweets) if tweets else 0,
            'follower_ids': follower_ids,
            'following_ids': following_ids
        }
        
        print(f"  ✓ Followers: {metrics['followers']}")
        print(f"  ✓ Following: {metrics['following']}")
        print(f"  ✓ Engagement: {metrics['engagement_rate']:.1f}%")
        
        return metrics
    
    def compare_archives(self, archive1_path, archive2_path, label1="Old", label2="New"):
        """Compare two archives and show growth"""
        print("=" * 70)
        print("📈 TWITTER GROWTH COMPARISON")
        print("=" * 70)
        
        old = self.analyze_archive(archive1_path, label1)
        new = self.analyze_archive(archive2_path, label2)
        
        if not old or not new:
            print("\n❌ Error: Could not analyze one or both archives")
            return
        
        print("\n" + "=" * 70)
        print("📊 GROWTH METRICS")
        print("=" * 70)
        
        # Calculate changes
        changes = {
            'followers': new['followers'] - old['followers'],
            'following': new['following'] - old['following'],
            'mutual': new['mutual'] - old['mutual'],
            'tweets': new['tweets'] - old['tweets'],
            'likes': new['likes'] - old['likes'],
            'engagement_rate': new['engagement_rate'] - old['engagement_rate'],
            'follower_ratio': new['follower_ratio'] - old['follower_ratio']
        }
        
        def format_change(value, is_percentage=False):
            """Format change with color indicator"""
            if value > 0:
                symbol = "📈 +"
            elif value < 0:
                symbol = "📉 "
            else:
                symbol = "➡️  "
            
            if is_percentage:
                return f"{symbol}{value:.1f}%"
            else:
                return f"{symbol}{value}"
        
        print(f"\n👥 Network Growth:")
        print(f"   Followers: {old['followers']} → {new['followers']} {format_change(changes['followers'])}")
        print(f"   Following: {old['following']} → {new['following']} {format_change(changes['following'])}")
        print(f"   Mutual Connections: {old['mutual']} → {new['mutual']} {format_change(changes['mutual'])}")
        
        print(f"\n📱 Content Activity:")
        print(f"   Tweets: {old['tweets']} → {new['tweets']} {format_change(changes['tweets'])}")
        print(f"   Likes: {old['likes']} → {new['likes']} {format_change(changes['likes'])}")
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Engagement Rate: {old['engagement_rate']:.1f}% → {new['engagement_rate']:.1f}% {format_change(changes['engagement_rate'], True)}")
        print(f"   Follower Ratio: {old['follower_ratio']:.2f} → {new['follower_ratio']:.2f} {format_change(changes['follower_ratio'])}")
        
        # Analyze follower changes
        print("\n" + "=" * 70)
        print("🔍 DETAILED CHANGES")
        print("=" * 70)
        
        # New followers
        new_followers = new['follower_ids'] - old['follower_ids']
        lost_followers = old['follower_ids'] - new['follower_ids']
        
        print(f"\n👥 Follower Changes:")
        print(f"   New followers: {len(new_followers)}")
        print(f"   Lost followers: {len(lost_followers)}")
        print(f"   Net change: {format_change(len(new_followers) - len(lost_followers))}")
        
        # Following changes
        new_following = new['following_ids'] - old['following_ids']
        unfollowed = old['following_ids'] - new['following_ids']
        
        print(f"\n👤 Following Changes:")
        print(f"   New accounts followed: {len(new_following)}")
        print(f"   Accounts unfollowed: {len(unfollowed)}")
        print(f"   Net change: {format_change(len(new_following) - len(unfollowed))}")
        
        # Growth rate
        if old['followers'] > 0:
            follower_growth_rate = (changes['followers'] / old['followers']) * 100
            print(f"\n📈 Growth Rate:")
            print(f"   Follower growth: {follower_growth_rate:+.1f}%")
        
        # Recommendations
        print("\n" + "=" * 70)
        print("💡 RECOMMENDATIONS")
        print("=" * 70)
        
        if changes['followers'] <= 0:
            print("\n⚠️  Follower Decline Detected")
            print("   • Focus on creating more engaging content")
            print("   • Increase posting frequency")
            print("   • Engage more with your community")
        elif changes['followers'] > 0 and changes['followers'] < 10:
            print("\n📊 Slow Growth")
            print("   • You're growing, but there's room for improvement")
            print("   • Try posting at peak hours")
            print("   • Use relevant hashtags")
        else:
            print("\n🎉 Great Growth!")
            print("   • Keep doing what you're doing")
            print("   • Maintain consistency")
            print("   • Continue engaging with your audience")
        
        if changes['engagement_rate'] < 0:
            print("\n⚠️  Engagement Rate Dropped")
            print("   • Review who you're following")
            print("   • Engage more with mutual connections")
            print("   • Build stronger relationships")
        
        if changes['tweets'] < 5:
            print("\n📝 Low Content Production")
            print("   • Try to post more regularly")
            print("   • Aim for 3-5 tweets per week")
            print("   • Share valuable insights")
        
        print("\n" + "=" * 70)
        
        # Save comparison report
        report = {
            'comparison_date': datetime.now().isoformat(),
            'old_archive': {
                'label': label1,
                'metrics': {k: v for k, v in old.items() if k not in ['follower_ids', 'following_ids']}
            },
            'new_archive': {
                'label': label2,
                'metrics': {k: v for k, v in new.items() if k not in ['follower_ids', 'following_ids']}
            },
            'changes': changes,
            'new_followers_count': len(new_followers),
            'lost_followers_count': len(lost_followers),
            'new_following_count': len(new_following),
            'unfollowed_count': len(unfollowed)
        }
        
        report_file = Path('growth_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file.absolute()}")
        print("=" * 70 + "\n")
    
    def track_progress(self, archive_path, target_followers=None, target_engagement=None):
        """Track progress towards goals"""
        print("=" * 70)
        print("🎯 GOAL TRACKING")
        print("=" * 70)
        
        metrics = self.analyze_archive(archive_path, "Current")
        
        if not metrics:
            return
        
        print("\n📊 Current Status:")
        print(f"   Followers: {metrics['followers']}")
        print(f"   Engagement Rate: {metrics['engagement_rate']:.1f}%")
        print(f"   Follower Ratio: {metrics['follower_ratio']:.2f}")
        
        if target_followers:
            remaining = target_followers - metrics['followers']
            progress = (metrics['followers'] / target_followers) * 100
            print(f"\n🎯 Follower Goal: {target_followers}")
            print(f"   Current: {metrics['followers']}")
            print(f"   Remaining: {remaining}")
            print(f"   Progress: {progress:.1f}%")
            
            if remaining > 0:
                print(f"\n💡 To reach your goal:")
                print(f"   • Need {remaining} more followers")
                print(f"   • At 10 followers/month: {remaining/10:.1f} months")
                print(f"   • At 20 followers/month: {remaining/20:.1f} months")
        
        if target_engagement:
            current_eng = metrics['engagement_rate']
            remaining_eng = target_engagement - current_eng
            print(f"\n🎯 Engagement Goal: {target_engagement}%")
            print(f"   Current: {current_eng:.1f}%")
            print(f"   Remaining: {remaining_eng:.1f}%")
            
            if remaining_eng > 0:
                mutual_needed = int((target_engagement / 100) * metrics['following'] - metrics['mutual'])
                print(f"\n💡 To reach your goal:")
                print(f"   • Need {mutual_needed} more mutual connections")
                print(f"   • Engage with accounts you follow")
                print(f"   • Build genuine relationships")
        
        print("\n" + "=" * 70 + "\n")


def main():
    import sys
    
    tracker = TwitterGrowthTracker()
    
    print("\n📈 Twitter Growth Tracker\n")
    print("Options:")
    print("1. Compare two archives (track growth)")
    print("2. Track progress towards goals")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n📊 Archive Comparison\n")
        old_path = input("Enter path to OLD archive: ").strip()
        new_path = input("Enter path to NEW archive: ").strip()
        
        if not Path(old_path).exists() or not Path(new_path).exists():
            print("\n❌ One or both paths do not exist")
            return
        
        tracker.compare_archives(old_path, new_path)
        
    elif choice == "2":
        print("\n🎯 Goal Tracking\n")
        archive_path = input("Enter path to archive: ").strip()
        
        if not Path(archive_path).exists():
            print("\n❌ Path does not exist")
            return
        
        target_followers = input("Target follower count (press Enter to skip): ").strip()
        target_engagement = input("Target engagement rate % (press Enter to skip): ").strip()
        
        target_followers = int(target_followers) if target_followers else None
        target_engagement = float(target_engagement) if target_engagement else None
        
        tracker.track_progress(archive_path, target_followers, target_engagement)
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()

