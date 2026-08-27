"""SQLite setup and query helpers for the restaurant chatbot."""
import re
import sqlite3
from typing import Any, Dict, List, Tuple, cast


def initialize_database(db_path: str = "restaurant.sqlite") -> None:
    """Create tables and seed starter data if this is a new database."""
    # 'with sqlite3.connect(...)' opens a connection and auto-commits on success.
    # The database file is created automatically if it does not exist yet.
    with sqlite3.connect(db_path) as conn:

        # CREATE TABLE IF NOT EXISTS means this is safe to run multiple times —
        # it only creates the table the very first time.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menu_items (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name     TEXT NOT NULL,
                category      TEXT NOT NULL,
                description   TEXT NOT NULL,
                price         REAL NOT NULL,
                is_vegetarian INTEGER NOT NULL DEFAULT 0,
                is_spicy      INTEGER NOT NULL DEFAULT 0,
                is_available  INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurant_details (
                id      INTEGER PRIMARY KEY CHECK (id = 1),
                name    TEXT NOT NULL,
                address TEXT NOT NULL,
                phone   TEXT NOT NULL,
                email   TEXT NOT NULL,
                website TEXT NOT NULL
            )
            """
            # id = 1 with a CHECK constraint guarantees there is only ever one row.
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opening_hours (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week TEXT NOT NULL UNIQUE,
                open_time   TEXT NOT NULL,
                close_time  TEXT NOT NULL,
                notes       TEXT
            )
            """
        )

        # Seed the tables only when they are empty (first run).
        _seed_if_empty(conn)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                date          TEXT NOT NULL,
                time          TEXT NOT NULL,
                party_size    INTEGER NOT NULL,
                contact       TEXT,
                status        TEXT NOT NULL DEFAULT 'confirmed',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert a small demo dataset once, keeping reruns idempotent."""
    # fetchone()[0] returns the integer count — if > 0, the table already has rows.
    has_menu    = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] > 0
    has_details = conn.execute("SELECT COUNT(*) FROM restaurant_details").fetchone()[0] > 0
    has_hours   = conn.execute("SELECT COUNT(*) FROM opening_hours").fetchone()[0] > 0

    if not has_menu:
        # Each tuple maps to: (item_name, category, description, price,
        #                     is_vegetarian, is_spicy, is_available)
        menu_rows = [
            ("Margherita Pizza",   "Main",    "Tomato, mozzarella, basil",          10.50, 1, 0, 1),
            ("Spicy Chicken Burger","Main",    "Grilled chicken, jalapeno mayo",     11.90, 0, 1, 1),
            ("Caesar Salad",        "Starter", "Romaine, parmesan, croutons",        7.25,  0, 0, 1),
            ("Mushroom Risotto",    "Main",    "Creamy arborio rice with mushrooms", 12.75, 1, 0, 1),
            ("Lemon Tart",          "Dessert", "House-made tart with lemon curd",    5.20,  1, 0, 1),
            ("Iced Latte",          "Drinks", "Espresso with cold milk and ice",    4.60,  1, 0, 1),
        ]
        # executemany inserts all rows in a single transaction — much faster than
        # calling execute() six times separately.
        conn.executemany(
            """
            INSERT INTO menu_items
            (item_name, category, description, price, is_vegetarian, is_spicy, is_available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            menu_rows,
        )

    if not has_details:
        conn.execute(
            """INSERT INTO restaurant_details (id, name, address, phone, email, website)
               VALUES (1, ?, ?, ?, ?, ?)""",
            (
                "Sunset Bistro",
                "123 Market Street, Springfield",
                "+1-555-0142",
                "hello@sunsetbistro.example",
                "www.sunsetbistro.example",
            ),
        )

    if not has_hours:
        hours_rows = [
            ("Monday",    "09:00", "21:00", ""),
            ("Tuesday",   "09:00", "21:00", ""),
            ("Wednesday", "09:00", "21:00", ""),
            ("Thursday",  "09:00", "22:00", ""),
            ("Friday",    "09:00", "23:00", ""),
            ("Saturday",  "10:00", "23:00", "Brunch menu until 14:00"),
            ("Sunday",    "10:00", "20:00", "Family set menu available"),
        ]
        conn.executemany(
            """INSERT INTO opening_hours (day_of_week, open_time, close_time, notes)
               VALUES (?, ?, ?, ?)""",
            hours_rows,
        )


def get_menu_items(db_path: str) -> List[Dict[str, Any]]:
    """Return all menu items from the database."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT item_name, category, description, price,
                   is_vegetarian, is_spicy, is_available
            FROM menu_items
            ORDER BY category, item_name
            """
        ).fetchall()

    return [cast(Dict[str, Any], dict(row)) for row in rows]

def search_menu_items(db_path: str, query: str) -> List[Dict[str, Any]]:
    """Search menu items using text search and binary menu filters."""

    lower_q = query.lower()

    # ---------------------------------------------------------
    # Detect binary filters
    # ---------------------------------------------------------

    vegetarian_filter = None
    spicy_filter = None
    available_filter = None

    # Vegetarian
    if "non-vegetarian" in lower_q or "not vegetarian" in lower_q:
        vegetarian_filter = 0
    elif "vegetarian" in lower_q or "veggie" in lower_q:
        vegetarian_filter = 1

    # Spicy
    if "non-spicy" in lower_q or "not spicy" in lower_q:
        spicy_filter = 0
    elif "spicy" in lower_q:
        spicy_filter = 1

    # Availability
    if "unavailable" in lower_q or "not available" in lower_q:
        available_filter = 0
    elif "available" in lower_q:
        available_filter = 1

    # ---------------------------------------------------------
    # Remove filter words from text search
    # ---------------------------------------------------------

    search_query = lower_q

    filter_phrases = [
        "non-vegetarian",
        "not vegetarian",
        "vegetarian",
        "veggie",
        "non-spicy",
        "not spicy",
        "spicy",
        "unavailable",
        "not available",
        "available",
    ]

    for phrase in filter_phrases:
        search_query = search_query.replace(phrase, " ")

    # ---------------------------------------------------------
    # Ignore generic question words
    # ---------------------------------------------------------

    stop_words = {
        "what",
        "which",
        "where",
        "when",
        "who",
        "how",
        "many",
        "much",
        "are",
        "the",
        "you",
        "have",
        "has",
        "does",
        "do",
        "can",
        "could",
        "would",
        "your",
        "there",
        "any",
        "dishes",
        "dish",
        "options",
        "option",
        "food",
        "foods",
        "please",
        "show",
        "give",
        "me",
    }

    tokens = [
        re.sub(r"[^\w]", "", word.lower())
        for word in search_query.split()
    ]

    tokens = [
        word
        for word in tokens
        if len(word) >= 3
           and word not in stop_words
    ]

    # ---------------------------------------------------------
    # Build SQL conditions
    # ---------------------------------------------------------

    where_clauses = []
    params: List[Any] = []

    # Binary filters
    if vegetarian_filter is not None:
        where_clauses.append("is_vegetarian = ?")
        params.append(vegetarian_filter)

    if spicy_filter is not None:
        where_clauses.append("is_spicy = ?")
        params.append(spicy_filter)

    if available_filter is not None:
        where_clauses.append("is_available = ?")
        params.append(available_filter)

    # Text search
    if tokens:
        text_conditions = []

        for token in tokens[:6]:
            text_conditions.append(
                "(LOWER(item_name) LIKE ? "
                "OR LOWER(description) LIKE ? "
                "OR LOWER(category) LIKE ?)"
            )

            wildcard = f"%{token}%"

            params.extend([
                wildcard,
                wildcard,
                wildcard
            ])

        where_clauses.append(
            "(" + " OR ".join(text_conditions) + ")"
        )

    # ---------------------------------------------------------
    # No filters and no useful text
    # ---------------------------------------------------------

    if not where_clauses:
        return get_menu_items(db_path)

    # ---------------------------------------------------------
    # Execute SQL
    # ---------------------------------------------------------

    sql = """
        SELECT
            item_name,
            category,
            description,
            price,
            is_vegetarian,
            is_spicy,
            is_available
        FROM menu_items
        WHERE
    """ + " AND ".join(where_clauses) + """
        ORDER BY category, item_name
    """

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            sql,
            params
        ).fetchall()

    return [
        cast(Dict[str, Any], dict(row))
        for row in rows
    ]


def get_restaurant_details_and_hours(db_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Return the single restaurant details row and all opening-hours rows."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        details_row = conn.execute(
            "SELECT name, address, phone, email, website FROM restaurant_details WHERE id = 1"
        ).fetchone()
        hours_rows = conn.execute(
            "SELECT day_of_week, open_time, close_time, notes FROM opening_hours ORDER BY id"
        ).fetchall()

    details = cast(Dict[str, Any], dict(details_row)) if details_row else {}
    hours   = [cast(Dict[str, Any], dict(row)) for row in hours_rows]
    return details, hours

def book_reservation(
    db_path: str, customer_name: str, date: str,
    time: str, party_size: int, contact: str = None
) -> int:
    """Insert a new reservation and return its ID."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO reservations (customer_name, date, time, party_size, contact)"
            " VALUES (?, ?, ?, ?, ?)",
            (customer_name, date, time, party_size, contact)
        )
        return cursor.lastrowid


def cancel_reservation(db_path: str, reservation_id: int) -> None:
    """Mark a reservation as cancelled (soft delete)."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE reservations SET status = 'cancelled' WHERE id = ?",
            (reservation_id,)
        )


def get_reservations(db_path: str, customer_name: str = None) -> list:
    """Return confirmed reservations, optionally filtered by customer name."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if customer_name:
            rows = conn.execute(
                "SELECT * FROM reservations WHERE status='confirmed'"
                " AND customer_name LIKE ?", (f"%{customer_name}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM reservations WHERE status='confirmed'"
            ).fetchall()
        return [dict(r) for r in rows]

def get_reservation_email(db_path: str, reservation_id: int):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT contact
        FROM reservations
        WHERE id = ?
        """,
        (reservation_id,)
    ).fetchone()

    conn.close()

    if not row:
        return None

    return row["contact"]