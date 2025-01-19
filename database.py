import sqlite3
import logging
from datetime import datetime
from typing import Optional, Tuple

from config import Config

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._setup_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _setup_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                remaining_analyses INTEGER DEFAULT 2,
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                subscription_type TEXT DEFAULT 'free',
                subscription_end_date TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()

    def get_user(self, user_id: int) -> Optional[Tuple]:
        """Get user information from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Database error in get_user: {e}")
            return None

    def add_user(self, user_id: int, username: str, first_name: str,
                 last_name: str, referral_code: str) -> bool:
        """Add new user to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, remaining_analyses, referral_code) 
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, 2, referral_code))
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error in add_user: {e}")
            return False

    def update_analyses_count(self, user_id: int, count: int) -> bool:
        """Update user's remaining analyses count"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE users 
                SET remaining_analyses = ?
                WHERE user_id = ?
                ''', (count, user_id))
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error in update_analyses_count: {e}")
            return False

    def process_referral(self, user_id: int, referrer_code: str) -> bool:
        """Process referral and update both users' analyses count"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if user has already been referred
                cursor.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
                if cursor.fetchone()[0]:
                    return False

                # Find referrer
                cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referrer_code,))
                referrer = cursor.fetchone()

                if referrer and referrer[0] != user_id:
                    # Update referred user
                    cursor.execute('''
                    UPDATE users 
                    SET remaining_analyses = remaining_analyses + ?,
                        referred_by = ?
                    WHERE user_id = ?
                    ''', (Config.REFERRAL_REWARD, referrer_code, user_id))

                    # Update referrer
                    cursor.execute('''
                    UPDATE users 
                    SET remaining_analyses = remaining_analyses + ?
                    WHERE user_id = ?
                    ''', (Config.REFERRAL_REWARD, referrer[0]))

                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Database error in process_referral: {e}")
            return False