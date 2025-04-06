import sqlite3
import secrets
from pathlib import Path
from typing import Optional
import logging
import json
from dataclasses import dataclass



# TelegramDataBase Keys

@dataclass
class TDB_KEYS:
    PROTECTION_ENABLED    = 'protection_enabled'
    MUTE_DURATION         = 'muteDuration'
    WARNING_MESSAGE       = 'warning_message'
    MUTE_COUNT            = 'repeat_offense_threshold'
    REPEAT_ACTION         = 'repeat_action'
    ALLOW_BANNING         = 'allow_banning'
    ADMIN_MESSAGE         = 'admin_message'
    TIMES_MUTED           = 'times_muted'
    WARNINGS              = 'warnings'
    IS_BANNED             = 'banned'
    BAN                   = 'ban'
    KICK                  = 'kick'

class TelegramDatabase:
    def __init__(self):
        """
        TelgramDatabase is a wrapper class to avoid writing sql code everywhere
        
        """
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

            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_installations (
            chat_id INTEGER PRIMARY KEY,  -- Telegram's unique chat identifier
            chat_title TEXT NOT NULL,
            chat_type TEXT NOT NULL CHECK(chat_type IN ('group', 'supergroup', 'channel')),
            adder_telegram_id INTEGER NOT NULL,  -- Who added the bot
            uuid TEXT NOT NULL,  -- Owner's UUID from user_mapping
            installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uuid) REFERENCES user_mapping(uuid)
            )
            """)

            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                chat_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0,
                FOREIGN KEY (chat_id) REFERENCES bot_installations(chat_id) ON DELETE CASCADE
            )
            """)
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (
            chat_id INTEGER PRIMARY KEY,
            uuid TEXT NOT NULL,
            settings_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY (uuid) REFERENCES user_mapping(uuid),
            FOREIGN KEY (chat_id) REFERENCES bot_installations(chat_id) ON DELETE CASCADE
                )
            """)
        # New table for tracking per-user stats in a group
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS group_user_stats (
                    chat_id INTEGER,
                    user_id INTEGER,
                    stats_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (chat_id, user_id),
                    FOREIGN KEY (chat_id) REFERENCES bot_installations(chat_id) ON DELETE CASCADE
                )
            """)

    def _get_default_stats(self):
        return {
            TDB_KEYS.TIMES_MUTED: 0,
            TDB_KEYS.WARNINGS: 0,
            TDB_KEYS.IS_BANNED: False
        }
    def _get_user_stats(self, chat_id, user_id):
        cur = self.conn.execute(
            "SELECT stats_json FROM group_user_stats WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None
    def _save_user_stats(self, chat_id, user_id, stats):
        stats_json = json.dumps(stats)
        self.conn.execute(
            "REPLACE INTO group_user_stats (chat_id, user_id, stats_json) VALUES (?, ?, ?)",
            (chat_id, user_id, stats_json)
        )
        self.conn.commit()
    def ensure_user(self, chat_id, user_id):
        stats = self._get_user_stats(chat_id, user_id)
        if stats is None:
            stats = self._get_default_stats()
            self._save_user_stats(chat_id, user_id, stats)

    def mute_user(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        stats[TDB_KEYS.TIMES_MUTED] += 1
        self._save_user_stats(chat_id, user_id, stats)
    def getMutedCount(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        return stats[TDB_KEYS.TIMES_MUTED]
    
    def resetMutedCount(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_default_stats()
        stats[TDB_KEYS.TIMES_MUTED] = 0
        self._save_user_stats(chat_id, user_id, stats)
    


    def warnUser(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        stats[TDB_KEYS.WARNINGS] += 1
        self._save_user_stats(chat_id, user_id, stats)

    def getWarningCount(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        return stats[TDB_KEYS.WARNINGS] if stats else 0

    def resetWarningCount(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        stats[TDB_KEYS.WARNINGS] = 0
        self._save_user_stats(chat_id, user_id, stats)
        
    def toggleBan(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        stats[TDB_KEYS.IS_BANNED] = not stats[TDB_KEYS.IS_BANNED]
        self._save_user_stats(chat_id, user_id, stats)

    def isBanned(self, chat_id, user_id):
        self.ensure_user(chat_id, user_id)
        stats = self._get_user_stats(chat_id, user_id)
        return stats[TDB_KEYS.IS_BANNED] if stats else False

    def update_user_stats(self, chat_id: int, user_id: int, new_stats: dict) -> bool:
        """
        Update the user stats for a group.
        new_stats should be a dictionary with keys and new values that you want to merge into the current stats.
        """
        self.ensure_user(chat_id, user_id)
        self._save_user_stats(chat_id, user_id, new_stats)
    def add_group_information(self, chat_id: int, chat_title: str, chat_type: str, 
                        adder_telegram_id: int, uuid: str) -> bool:
        """Add new group with atomic settings initialization"""
        with self.conn:
            try:
                # Insert to installations table
                self.conn.execute(
                    """INSERT INTO bot_installations 
                    (chat_id, chat_title, chat_type, adder_telegram_id, uuid)
                    VALUES (?, ?, ?, ?, ?)""",
                    (chat_id, chat_title, chat_type, adder_telegram_id, uuid)
                )
                
                # Initialize default settings
                self.conn.execute(
                    """INSERT INTO group_settings (chat_id, uuid) 
                    VALUES (?, ?)""",
                    (chat_id, uuid)
                )
                return True
            except sqlite3.IntegrityError as e:
                logging.error(f"Group addition failed: {e}")
                return False

    def retrieve_all_groups(self, uuid: str) -> list[dict]:
        """Get all groups with basic info for a user"""
        with self.conn:
            rows = self.conn.execute("""
                SELECT i.chat_id, i.chat_title, i.chat_type, 
                    i.installed_at, s.settings_json
                FROM bot_installations i
                JOIN group_settings s ON i.chat_id = s.chat_id
                WHERE i.uuid = ?
                """, (uuid,)).fetchall()
        return [dict(row) for row in rows]
    


    # In Database/telegram_database.py

    def get_group_info(self, chat_id: int, uuid: str) -> Optional[dict]:
        with self.conn:
            try:
                # Use chat_id as an integer, not a string.
                group = self.conn.execute(
                    "SELECT chat_id, chat_title, chat_type FROM bot_installations WHERE chat_id = ? AND uuid = ?",
                    (chat_id, uuid)
                ).fetchone()
                
                if not group:
                    return None
                        
                # Get existing settings if they exist
                settings_row = self.conn.execute(
                    "SELECT settings_json FROM group_settings WHERE chat_id = ?",
                    (chat_id,)
                ).fetchone()
                        
                # Merge with defaults, giving priority to saved settings
                default_settings = self.get_default_settings()
                saved_settings = json.loads(settings_row[0]) if settings_row else {}
                merged_settings = {**default_settings, **saved_settings}
                        
                return {
                    'id': group[0],
                    'name': group[1],
                    'type': group[2],
                    'settings': merged_settings
                }
            except Exception as e:
                logging.error(f"Error getting group info: {str(e)}")
                return None


    def get_default_settings(self) -> dict:
        """Return default hate speech protection settings"""
        warning_message = """    ⚠️ *Content Warning* ⚠️
    Your message was flagged by our AI protection system. 
    Our community has zero tolerance for hate speech, discrimination, or harmful content.
    *Consequences:*
    • 1st offense: After 3 warning you will be muted.
    • Repeated violations: You will be muted {mute_times} times. The next time you will be banned
    Please review our community guidelines and keep discussions respectful. 
    Continued violations will result in permanent removal.
    • *Tip*: Disagreements are fine, but keep it civil and focus on ideas, not individuals
    """
        ban_message = """
        You've been removed from {GroupName} for violating our community guidelines.

    Reason:
    ▸ Repeated inappropriate messages
    ▸ Violation of Rule #3: No hate speech

    Next Steps:
    ✓ This restriction lasts 30 days
    ✓ You may appeal this decision by contacting \n{Admins}\n

    We take these measures to maintain a safe, respectful environment for all members.

        """
    
        return {
            TDB_KEYS.PROTECTION_ENABLED   : True,
            TDB_KEYS.MUTE_DURATION        : 1,
            TDB_KEYS.WARNING_MESSAGE      : warning_message,
            TDB_KEYS.MUTE_COUNT           : 3,
            TDB_KEYS.REPEAT_ACTION        : 'ban',
            TDB_KEYS.ALLOW_BANNING        : True,
            TDB_KEYS.ADMIN_MESSAGE        : ban_message
        }

    def getGroupSetting(self, chat_id: int, settingRequired: str) -> any:
        """Get a specific setting value for a group"""
        with self.conn:
            try:
                # Get the settings JSON for this chat
                row = self.conn.execute(
                    "SELECT settings_json FROM group_settings WHERE chat_id = ?",
                    (chat_id,)
                ).fetchone()
                
                if not row:
                    return None
                    
                settings = json.loads(row[0])
                
                
                # Return the requested setting if it exists
                return settings.get(settingRequired)
                
            except sqlite3.Error as e:
                logging.error(f"Error getting setting {settingRequired} for chat {chat_id}: {str(e)}")
                return None
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON settings for chat {chat_id}")
                return None

    def save_hate_speech_settings(self, chat_id: str, uuid: str, settings: dict) -> bool:
        """Save settings with proper error handling"""
        with self.conn:
            try:
                # Verify ownership first
                owner = self.conn.execute(
                    "SELECT 1 FROM bot_installations WHERE chat_id = ? AND uuid = ?",
                    (str(chat_id), uuid)
                ).fetchone()
                if not owner:
                    return False

                # Get current settings if they exist
                current_settings = {}
                row = self.conn.execute(
                    "SELECT settings_json FROM group_settings WHERE chat_id = ?",
                    (str(chat_id),)
                ).fetchone()
                if row:
                    current_settings = json.loads(row[0])

                """
                # SPECIAL FIX: Ensure admin_message is properly saved
                if 'admin_message' in settings:
                    current_settings['admin_message'] = settings['admin_message']
                if 'warning_message' in settings:
                    current_settings['warning_message'] = settings['warning_message']
                """
                # Update other settings
                for key in [TDB_KEYS.PROTECTION_ENABLED, TDB_KEYS.MUTE_DURATION, TDB_KEYS.MUTE_COUNT, TDB_KEYS.WARNING_MESSAGE,
                            TDB_KEYS.REPEAT_ACTION, TDB_KEYS.ALLOW_BANNING, TDB_KEYS.ADMIN_MESSAGE]:
                    if key in settings:
                        current_settings[key] = settings[key]

                # Save the merged settings
                self.conn.execute(
                    """INSERT OR REPLACE INTO group_settings 
                    (chat_id, uuid, settings_json) 
                    VALUES (?, ?, ?)""",
                    (str(chat_id), uuid, json.dumps(current_settings))
                )
                return True
                
            except sqlite3.Error as e:
                logging.error(f"Database error: {str(e)}")
                return False
    def remove_group(self, chat_id: int) -> bool:
        """Remove group and its settings"""
        with self.conn:
            self.conn.execute("DELETE FROM bot_installations WHERE chat_id = ?", (chat_id,))
            return self.conn.total_changes > 0
    def get_user_groups(self, uuid: str) -> list[dict]:
        """Get all groups for a user with properly formatted dates"""
        with self.conn:
            rows = self.conn.execute("""
                SELECT 
                    i.chat_id, 
                    i.chat_title, 
                    i.chat_type,
                    i.adder_telegram_id,
                    i.installed_at,
                    COALESCE(m.count, 0) as member_count
                FROM bot_installations i
                LEFT JOIN group_members m ON i.chat_id = m.chat_id
                WHERE i.uuid = ?
                ORDER BY i.installed_at DESC
            """, (uuid,)).fetchall()
            
        return [{
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'adder_id': row[3],
            'added': row[4],  # Keep as string for now
            'members': row[5]
        } for row in rows]
        
    def add_group_member_count(self, chat_id: int, count: int) -> bool:
        """Update member count for a group"""
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO group_members (chat_id, count)
                VALUES (?, ?)
            """, (chat_id, count))
        return True
    def get_group_settings(self, chat_id: int, uuid: str) -> Optional[dict]:
        """Verify ownership before returning settings"""
        with self.conn:
            # First verify the requesting user owns this chat
            owner = self.conn.execute(
                "SELECT 1 FROM bot_installations WHERE chat_id = ? AND uuid = ?",
                (chat_id, uuid)
            ).fetchone()
            
            if not owner:
                return None
                
            # Then fetch settings
            row = self.conn.execute(
                "SELECT settings_json FROM group_settings WHERE chat_id = ?",
                (chat_id,)
            ).fetchone()
            
        return json.loads(row[0]) if row else {}
    
    def update_group_settings(self, chat_id: int, uuid: str, **settings) -> bool:
        """Securely update settings after ownership check"""
        with self.conn:
            # Verify ownership
            owner = self.conn.execute(
                "SELECT 1 FROM bot_installations WHERE chat_id = ? AND uuid = ?",
                (chat_id, uuid)
            ).fetchone()
            
            if not owner:
                return False
                
            # Merge new settings
            current_json = self.conn.execute(
                "SELECT settings_json FROM group_settings WHERE chat_id = ?",
                (chat_id,)
            ).fetchone()[0] or '{}'
            
            current = json.loads(current_json)
            current.update(settings)
            
            # Save updates
            self.conn.execute(
                "UPDATE group_settings SET settings_json = ? WHERE chat_id = ?",
                (json.dumps(current), chat_id)
            )
            return True
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
                (uuid, code)
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
    def get_uuid(self, telegram_id: str) -> Optional[str]:
        """Get UUID from corresponding telegram_id
        
        Args:
            telegram_id: The user's unique telegram id
            
        Returns:
            The UUID if found, None otherwise
        """
        with self.conn:
            row = self.conn.execute(
                "SELECT uuid FROM user_mapping WHERE telegram_id = ?",
                (telegram_id,)
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