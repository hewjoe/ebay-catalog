"""
Database operations for the eBay Auction Tracker.
"""
import logging
import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Handles all database operations for the eBay Auction Tracker."""
    
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize with database configuration."""
        self.config = db_config
        self.conn = None
        
    def _get_connection(self):
        """Get a database connection, creating one if necessary."""
        if self.conn is None or self.conn.closed:
            logger.debug("Creating new database connection")
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                dbname=self.config['name'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.conn.autocommit = False
        return self.conn
    
    def initialize_schema(self):
        """Create the database schema if it doesn't exist."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            # Create tables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                id SERIAL PRIMARY KEY,
                ebay_user_id VARCHAR(255) UNIQUE NOT NULL,
                rating FLOAT,
                feedback_score INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS auctions (
                id SERIAL PRIMARY KEY,
                item_id VARCHAR(255) UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                seller_id INTEGER REFERENCES sellers(id),
                search_pattern VARCHAR(255) NOT NULL,
                description TEXT,
                condition VARCHAR(255),
                current_price NUMERIC(10, 2),
                buy_it_now_price NUMERIC(10, 2),
                shipping_cost NUMERIC(10, 2),
                num_bids INTEGER DEFAULT 0,
                auction_end_time TIMESTAMP NOT NULL,
                auction_start_time TIMESTAMP,
                auction_status VARCHAR(50) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS item_specifics (
                id SERIAL PRIMARY KEY,
                auction_id INTEGER REFERENCES auctions(id) ON DELETE CASCADE,
                spec_key VARCHAR(255) NOT NULL,
                spec_value TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (auction_id, spec_key)
            );
            
            CREATE TABLE IF NOT EXISTS bids (
                id SERIAL PRIMARY KEY,
                auction_id INTEGER REFERENCES auctions(id) ON DELETE CASCADE,
                bid_amount NUMERIC(10, 2) NOT NULL,
                bid_time TIMESTAMP NOT NULL,
                bidder_id VARCHAR(255),
                winning_bid BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_auctions_search_pattern ON auctions(search_pattern);
            CREATE INDEX IF NOT EXISTS idx_auctions_auction_end_time ON auctions(auction_end_time);
            CREATE INDEX IF NOT EXISTS idx_auctions_auction_status ON auctions(auction_status);
            CREATE INDEX IF NOT EXISTS idx_item_specifics_key ON item_specifics(spec_key);
            CREATE INDEX IF NOT EXISTS idx_bids_auction_id ON bids(auction_id);
            """)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    def get_seller_id(self, seller_data: Dict[str, Any]) -> int:
        """Get the seller ID, creating a new record if necessary."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            # Try to find existing seller
            cursor.execute(
                "SELECT id FROM sellers WHERE ebay_user_id = %s",
                (seller_data['ebay_user_id'],)
            )
            result = cursor.fetchone()
            
            if result:
                # Update seller data
                cursor.execute(
                    """
                    UPDATE sellers 
                    SET rating = %s, feedback_score = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (seller_data.get('rating'), seller_data.get('feedback_score'), result[0])
                )
                return result[0]
            else:
                # Insert new seller
                cursor.execute(
                    """
                    INSERT INTO sellers (ebay_user_id, rating, feedback_score)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        seller_data['ebay_user_id'],
                        seller_data.get('rating'),
                        seller_data.get('feedback_score')
                    )
                )
                return cursor.fetchone()[0]
    
    def save_items(self, items: List[Dict[str, Any]]) -> None:
        """Save or update multiple auction items."""
        if not items:
            return
            
        conn = self._get_connection()
        try:
            for item in items:
                self.save_item(item, conn)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving items: {e}", exc_info=True)
            raise
    
    def save_item(self, item: Dict[str, Any], conn=None) -> Optional[int]:
        """Save or update an auction item."""
        if conn is None:
            conn = self._get_connection()
            should_commit = True
        else:
            should_commit = False
            
        try:
            with conn.cursor() as cursor:
                # Get or create seller
                seller_id = self.get_seller_id(item['seller'])
                
                # Check if auction already exists
                cursor.execute(
                    "SELECT id FROM auctions WHERE item_id = %s",
                    (item['item_id'],)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing auction
                    auction_id = result[0]
                    cursor.execute(
                        """
                        UPDATE auctions SET
                            title = %s,
                            url = %s,
                            seller_id = %s,
                            description = %s,
                            condition = %s,
                            current_price = %s,
                            buy_it_now_price = %s,
                            shipping_cost = %s,
                            num_bids = %s,
                            auction_status = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            item['title'],
                            item['url'],
                            seller_id,
                            item.get('description'),
                            item.get('condition'),
                            item.get('current_price'),
                            item.get('buy_it_now_price'),
                            item.get('shipping_cost'),
                            item.get('num_bids', 0),
                            item['auction_status'],
                            auction_id
                        )
                    )
                else:
                    # Insert new auction
                    cursor.execute(
                        """
                        INSERT INTO auctions (
                            item_id, title, url, seller_id, search_pattern,
                            description, condition, current_price, buy_it_now_price,
                            shipping_cost, num_bids, auction_end_time, auction_start_time,
                            auction_status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            item['item_id'],
                            item['title'],
                            item['url'],
                            seller_id,
                            item['search_pattern'],
                            item.get('description'),
                            item.get('condition'),
                            item.get('current_price'),
                            item.get('buy_it_now_price'),
                            item.get('shipping_cost'),
                            item.get('num_bids', 0),
                            item['auction_end_time'],
                            item.get('auction_start_time'),
                            item['auction_status']
                        )
                    )
                    auction_id = cursor.fetchone()[0]
                
                # Save item specifics
                if 'item_specifics' in item and item['item_specifics']:
                    for key, value in item['item_specifics'].items():
                        cursor.execute(
                            """
                            INSERT INTO item_specifics (auction_id, spec_key, spec_value)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (auction_id, spec_key) 
                            DO UPDATE SET spec_value = EXCLUDED.spec_value
                            """,
                            (auction_id, key, value)
                        )
                
                # Save bids if available
                if 'bids' in item and item['bids']:
                    for bid in item['bids']:
                        cursor.execute(
                            """
                            INSERT INTO bids (
                                auction_id, bid_amount, bid_time, bidder_id, winning_bid
                            ) VALUES (
                                %s, %s, %s, %s, %s
                            )
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                auction_id,
                                bid['amount'],
                                bid['time'],
                                bid.get('bidder_id'),
                                bid.get('winning_bid', False)
                            )
                        )
                
                if should_commit:
                    conn.commit()
                    
                return auction_id
                
        except Exception as e:
            if should_commit:
                conn.rollback()
            logger.error(f"Error saving item {item.get('item_id')}: {e}", exc_info=True)
            raise
    
    def get_active_auctions(self) -> List[Dict[str, Any]]:
        """Get all active auctions that we're tracking."""
        conn = self._get_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                """
                SELECT a.*, s.ebay_user_id as seller_username
                FROM auctions a
                JOIN sellers s ON a.seller_id = s.id
                WHERE a.auction_status = 'active'
                """
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_completed_items(self, items: List[Dict[str, Any]]) -> None:
        """Update information for completed auction items."""
        if not items:
            return
            
        conn = self._get_connection()
        try:
            for item in items:
                # Mark as completed and update final price and bids
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE auctions SET
                            auction_status = 'completed',
                            current_price = %s,
                            num_bids = %s,
                            updated_at = NOW()
                        WHERE item_id = %s
                        RETURNING id
                        """,
                        (
                            item.get('final_price'),
                            item.get('num_bids', 0),
                            item['item_id']
                        )
                    )
                    result = cursor.fetchone()
                    
                    if result and 'bids' in item and item['bids']:
                        auction_id = result[0]
                        # Add the winning bid
                        winning_bid = item['bids'][-1] if item['bids'] else None
                        
                        if winning_bid:
                            cursor.execute(
                                """
                                INSERT INTO bids (
                                    auction_id, bid_amount, bid_time, bidder_id, winning_bid
                                ) VALUES (
                                    %s, %s, %s, %s, TRUE
                                )
                                ON CONFLICT DO NOTHING
                                """,
                                (
                                    auction_id,
                                    winning_bid['amount'],
                                    winning_bid['time'],
                                    winning_bid.get('bidder_id')
                                )
                            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating completed items: {e}", exc_info=True)
            raise
            
    def close(self):
        """Close the database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.debug("Database connection closed") 