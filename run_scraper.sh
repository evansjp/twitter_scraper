#!/bin/bash

# Activate the virtual environment
source /home/ubuntu/twitter_scraper/venv/bin/activate

# Ensure the correct PATH is set
# export PATH="/usr/local/bin:/usr/bin:/bin:/home/ubuntu/twitter_scraper/venv/bin:$PATH"

# Run the script using xvfb-run to simulate a display for headless Chrome
xvfb-run -a /home/ubuntu/twitter_scraper/venv/bin/python3 /home/ubuntu/twitter_scraper/twitter_scraper.py

# Deactivate virtual environment (optional, but good practice)
deactivate
