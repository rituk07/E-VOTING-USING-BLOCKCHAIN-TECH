import sqlite3
import os

DB_NAME = "evoting.db"

def reset_database():
    try:
        # Try to remove file first for a truly clean slate
        if os.path.exists(DB_NAME):
            try:
                os.remove(DB_NAME)
                print("--- Old database file removed.")
            except PermissionError:
                print("--- Database file locked. Falling back to clearing tables...")

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        print("--- Resetting tables...")
        cur.execute("DROP TABLE IF EXISTS users")
        cur.execute("DROP TABLE IF EXISTS blockchain")
        
        # Voters Table
        cur.execute("""
        CREATE TABLE users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            voter_id TEXT UNIQUE,
            password TEXT,
            face_path TEXT,
            voted INTEGER DEFAULT 0
        )
        """)

        # Blockchain Table
        cur.execute("""
        CREATE TABLE blockchain(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_data TEXT,
            block_hash TEXT,
            prev_hash TEXT
        )
        """)

        conn.commit()
        conn.close()
        print("--- Database tables recreated.")

        # Clear stored faces
        face_dir = "static/faces"
        if os.path.exists(face_dir):
            import shutil
            for f in os.listdir(face_dir):
                file_path = os.path.join(face_dir, f)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except: pass
            print("--- Stored face profiles cleared.")

        print("SUCCESS: Full system reset complete!")
    except Exception as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    reset_database()
