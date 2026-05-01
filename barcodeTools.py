from multiprocessing import process
import os

from flask.cli import load_dotenv
import requests
import sqlite3
from pathlib import Path

load_dotenv()
API_KEY = os.getenv("API_KEY")


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

def clear_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Database cleared.")
    else:
        print("No database found to clear.")

def input_game(name: str, barcode: str, system: str, used: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO SystemList (system_name) VALUES (?)",
        (system,)
    )

    c.execute("""
        INSERT INTO GameLibrary (name, barcode, system, used)
        VALUES (?, ?, ?, ?)
    """, (name, barcode, system, used))
    conn.commit()

def update_quantity(barcode: str, used: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE GameLibrary
        SET quantity = quantity + 1
        WHERE barcode = ? AND used = ?
    """, (barcode, used))
    conn.commit()
    conn.close()

def process_barcode(barcode: str, system: str = "", quality: str = "") -> tuple[str, str, str]:
    conn = get_connection()
    c = conn.cursor()

    while not quality:
        quality = input("Is this game Used or Sealed?\n").strip().lower()
        if quality not in ["used", "sealed"]:
            print("Invalid input. Please enter 'Used' or 'Sealed'.")
            quality = ""

    if quality == "used":
        used = 1
    else:
        used = 0

    c.execute("""
        SELECT name, system, quantity
        FROM GameLibrary
        WHERE barcode = ? AND used = ?
    """, (barcode, used))
    result = c.fetchone()

    if not result:
        while True:
            name = input("Game not found. Please enter the game name: \n").strip()
            if name:
                break
            print("Game name cannot be empty.")

        while not system:
            system = input("Please enter the game system: \n").strip().lower()
            if system:
                break
            print("Game system cannot be empty.")

        input_game(name, barcode, system, used)
    else:
        name, system, _ = result
        update_quantity(barcode, used)
        
    conn.close()
    return name, system, quality


def input_mode(system = "", quality = ""):
    while True:
        barcode = input("Scan a barcode and press Enter, or press Enter to quit: \n").strip()
        if not barcode:
            print("Exiting input mode.")
            break

        name, system, quality = process_barcode(barcode, system, quality)
        print(f"Processed: '{name}' for {system}. Condition: {quality}")

def input_GoUPC():
    while True:
        barcode = input("Please enter the GoUPC code and press Enter, or press Enter to quit: \n").strip()
        if not barcode:
            print("Exiting input mode.")
            break

        response = requests.get(f"https://go-upc.com/api/v1/code/{barcode}?key={API_KEY}")  # Placeholder response

        name = response.json().get("name", "Unknown")
        system = response.json().get("system", "Unknown")
        # TODO: Check response, see if json.get("system") is correct

        while not quality:
            quality = input("Is this game Used or Sealed?").strip().lower()
            if quality not in ["used", "sealed"]:
                print("Invalid input. Please enter 'Used' or 'Sealed'.")
                quality = ""

        print(f"Processed: '{name}' for {system}. Condition: {quality}")

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
            print(f"{name:<30} {system:<20} {condition:<10} {quantity:<8}")

    conn.close()

def main():
    init_db()
    while True:
        print("\nMenu:")
        print("1. Input mode (scan barcodes)")
        print("2. Input in group (same system, quality, etc.)")
        print("3. Output list of games")
        print("4. Remove games from library (not implemented yet)")
        print("5. Clear database")
        print("6. Exit")
        print("\n")
        choice = input("Select an option: ").strip()

        if choice == "1":
            input_mode()

        elif choice == "2":
            system = input("Please state the system you are inputting, or leave blank for different systems.\n").strip().lower()
            while True:
                quality = input("Please state the quality you are inputting, or leave blank for different quality. Used or Sealed only.\n").strip().lower()
                if quality in ["used", "sealed", ""]:
                    break
                print("Invalid option, please try again.\n\n")
            input_mode(system, quality)       

        elif choice == "3":
            output_list()

        elif choice == "4":
            print("This option is not implemented yet.")
            
        elif choice == "5":
            if input("Are you sure you want to clear the database? This action cannot be undone. (yes/no)\n").strip().lower() == "yes":
                clear_db()
            else:
                print("Database clear cancelled.")

        elif choice == "6":
            print("Exiting program.")
            break
        else:
            print("Invalid option. Please select option 1 through 6.\n")

if __name__ == "__main__":
    main()