from sqlalchemy import create_engine, text


def test_connection():
    conn_str = "postgresql://postgres:postgres@localhost:5432/postgres"
    engine = create_engine(conn_str)

    try:
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")

            # Test users table
            result = conn.execute(text("SELECT * FROM users LIMIT 3"))
            print("Users data:")
            for row in result:
                print(row)

            # Test products table
            result = conn.execute(text("SELECT * FROM products LIMIT 3"))
            print("\nProducts data:")
            for row in result:
                print(row)

        return True
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False


if __name__ == "__main__":
    test_connection()
