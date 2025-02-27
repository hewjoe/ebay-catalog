"""
Configuration handling for the eBay Auction Tracker.
"""
import argparse
import logging
import os
import yaml
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'name': 'ebay_tracker',
        'user': 'postgres',
        'password': '',
    },
    'ebay': {
        'api_key': None,  # For eBay API usage if available
        'use_scraping': True,  # Fall back to scraping if no API key
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'request_delay': 2,  # Seconds between requests to avoid rate limiting
    },
    'search': {
        'pattern': 'rtx 3090',
        'auction_period': 24,  # Hours
        'completed_period': 48,  # Hours
        'excluded_terms': ['broken', 'not working', 'for parts', 'repair', 'faulty'],
    },
    'daemon': {
        'polling_interval': 30,  # Minutes
    },
    'logging': {
        'level': 'INFO',
    }
}

def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found")
        return {}
        
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return {}

def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two configuration dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
            
    return result

def args_to_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Convert command line arguments to a configuration dictionary."""
    config = {}
    
    # Database settings
    if any([args.db_host, args.db_port, args.db_name, args.db_user, args.db_password]):
        config['database'] = {}
        if args.db_host:
            config['database']['host'] = args.db_host
        if args.db_port:
            config['database']['port'] = args.db_port
        if args.db_name:
            config['database']['name'] = args.db_name
        if args.db_user:
            config['database']['user'] = args.db_user
        if args.db_password:
            config['database']['password'] = args.db_password
    
    # Search settings
    if args.search_pattern or args.auction_period or args.completed_period:
        config['search'] = {}
        if args.search_pattern:
            config['search']['pattern'] = args.search_pattern
        if args.auction_period:
            config['search']['auction_period'] = args.auction_period
        if args.completed_period:
            config['search']['completed_period'] = args.completed_period
    
    # Daemon settings
    if args.polling_interval:
        config['daemon'] = {'polling_interval': args.polling_interval}
    
    # Logging settings
    if args.log_level:
        config['logging'] = {'level': args.log_level}
    
    return config

def load_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Load configuration from default values, config file, and command line arguments.
    Command line arguments take precedence over config file, which takes precedence over defaults.
    """
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Load from config file if specified
    if args.config:
        file_config = load_config_file(args.config)
        config = merge_configs(config, file_config)
    
    # Override with command line arguments
    args_config = args_to_config(args)
    config = merge_configs(config, args_config)
    
    return config 