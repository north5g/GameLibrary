import sqlite3
from pathlib import Path

DB_PATH = Path("GameLibrary.sqlite")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(database: str = "GameLibrary.sqlite"):
    global DB_PATH
    DB_PATH = Path(database)

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS SystemList (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_name TEXT NOT NULL UNIQUE
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS GameLibrary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT NOT NULL,
            system TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0 CHECK (used IN (0, 1)),
            quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
            FOREIGN KEY (system) REFERENCES SystemList(system_name)
                ON DELETE CASCADE,
            UNIQUE (barcode, used)
        );
    """)

    c.executescript("""
        CREATE INDEX IF NOT EXISTS idx_barcode
            ON GameLibrary(barcode);

        CREATE INDEX IF NOT EXISTS idx_system
            ON GameLibrary(system);

        CREATE INDEX IF NOT EXISTS idx_barcode_used
            ON GameLibrary(barcode, used);
    """)

    conn.commit()
    conn.close()


def ask_used_status(name: str = "this game", system: str = "") -> tuple[str, int]:
    while True:
        used = input(f"Is '{name}' for {system} used? (y/n): ").strip().lower()
        if used in ("y", "n"):
            return used, 1 if used == "y" else 0
        print("Invalid input. Please enter 'y' for yes or 'n' for no.")


def process_barcode(barcode: str) -> tuple[str, str, str]:
    conn = get_connection()
    c = conn.cursor()

    used, used_value = ask_used_status("this game", "unknown system")

    c.execute("""
        SELECT name, system, quantity
        FROM GameLibrary
        WHERE barcode = ? AND used = ?
    """, (barcode, used_value))
    result = c.fetchone()

    if result:
        name, system, _ = result
        c.execute("""
            UPDATE GameLibrary
            SET quantity = quantity + 1
            WHERE barcode = ? AND used = ?
        """, (barcode, used_value))
        conn.commit()
    else:
        while True:
            name = input("Game not found. Please enter the game name: ").strip()
            if name:
                break
            print("Game name cannot be empty.")

        while True:
            system = input("Please enter the game system: ").strip()
            if system:
                break
            print("Game system cannot be empty.")

        c.execute(
            "INSERT OR IGNORE INTO SystemList (system_name) VALUES (?)",
            (system,)
        )

        c.execute("""
            INSERT INTO GameLibrary (name, barcode, system, used)
            VALUES (?, ?, ?, ?)
        """, (name, barcode, system, used_value))
        conn.commit()

    conn.close()
    return name, system, used


def input_mode():
    while True:
        barcode = input("Scan a barcode and press Enter, or press Enter to quit: ").strip()
        if not barcode:
            print("Exiting input mode.")
            break

        if not barcode.isdigit():
            print("Invalid input. Please scan a numeric barcode.")
            continue

        name, system, used = process_barcode(barcode)
        condition = "Used" if used == "y" else "New"
        print(f"Processed: '{name}' for {system}. Condition: {condition}")

def output_list():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT name, system, used, quantity
        FROM GameLibrary
        ORDER BY system, name
    """)
    games = c.fetchall()

    if not games:
        print("No games in library.")
    else:
        print("\nGame Library:\n")
        print(f"{'Name':<30} {'System':<20} {'Condition':<10} {'Quantity':<8}")
        for name, system, used, quantity in games:
            condition = "Used" if used == 1 else "Sealed"
            print(f"{name} ({system}) - {condition} - Quantity: {quantity}")

    conn.close()

def main():
    init_db()
    while True:
        print("\nMenu:")
        print("1. Input mode (scan barcodes)")
        print("2. Output list of games")
        print("3. Remove games from library (not implemented yet)")
        print("4. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            input_mode()
        elif choice == "2":
            output_list()
        elif choice == "3":
            print("This option is not implemented yet.")
        elif choice == "4":
            print("Exiting program.")
            break
        else:
            print("Invalid option. Please select 1, 2, or 3.")