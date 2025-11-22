# 🐦 Twitter Archive Analytics

A powerful analytics tool to extract insights from your Twitter/X data archive. This tool helps you understand your follower relationships, tweet patterns, engagement metrics, and much more!

## ✨ Features

### 📊 Key Insights
- **Follower Analysis**: Track followers vs following ratios
- **Mutual Connections**: Identify who you follow that follows you back
- **One-sided Follows**: Find accounts that don't follow you back
- **Engagement Metrics**: Calculate your engagement rate and social reach

### 📈 Visualizations
- Interactive follower/following pie charts
- Tweet activity timeline
- Activity heatmap (day vs hour)
- Top hashtags analysis
- Engagement trends over time

### 💡 Smart Recommendations
- Content strategy suggestions based on your data
- Follower growth opportunities
- Engagement optimization tips
- Connection management insights

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Your Twitter/X data archive (Download from Twitter Settings > Your Account > Download an archive)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Usage

#### Option 1: Command Line Analyzer
Simple text-based analysis tool:

```bash
python analyzer.py
```

Enter the path to your Twitter archive folder when prompted.

#### Option 2: Interactive Dashboard (Recommended)
Beautiful web-based dashboard with charts and visualizations:

```bash
streamlit run main.py
```

This will open a browser window with your interactive analytics dashboard.

## 📂 What Data is Analyzed?

Your Twitter archive contains:
- ✅ **Followers**: List of accounts following you
- ✅ **Following**: List of accounts you follow
- ✅ **Tweets**: All your tweets with metadata
- ✅ **Likes**: Tweets you've liked
- ✅ **Direct Messages**: Your DM history
- ✅ **Account Info**: Profile and account details
- ✅ **Engagement Data**: Retweets, replies, mentions

## 📊 Sample Insights

The tool provides insights like:

- **"You follow 52 accounts but only 5 follow you back"** - Helps identify one-sided relationships
- **"Your most active hour is 3:00 PM"** - Optimal posting times
- **"90% of your tweets are replies"** - Content mix analysis
- **"#AI is your most used hashtag"** - Topic analysis

## 🎯 Use Cases

1. **Personal Brand Optimization**: Understand your Twitter presence and optimize your content strategy
2. **Audience Analysis**: Learn who engages with your content
3. **Connection Management**: Identify valuable connections vs one-sided follows
4. **Content Planning**: Discover best times to post and trending topics
5. **Archive Exploration**: Dive deep into your Twitter history

## 🔒 Privacy & Security

- All analysis is done **locally** on your machine
- No data is sent to external servers
- Your Twitter archive remains private
- No API keys or authentication required

## 🛠️ Technical Details

### Built With
- **Python**: Core analytics engine
- **Streamlit**: Interactive web dashboard
- **Plotly**: Beautiful interactive charts
- **Pandas**: Data manipulation and analysis

### Architecture
```
twitter-analytics/
├── analyzer.py          # CLI-based analyzer
├── dashboard.py         # Web-based dashboard
├── requirements.txt     # Python dependencies
├── README.md           # Documentation
└── twitter-YYYY-MM-DD-*/  # Your Twitter archive
    └── data/
        ├── follower.js
        ├── following.js
        ├── tweets.js
        ├── likes.js
        └── ...
```

## 📖 How to Download Your Twitter Archive

1. Log in to Twitter/X
2. Go to **Settings and Privacy** > **Your Account** > **Download an archive of your data**
3. Confirm your password
4. Wait for Twitter to prepare your archive (can take 24-48 hours)
5. Download the ZIP file and extract it
6. Use the extracted folder path with this tool

## 🎨 Dashboard Features

### Interactive Elements
- **Metrics Cards**: Quick overview of key statistics
- **Dynamic Charts**: Hover for detailed information
- **Filtering Options**: Focus on specific time periods
- **Expandable Sections**: Dive deeper into specific areas

### Visualizations
1. **Follower Relationship Pie Chart**: Visual breakdown of mutual/one-sided follows
2. **Tweet Timeline**: Activity over time with trend lines
3. **Activity Heatmap**: Best posting times visualization
4. **Hashtag Bar Chart**: Your most used topics
5. **Engagement Metrics**: Comprehensive stats dashboard

## 🤝 Contributing

Ideas for improvements:
- [ ] Network graph visualization of connections
- [ ] Sentiment analysis of tweets
- [ ] Tweet engagement prediction
- [ ] Export reports to PDF
- [ ] Compare multiple archives over time
- [ ] Integration with Twitter API for live data

## 📝 Example Output

```
============================================================
👤 ACCOUNT OVERVIEW
============================================================

📝 Account Details:
   Username: @YourUsername
   Display Name: Your Name
   Account ID: 949939849796243456
   Created: 2018-01-07

============================================================
👥 FOLLOWER & FOLLOWING INSIGHTS
============================================================

📊 Basic Stats:
   Followers: 5
   Following: 52
   Follower/Following Ratio: 0.10

🤝 Mutual Connections:
   Mutual follows (friends): 2
   Followers you don't follow back: 3
   Following who don't follow back: 50
   
   Engagement rate: 3.8% of people you follow also follow you back
```

## 🐛 Troubleshooting

### "Path does not exist" error
- Make sure you've extracted the Twitter archive ZIP file
- Use the full path to the extracted folder
- Check that the folder contains a `data` subfolder

### "No data found" error
- Verify your archive is complete
- Check that .js files exist in the `data` folder
- Try downloading a fresh archive from Twitter

### Charts not displaying
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try updating Streamlit: `pip install --upgrade streamlit`

## 📄 License

This project is open source and available for personal use.

## 🙏 Acknowledgments

- Twitter/X for providing data export functionality
- Streamlit for the amazing dashboard framework
- The open-source community for inspiration

---

**Made with ❤️ for Twitter data enthusiasts**

**Note**: This tool is not affiliated with Twitter/X. It's an independent project for personal data analysis.

