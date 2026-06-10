# UnlistedZone Price Tracker

This repository contains an automated price tracking scraper for UnlistedZone. It runs on a schedule using GitHub Actions and updates the `prices.csv` file automatically.

## How It Works

The scraper has two modes:
1. **High Priority (Twice Daily):** Scrapes only the 10-15 stocks defined in `priority_stocks.json`. This is incredibly fast and reduces server load.
2. **All Stocks (Every 3 Days):** Scrapes all available stocks on the website.

It runs completely unattended via `.github/workflows/scrape.yml`. The output is constantly appended/updated in `prices.csv`.

## Setup Instructions

To get this running on your own GitHub:

1. **Initialize Git Repository:**
   Open a terminal in this directory and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Push to GitHub:**
   - Create a new, empty repository on GitHub.
   - Run the commands GitHub provides to push your local code:
     ```bash
     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
     git branch -M main
     git push -u origin main
     ```

3. **Enable GitHub Actions:**
   - Go to the **Actions** tab of your repository on GitHub.
   - You may need to click "I understand my workflows, go ahead and enable them."
   - Go to **Settings > Actions > General**. Under "Workflow permissions", ensure it is set to **Read and write permissions**. This is required so the bot can commit the updated `prices.csv` back to the repository.

4. **Modify Priority Stocks:**
   - To change which stocks update twice daily, simply edit `priority_stocks.json` and push the changes.

## Accessing the Data

Your external tool can access the latest prices at any time by fetching the raw CSV URL:
`https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO_NAME/main/prices.csv`
*(If your repository is private, you will need to generate a Personal Access Token to pass in the Authorization header).*
