import sqlite3
from datetime import datetime, timezone

DB_NAME = "bot_database.db"


def get_connection():
    """Returns a connection to the local SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Enables dict-like row access
    return conn


def init_db():
    """Initializes the database schema if tables do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Table for storing global blacklists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS global_blacklist (
                user_id INTEGER PRIMARY KEY,
                reason TEXT NOT NULL,
                added_at TEXT NOT NULL,
                added_by INTEGER
            )
        """
        )

        # Table for guild whitelists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_whitelist (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """
        )

        # Table for storing guild logging settings
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                log_channel_id INTEGER
            )
        """
        )

        conn.commit()


# Initialize database tables on module load
init_db()


# --- Global Blacklist Functions ---


def is_globally_blacklisted(user_id: int) -> bool:
    """Check if a user is in the global blacklist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM global_blacklist WHERE user_id = ?", (user_id,)
        )
        return cursor.fetchone() is not None


def get_blacklist_reason(user_id: int) -> str:
    """Retrieve the reason why a user was blacklisted."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT reason FROM global_blacklist WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        return row["reason"] if row else "No reason provided"


def add_to_global_blacklist(
    user_id: int, reason: str, admin_id: int = None
) -> bool:
    """Add a user to the global blacklist."""
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO global_blacklist (user_id, reason, added_at, added_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    reason = excluded.reason,
                    added_at = excluded.added_at,
                    added_by = excluded.added_by
            """,
                (user_id, reason, now_iso, admin_id),
            )
            conn.commit()
            return True
    except sqlite3.Error:
        return False


def remove_from_global_blacklist(user_id: int) -> bool:
    """Remove a user from the global blacklist."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM global_blacklist WHERE user_id = ?", (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error:
        return False


def get_all_blacklisted_users() -> list[dict]:
    """Fetch all globally blacklisted users ordered by newest first."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, reason, added_at FROM global_blacklist ORDER BY added_at DESC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# --- Whitelist Functions ---


def is_whitelisted(guild_id: int, user_id: int) -> bool:
    """Check if a user is whitelisted in a specific guild."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM guild_whitelist WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        return cursor.fetchone() is not None


def add_to_whitelist(guild_id: int, user_id: int) -> bool:
    """Add a user to a guild's whitelist."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO guild_whitelist (guild_id, user_id) VALUES (?, ?)",
                (guild_id, user_id),
            )
            conn.commit()
            return True
    except sqlite3.Error:
        return False


def remove_from_whitelist(guild_id: int, user_id: int) -> bool:
    """Remove a user from a guild's whitelist."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM guild_whitelist WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error:
        return False


# --- Guild Log Channel Functions ---


def set_log_channel(guild_id: int, channel_id: int) -> bool:
    """Set or update the log channel for auto-kicks in a guild."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, log_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET log_channel_id = excluded.log_channel_id
            """,
                (guild_id, channel_id),
            )
            conn.commit()
            return True
    except sqlite3.Error:
        return False


def get_log_channel(guild_id: int) -> int | None:
    """Retrieve the log channel ID for a guild."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT log_channel_id FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        )
        row = cursor.fetchone()
        return row["log_channel_id"] if row else None