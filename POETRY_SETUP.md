# Twitter Analytics - Setup Guide with Poetry

## 🚀 Quick Setup Steps

### Prerequisites
- Python 3.8 or higher
- Poetry (install if needed)

### Step 1: Install Poetry (if not installed)
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or on macOS with Homebrew:
```bash
brew install poetry
```

### Step 2: Navigate to Project Directory
```bash
cd /Users/ajit.gupta/Desktop/HHpersonal/projects/twitter-analytics
```

### Step 3: Install Dependencies with Poetry
```bash
poetry install
```

### Step 4: Activate Virtual Environment
```bash
poetry shell
```

### Step 5: Run the Tools

#### Option A: Interactive Dashboard (Best!)
```bash
poetry run streamlit run dashboard.py
```

Or if you're in the poetry shell:
```bash
streamlit run dashboard.py
```

#### Option B: Advanced CLI Analysis
```bash
poetry run python advanced_analyzer.py "twitter-2025-11-18-753643d946ad97c385806a0b57293cc805c30525ff3f1f515cc2d4bd40112f50"
```

#### Option C: Export Data to CSV
```bash
poetry run python exporter.py "twitter-2025-11-18-753643d946ad97c385806a0b57293cc805c30525ff3f1f515cc2d4bd40112f50"
```

---

## 📋 All Commands at a Glance

```bash
# Setup
poetry install              # Install all dependencies
poetry shell               # Activate virtual environment

# Run Tools
streamlit run dashboard.py                    # Web dashboard
python advanced_analyzer.py "archive-path"    # CLI analysis
python exporter.py "archive-path"            # Export data
python growth_tracker.py                     # Track growth

# Manage Dependencies
poetry add package-name     # Add new package
poetry remove package-name  # Remove package
poetry update              # Update all packages
poetry show                # List installed packages
```

---

## 📦 What Gets Installed

### Core Dependencies
- `streamlit` (1.28.0) - Web dashboard
- `plotly` (5.17.0) - Interactive charts
- `pandas` (2.1.1) - Data manipulation
- `matplotlib` (3.8.0) - Static charts
- `seaborn` (0.13.0) - Statistical visualizations
- `numpy` (1.26.0) - Numerical operations

### Dev Dependencies (optional)
- `pytest` - Testing
- `black` - Code formatting
- `flake8` - Linting

---

## 🎯 Quick Test

After setup, test that everything works:

```bash
# Test 1: Run advanced analyzer
poetry run python advanced_analyzer.py "twitter-2025-11-18-753643d946ad97c385806a0b57293cc805c30525ff3f1f515cc2d4bd40112f50"

# Test 2: Launch dashboard
poetry run streamlit run dashboard.py
```

---

## 🔧 Troubleshooting

### Issue: "Poetry not found"
```bash
# Add Poetry to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"
```

### Issue: "Python version mismatch"
```bash
# Use specific Python version
poetry env use python3.9
poetry install
```

### Issue: "Module not found"
```bash
# Reinstall dependencies
poetry install --no-cache
```

---

## 📁 Your Archive Path

For convenience, your archive path is:
```
twitter-2025-11-18-753643d946ad97c385806a0b57293cc805c30525ff3f1f515cc2d4bd40112f50
```

---

## ✨ You're All Set!

Start with the dashboard:
```bash
poetry shell
streamlit run dashboard.py
```

**Have fun analyzing your Twitter data! 🚀**

