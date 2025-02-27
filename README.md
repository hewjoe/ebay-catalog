# eBay Auction Tracker

A Python application that tracks RTX 3090 graphics card auctions on eBay and stores the data in PostgreSQL for analysis with Grafana dashboards.

## Overview

This application helps you track eBay auctions for specific items (initially focused on RTX 3090 graphics cards) to identify pricing trends and find good deals. It extracts detailed information about each listing, including seller information, item specifics, auction status, and bid history.

## Features

- Search eBay for auctions matching specific search patterns
- Filter out non-working or damaged items
- Focus on auctions ending within a configurable time window
- Track auction progress and final sale prices
- Store comprehensive data in PostgreSQL for analysis
- Track bidding history and winning bids
- Containerized setup with Docker and Docker Compose
- Integration with Grafana for data visualization and insights
- Configurable via command-line arguments or YAML configuration file

## Prerequisites

- Docker and Docker Compose
- Internet access to reach eBay

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ebay-auction-tracker.git
   cd ebay-auction-tracker
   ```

2. Create a `config.yaml` file or use the provided example.

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. Initialize the database schema:
   ```bash
   docker-compose exec app python -m ebay_auction_tracker.main --initialize-db
   ```

## Usage

### Running in Docker

The Docker Compose configuration includes three services:
- `app`: The eBay Auction Tracker application
- `db`: PostgreSQL database for storing auction data
- `grafana`: Grafana for visualizing the data

Start all services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f app
```

### Command Line Options

The application can be run with various command-line options:

```
usage: main.py [-h] [--daemon] [--config CONFIG] [--initialize-db]
               [--search-pattern SEARCH_PATTERN]
               [--auction-period AUCTION_PERIOD]
               [--completed-period COMPLETED_PERIOD]
               [--polling-interval POLLING_INTERVAL]
               [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
               [--db-host DB_HOST] [--db-port DB_PORT] [--db-name DB_NAME]
               [--db-user DB_USER] [--db-password DB_PASSWORD]

Track eBay RTX 3090 auctions

optional arguments:
  -h, --help            show this help message and exit
  --daemon              Run in daemon mode
  --config CONFIG       Path to configuration file
  --initialize-db       Initialize the database schema
  --search-pattern SEARCH_PATTERN
                        Search pattern for eBay
  --auction-period AUCTION_PERIOD
                        Only include auctions ending within this many hours (default: 24)
  --completed-period COMPLETED_PERIOD
                        Check completed auctions from the past N hours (default: 48)
  --polling-interval POLLING_INTERVAL
                        Polling interval in minutes for daemon mode (default: 30)
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level
  --db-host DB_HOST     Database host
  --db-port DB_PORT     Database port
  --db-name DB_NAME     Database name
  --db-user DB_USER     Database user
  --db-password DB_PASSWORD
                        Database password
```

## Configuration

You can configure the application using a YAML file. Here's an example `config.yaml`:

```yaml
database:
  host: db
  port: 5432
  name: ebay_tracker
  user: postgres
  password: postgres

ebay:
  use_scraping: true
  request_delay: 3  # Seconds between requests to avoid rate limiting

search:
  pattern: rtx 3090
  auction_period: 24  # Hours
  completed_period: 48  # Hours
  excluded_terms:
    - broken
    - not working
    - for parts
    - repair
    - faulty
    - defective
    - dead

daemon:
  polling_interval: 30  # Minutes

logging:
  level: INFO
```

## Setting Up Grafana Dashboards

1. Access Grafana at http://localhost:3000 (default credentials: admin/admin)

2. Add a PostgreSQL data source:
   - Name: eBay Tracker
   - Host: db:5432
   - Database: ebay_tracker
   - User: postgres
   - Password: postgres
   - SSL Mode: disable

3. Create dashboards to monitor RTX 3090 prices. Some useful panels to create:
   - Average price over time
   - Price distribution
   - Number of auctions by day
   - Auctions ending soon with current price below average
   - Items with highest bid activity
   - Price comparison by item condition

## Database Schema

The application uses the following database tables:

- **sellers**: Information about eBay sellers
- **auctions**: Main auction details including prices, condition, and status
- **item_specifics**: Product specifications broken down by key/value pairs
- **bids**: Full bid history for tracked auctions

You can run SQL queries directly against these tables to build custom reports or use them as data sources in Grafana.

## Development

To set up a development environment:

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.