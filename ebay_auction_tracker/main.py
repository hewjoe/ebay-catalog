#!/usr/bin/env python3
"""
eBay Auction Tracker for RTX 3090 Cards

This program tracks RTX 3090 listings on eBay and stores the data in PostgreSQL
for analysis with Grafana dashboards.
"""
import argparse
import logging
import signal
import sys
import time
from typing import Dict, Any

from .config import load_config
from .ebay_interface import EbayInterface
from .db import DatabaseHandler

logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Track eBay RTX 3090 auctions')
    
    # Running mode
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    
    # Configuration
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--initialize-db', action='store_true', help='Initialize the database schema')
    
    # Search parameters
    parser.add_argument('--search-pattern', type=str, help='Search pattern for eBay')
    parser.add_argument('--auction-period', type=int, default=24, 
                        help='Only include auctions ending within this many hours (default: 24)')
    parser.add_argument('--completed-period', type=int, default=48,
                        help='Check completed auctions from the past N hours (default: 48)')
    
    # Operation parameters
    parser.add_argument('--polling-interval', type=int, default=30,
                        help='Polling interval in minutes for daemon mode (default: 30)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Logging level')
    
    # Database connection
    parser.add_argument('--db-host', type=str, help='Database host')
    parser.add_argument('--db-port', type=int, help='Database port')
    parser.add_argument('--db-name', type=str, help='Database name')
    parser.add_argument('--db-user', type=str, help='Database user')
    parser.add_argument('--db-password', type=str, help='Database password')
    
    return parser.parse_args()

def setup_logging(log_level: str) -> None:
    """Set up logging with the specified level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def run_once(config: Dict[str, Any]) -> None:
    """Run the auction tracker once (adhoc mode)."""
    logger.info("Starting auction tracking in adhoc mode")
    
    db = DatabaseHandler(config['database'])
    ebay = EbayInterface(config['ebay'])
    
    # Search for active auctions
    active_items = ebay.search_active_items(
        config['search']['pattern'],
        config['search']['auction_period']
    )
    db.save_items(active_items)
    
    # Check completed auctions we're tracking
    completed_items = ebay.get_completed_items(
        config['search']['completed_period']
    )
    db.update_completed_items(completed_items)
    
    logger.info(f"Processed {len(active_items)} active and {len(completed_items)} completed items")

def run_daemon(config: Dict[str, Any]) -> None:
    """Run the auction tracker in daemon mode."""
    logger.info("Starting auction tracking in daemon mode")
    
    db = DatabaseHandler(config['database'])
    ebay = EbayInterface(config['ebay'])
    
    polling_interval = config['daemon']['polling_interval'] * 60  # Convert to seconds
    
    # Set up signal handling for graceful shutdown
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Shutdown signal received, exiting after current cycle")
        running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while running:
        try:
            start_time = time.time()
            
            # Search for active auctions
            active_items = ebay.search_active_items(
                config['search']['pattern'],
                config['search']['auction_period']
            )
            db.save_items(active_items)
            
            # Check completed auctions we're tracking
            completed_items = ebay.get_completed_items(
                config['search']['completed_period']
            )
            db.update_completed_items(completed_items)
            
            logger.info(f"Processed {len(active_items)} active and {len(completed_items)} completed items")
            
            # Calculate sleep time, ensuring we don't go negative
            elapsed = time.time() - start_time
            sleep_time = max(0, polling_interval - elapsed)
            
            if running:
                logger.info(f"Sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"Error in daemon loop: {e}", exc_info=True)
            # Sleep a bit before trying again
            time.sleep(60)

def main() -> None:
    """Main entry point for the application."""
    args = parse_arguments()
    setup_logging(args.log_level)
    
    logger.info("eBay Auction Tracker starting")
    
    # Load configuration from file and/or command line
    config = load_config(args)
    
    # Initialize database if requested
    if args.initialize_db:
        db = DatabaseHandler(config['database'])
        db.initialize_schema()
        logger.info("Database schema initialized")
        if not args.daemon:
            return
    
    # Run in the appropriate mode
    if args.daemon:
        run_daemon(config)
    else:
        run_once(config)
        
    logger.info("eBay Auction Tracker completed")

if __name__ == "__main__":
    main() 