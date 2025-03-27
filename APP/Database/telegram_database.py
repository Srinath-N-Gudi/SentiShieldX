import sqlite3
import secrets
from pathlib import Path
from typing import Optional
import logging
class TelegramDatabase:
    def __init__(self):
        self.db_path = Path("instance") / "telegram_data.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Two tables: one for ID mapping, one for codes"""
        with self.conn:
            # Stores Telegram ID ↔ UUID links
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_mapping (
                    uuid TEXT PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    is_verified BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Stores active verification codes
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS verification_codes (
                    uuid TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    FOREIGN KEY (uuid) REFERENCES user_mapping(uuid)
                )
            """)

    def register_uuid(self, telegram_id: int, uuid: str):
        """Only stores the ID mapping - no codes"""
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO user_mapping (uuid, telegram_id) VALUES (?, ?)",
                (uuid, telegram_id)
            )

    def generate_verification_code(self, uuid: str) -> str:
        """Generates and stores a new code for the UUID"""
        code = f"{secrets.randbelow(10**10):010d}"
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO verification_codes VALUES (?, ?)",
                (uuid, code)  # expires_at set by default
            )
        return code

    def verify_code(self, telegram_id: int, input_code: str) -> bool:
        """Checks if the code matches for this Telegram ID"""
        with self.conn:
            # Get UUID linked to this Telegram ID
            uuid = self.conn.execute(
                "SELECT uuid FROM user_mapping WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchone()
            
            uuid = uuid[0]
            
            # Check code match
            code_match = self.conn.execute(
                "SELECT 1 FROM verification_codes WHERE uuid = ? AND code = ?",
                (uuid, input_code.strip())
            ).fetchone()
            
            if code_match:
                # Update verification status
                self.conn.execute(
                    "UPDATE user_mapping SET is_verified = TRUE WHERE uuid = ?",
                    (uuid,)
                )
                return True
            return False
        
    def get_telegram_id(self, uuid: str) -> Optional[int]:
        """Get Telegram ID associated with a given UUID
        
        Args:
            uuid: The user's unique identifier
            
        Returns:
            The Telegram ID if found, None otherwise
        """
        with self.conn:
            row = self.conn.execute(
                "SELECT telegram_id FROM user_mapping WHERE uuid = ?",
                (uuid,)
            ).fetchone()
            return row[0] if row else None
    def is_verified(self, telegram_id: int) -> bool:
        """Check if user is verified"""
        with self.conn:
            row = self.conn.execute(
                "SELECT is_verified FROM user_mapping WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchone()
            return bool(row and row[0]) if row else False