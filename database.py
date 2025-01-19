def _setup_database(self):
    """Initialize database tables"""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        
        # Create users table with premium fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            remaining_analyses INTEGER DEFAULT 2,
            referral_code TEXT UNIQUE,
            referred_by TEXT,
            is_premium BOOLEAN DEFAULT 0,
            premium_expiry TIMESTAMP,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

def update_premium_status(self, user_id: int, expiration_date: datetime) -> bool:
    """Update user's premium status"""
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE users 
            SET is_premium = 1,
                premium_expiry = ?,
                remaining_analyses = -1
            WHERE user_id = ?
            ''', (expiration_date.strftime('%Y-%m-%d %H:%M:%S'), user_id))
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating premium status: {e}")
        return False

def remove_premium_status(self, user_id: int) -> bool:
    """Remove user's premium status"""
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE users 
            SET is_premium = 0,
                premium_expiry = NULL,
                remaining_analyses = 2
            WHERE user_id = ?
            ''', (user_id,))
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error removing premium status: {e}")
        return False

def get_premium_info(self, user_id: int) -> Optional[Dict]:
    """Get user's premium information"""
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT is_premium, premium_expiry
            FROM users 
            WHERE user_id = ? AND is_premium = 1
            ''', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'is_premium': bool(row[0]),
                    'expiration_date': row[1]
                }
            return None
    except Exception as e:
        logger.error(f"Error getting premium info: {e}")
        return None

def get_all_premium_users(self) -> List[Dict]:
    """Get all premium users"""
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, username, premium_expiry
            FROM users 
            WHERE is_premium = 1
            ORDER BY premium_expiry DESC
            ''')
            
            return [{
                'user_id': row[0],
                'username': row[1],
                'expiration_date': row[2]
            } for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting premium users: {e}")
        return []

def check_premium_status(self, user_id: int) -> bool:
    """Check if user has active premium status"""
    try:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT 1
            FROM users 
            WHERE user_id = ? 
              AND is_premium = 1 
              AND premium_expiry > datetime('now')
            ''', (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
        return False
