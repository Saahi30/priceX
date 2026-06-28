# Unlisted Market Data Scraper

This repository contains an automated price tracking scraper that fetches data for unlisted shares from **UnlistedZone** and **SharesCart**. The data is compiled, normalized, and saved into a comprehensive `stocks_data.json` file.

## Features

- **Multi-Source Scraping:** Pulls real-time pricing and fundamental data from multiple brokers.
- **Intelligent Merging (Backup Pricing):** **UnlistedZone** is treated as the primary source of truth. When **SharesCart** is scraped, the system uses fuzzy string matching to find the corresponding UnlistedZone record. If a match is found, the SharesCart price is saved as a `backup_price` within the primary record.
- **Priority Mode:** Allows for ultra-fast scraping of specific stocks (defined in `priority_stocks.json`) rather than parsing the entire database.

## Usage

Run the scraper locally by executing `main.py` as a module. You must specify a `--mode` and can optionally specify a `--source`.

### Modes
- `--mode high-priority`: Scrapes only the URLs/slugs defined in `priority_stocks.json`.
- `--mode all`: Scrapes all available stocks on the active platforms.

### Sources
- `--source all` (Default): Scrapes UnlistedZone first, then SharesCart, and merges the data.
- `--source unlistedzone`: Scrapes only UnlistedZone.
- `--source sharescart`: Scrapes only SharesCart.

**Examples:**
```bash
# Scrape all data from all platforms
python -m scraper.main --mode all --source all

# Fast update for priority stocks only, using both platforms
python -m scraper.main --mode high-priority --source all

# Scrape only UnlistedZone's full directory
python -m scraper.main --mode all --source unlistedzone
```

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
   - Go to **Settings > Actions > General**. Under "Workflow permissions", ensure it is set to **Read and write permissions**. This is required so the bot can commit the updated `stocks_data.json` back to the repository.

4. **Modify Priority Stocks:**
   - To change which stocks update quickly, edit the array of URLs in `priority_stocks.json`.

## Accessing the Data

Your external tools and frontend dashboards can access the latest prices at any time by fetching the raw JSON URL:
`https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO_NAME/main/stocks_data.json`
*(If your repository is private, you will need to generate a Personal Access Token to pass in the Authorization header).*
