import os
import sys
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_connection():
    print("Starting test...")

    # Import from our app
    from app.db.adapters import PostgresAdapter

    try:
        print("Creating adapter...")
        adapter = PostgresAdapter(
            "postgresql://postgres:postgres@localhost:5432/postgres"
        )

        print("Testing connection...")
        try:
            await adapter.test_connection()
            print("Connection successful")
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return

        print("Getting schemas...")
        try:
            tables = await adapter.get_table_schemas()
            print(f"Found {len(tables)} tables:")
            for t in tables:
                print(f"- {t.name} ({len(t.columns)} columns)")
        except Exception as e:
            print(f"Schema error: {str(e)}")
            return

        # Try to store in vector DB
        print("Testing vector store...")
        from app.utils.vector_store import get_vector_store

        vector_store = get_vector_store()
        print("Vector store created")

        try:
            await vector_store.index_tables("test-db", tables)
            print("Tables indexed successfully")
        except Exception as e:
            print(f"Vector store error: {str(e)}")

    except Exception as e:
        print(f"Global error: {str(e)}")

    print("Test completed")


if __name__ == "__main__":
    asyncio.run(test_connection())
