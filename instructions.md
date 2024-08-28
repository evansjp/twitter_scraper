Step 1:
Open Google Chrome & make sure you've logged into Twitter with your scraper account before.

Step 2:
Go to credentials.txt and enter your Twitter username and password.

Step 3:
Go to accounts_to_scrape.txt and enter the Twitter accounts you want to scrape. Each account should be on a new line.

Step 4:
Open the terminal & run `chmod +x simple_twitter_scraper.py`

Step 5:
Enter `crontab -e` & add the following line (replace /path/to/ with the path to the simple_twitter_scraper.py file):
`0 * * * * /usr/bin/python3 /path/to/simple_twitter_scraper.py`
