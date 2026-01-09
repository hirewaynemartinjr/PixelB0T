📋 Overview
PixelB0T is a production Discord bot designed to solve real-world team coordination challenges. It manages availability across multiple games/projects, handles 100+ timezone formats, and exports calendar data for 20+ active users.
Problem Solved: Coordinating team availability across global timezones is difficult. PixelB0T automates weekly availability collection, timezone conversion, and calendar generation.

✨ Key Features
Core Functionality

Multi-game support - Separate availability tracking for different projects/games
Flexible input parsing - Accepts emoji reactions (1-7) or text ("Monday 5-9 PM, Friday 8-11 PM")
100+ timezone shortcuts - Supports global timezones (PST, EST, GMT, JST, etc.)
Calendar export - Generates .ics files for Google Calendar integration
Automated weekly polls - Posts availability check every Sunday at 00:00 UTC

Production Features

Automated backups - 6-hour rotation with timestamped snapshots
Health monitoring - System resource tracking and uptime reporting
Graceful shutdown - Data persistence on service restarts
Error handling - Comprehensive logging and user-friendly error messages
Data isolation - Multi-game data stored separately to prevent conflicts


🏗️ Architecture
Technology Stack
Frontend:  Discord (User Interface)
Backend:   Python 3.8+ with discord.py
Storage:   JSON (availability.json, user_tzs.json)
Hosting:   Oracle Cloud Infrastructure (OCI)
Service:   systemd daemon with auto-restart
Backups:   Automated 6-hour rotation
System Architecture
User Input → Discord → PixelB0T (Python) → JSON Storage
                           ↓
                    systemd Service
                           ↓
                  Automated Backups (6hr)
                           ↓
                  Health Monitoring & Logs

🚀 Technical Highlights
Advanced Parsing
Handles multiple input formats:
python# Emoji reactions (1-7 for days of week)
✅ React with 1️⃣ 3️⃣ 5️⃣ = Monday, Wednesday, Friday

# Text input (flexible formats)
✅ "Monday 5-9 PM, Wednesday 5-9 PM, Friday 5-11 PM"
✅ "1,3,5"
✅ "Mon, Wed, Fri"
Timezone Intelligence
Supports 100+ timezone formats:
python'PST', 'EST', 'CST', 'MST'        # US timezones
'GMT', 'UTC', 'BST', 'CET'        # Europe
'JST', 'KST', 'IST', 'AEST'       # Asia-Pacific
'US/Eastern', 'America/New_York'   # Full IANA names
Production Deployment
bash# Deployed as systemd service
[Unit]
Description=PixelB0T Discord Availability Bot
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc
ExecStart=/usr/bin/python3 /home/opc/availability_bot.py
Restart=always

[Install]
WantedBy=multi-user.target

📊 Commands Reference
User Commands
CommandDescriptionExample!available <days>Set your weekly availability!available Monday 5-9 PM, Friday 8-11 PM!myavailabilityView your current availability!myavailability!settimezone <tz>Set your timezone!settimezone EST!mytimezoneView your timezone setting!mytimezone!calendarExport team calendar (.ics)!calendar!clearRemove your availability!clear
Admin Commands
CommandDescription!pollManually trigger weekly poll!allavailabilityView all team availability!uptimeSystem health & resource stats

🔧 Installation & Deployment
Prerequisites
bash# System requirements
Python 3.8+
pip3
systemd (for service management)
Oracle Cloud Infrastructure account (or any Linux VPS)
Quick Start
bash# 1. Clone repository
git clone https://github.com/hirewaynemartinjr/PixelB0T.git
cd PixelB0T

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Configure environment
echo "DISCORD_TOKEN=your_token_here" > .env

# 4. Run bot
python3 availability_bot.py
Production Deployment (systemd)
bash# 1. Create service file
sudo nano /etc/systemd/system/availabilitybot.service

# 2. Add configuration (see Architecture section)

# 3. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable availabilitybot
sudo systemctl start availabilitybot

# 4. Monitor
sudo systemctl status availabilitybot
tail -f /home/opc/availabilitybot.log

📁 Project Structure
PixelB0T/
├── availability_bot.py          # Main bot code
├── requirements.txt              # Python dependencies
├── .env                          # Discord token (not in repo)
├── availability.json             # Availability data
├── user_tzs.json                 # User timezone preferences
├── availabilitybot.log           # Activity logs
├── backup/                       # Automated backups
│   ├── availability_20260109_120000.json
│   └── user_tzs_20260109_120000.json
├── maintenance_suite.sh          # Admin management console
├── update_manager.sh             # Deployment automation
└── README.md                     # This file

💡 Use Cases
Gaming Communities:
Coordinate raid schedules, team practice sessions, tournament availability
Remote Teams:
Track working hours across global timezones for project collaboration
Event Planning:
Collect availability for meetings, events, or group activities

🛠️ Technologies Used

Python 3.8+ - Core language
discord.py 2.0+ - Discord API wrapper
pytz - Timezone handling
psutil - System resource monitoring
systemd - Service management
Oracle Cloud Infrastructure - Production hosting
JSON - Data persistence


📈 Performance Metrics

Uptime: 99.9% (6 months production)
Users: 20+ active users
Response Time: <100ms average
Memory Usage: ~250MB RAM
CPU Usage: <1% average
Backup Frequency: Every 6 hours
Data Integrity: 100% (no data loss in 6 months)


🔒 Security & Reliability

✅ Environment variables for sensitive tokens
✅ Automated backup system with rotation
✅ Graceful shutdown handling
✅ Error logging and monitoring
✅ Service auto-restart on failure
✅ Data validation on all inputs


🚧 Future Enhancements

 PostgreSQL database migration (scale beyond JSON)
 Web dashboard for availability visualization
 Conflict detection (overlapping times)
 Advanced analytics (participation tracking)
 Multi-server support
 Integration with Google Calendar API


📄 License
MIT License - See LICENSE file for details

🤝 Contributing
This is a personal project showcasing production deployment and DevOps skills. Feel free to fork and adapt for your own use!

📞 Contact
Questions or feedback? Open an issue or reach out:

Email: hirewaynemartinjr@gmail.com
GitHub: @hirewaynemartinjr


Built with Python. Deployed on OCI. Serving real users in production.
