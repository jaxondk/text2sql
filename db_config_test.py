import json
import os
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine


async def test_connection_async():
    """Test async database connection using the same connection string from databases.json"""
    try:
        # Read the connection string from the config file
        with open("data/config/databases.json", "r") as f:
            configs = json.load(f)

        if not configs:
            print("No database configurations found!")
            return False

        connection_string = configs[0]["connection_string"]
        db_id = configs[0]["id"]

        print(f"Found database ID: {db_id}")
        print(f"Using connection string: {connection_string}")

        # Convert to async version if needed
        if not connection_string.startswith("postgresql+asyncpg://"):
            if connection_string.startswith("postgresql://"):
                async_connection_string = connection_string.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )
            else:
                async_connection_string = f"postgresql+asyncpg://{connection_string}"
        else:
            async_connection_string = connection_string

        print(f"Using async connection string: {async_connection_string}")

        # Test async connection
        engine = create_async_engine(async_connection_string)

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Async database connection successful!")

            # Test users table
            result = await conn.execute(text("SELECT * FROM users LIMIT 3"))
            print("Users data:")
            rows = result.fetchall()
            for row in rows:
                print(row)

            # Close the connection explicitly
            await conn.close()

        return True
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False


def test_connection_sync():
    """Test sync database connection using the same connection string from databases.json"""
    try:
        # Read the connection string from the config file
        with open("data/config/databases.json", "r") as f:
            configs = json.load(f)

        if not configs:
            print("No database configurations found!")
            return False

        connection_string = configs[0]["connection_string"]

        # Use standard connection string
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Sync database connection successful!")

            # Test users table
            result = conn.execute(text("SELECT * FROM users LIMIT 3"))
            print("Users data:")
            for row in result:
                print(row)

        return True
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False


async def main():
    print("Testing async connection...")
    await test_connection_async()

    print("\nTesting sync connection...")
    test_connection_sync()


if __name__ == "__main__":
    asyncio.run(main())
