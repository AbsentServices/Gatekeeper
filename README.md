# Gatekeeper Bot

A modular Discord security bot designed for global blacklist enforcement, local guild whitelisting, and logging using a local SQLite database.

## Features
- **Global Network Blacklist**: Ban or auto-kick blacklisted users across all shared servers upon joining.
- **Guild Whitelisting**: Exclude specific users per server from security filters.
- **Custom Logging**: Route auto-kick notifications to designated log channels.
- **Local SQLite Backend**: Zero external cloud database dependencies.



## Set up a virtual environment and install dependencies:

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install .
Configure your environment variables:
Copy .env.example to .env and insert your Discord Bot Token:

Code snippet
DISCORD_TOKEN=your_actual_bot_token_here
Run the bot:

Bash
python gatekeeper.py

---

### Step 4: Commit and push package files to GitHub

Run the following commands in your terminal:

```bash
# Add newly created package files
git add pyproject.toml README.md cogs/__init__.py

# Commit changes
git commit -m "Add pyproject.toml package metadata and README documentation"

# Push to GitHub
git push origin main