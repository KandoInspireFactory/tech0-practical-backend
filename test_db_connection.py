import os
from sqlalchemy import text
from db_control.connect_MySQL import engine

def test_connection():
    print("Attempting to connect to the database...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connection successful!")
            for row in result:
                print(f"Test query result: {row}")
        print("Connection closed.")
    except Exception as e:
        print(f"Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
