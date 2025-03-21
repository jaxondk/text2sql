# Text2SQL Database Setup Guide

This guide will help you set up and configure databases for the Text2SQL application, both for development and production environments.

## Automatic Database Connection

Text2SQL now automatically connects to your local PostgreSQL database on startup if no databases are configured. The default connection uses:

- Host: localhost
- Port: 5432
- User: postgres
- Password: postgres
- Database: postgres

This connection is pulled from the `DATABASE_URL` environment variable in your `.env` file. If you need to customize this default connection, simply update this variable:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

## Development Setup

### Option 1: Using Docker (Recommended)

Docker provides a simple way to run a PostgreSQL instance without installing it locally.

1. Start a PostgreSQL container:
```bash
docker run --name text2sql-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=postgres -p 5432:5432 -d postgres:14
```

2. To create the sample database for testing, save the sample schema to a file named `sample_db.sql` and run:
```bash
docker exec -i text2sql-postgres psql -U postgres -d postgres < sample_db.sql
```

3. To restart the container after rebooting:
```bash
docker start text2sql-postgres
```

4. To stop the container:
```bash
docker stop text2sql-postgres
```

### Option 2: Local PostgreSQL Installation

1. Install PostgreSQL:
   - macOS: `brew install postgresql@14`
   - Linux: `sudo apt install postgresql-14`
   - Windows: Download installer from postgresql.org

2. Start the PostgreSQL service:
   - macOS: `brew services start postgresql@14`
   - Linux: `sudo systemctl start postgresql`
   - Windows: Service is started automatically

3. Create a database and load sample data:
```bash
psql -U postgres -c "CREATE DATABASE text2sql_dev;"
psql -U postgres -d text2sql_dev -f sample_db.sql
```

## Required Python Packages

Ensure these are installed:
```bash
pip install psycopg2-binary asyncpg sqlalchemy greenlet
```

The `greenlet` package is required for SQLAlchemy's async support with PostgreSQL. If you encounter an error like `the greenlet library is required to use this function`, run:
```bash
pip install greenlet
```

## Connection Configuration

Update the `.env` file with the appropriate connection string:

```
# For local Docker installation
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres

# For custom database
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

## Manual Database Configuration

If you need to configure multiple databases or want to manually add a connection:

1. Start the application:
```bash 
python -m app.main
```

2. Navigate to http://localhost:8000 in your browser

3. Go to the Settings page and add your database connection:
   - Name: Local Development DB
   - Type: PostgreSQL
   - Connection string: postgresql://postgres:postgres@localhost:5432/postgres
   - Description: Local development database

## Testing the Connection

Run this test script to verify your database connection:

```python
from sqlalchemy import create_engine, text

def test_connection():
    conn_str = "postgresql://postgres:postgres@localhost:5432/postgres"
    engine = create_engine(conn_str)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            
            # Test a specific table
            result = conn.execute(text("SELECT * FROM users LIMIT 3"))
            for row in result:
                print(row)
                
        return True
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
```

## Troubleshooting

### Connection Refused
- Check if PostgreSQL is running: `docker ps` (for Docker) or `pg_isready` (for local install)
- Verify the port is correct (default is 5432)
- Ensure no firewall is blocking the connection

### Authentication Failed
- Verify username and password in the connection string
- Check PostgreSQL authentication settings in `pg_hba.conf`

### Missing Database Drivers
If you get errors about missing drivers:
```bash
pip install psycopg2-binary asyncpg greenlet
```

### Missing Greenlet Library
If you see an error about the greenlet library:
```
ERROR: the greenlet library is required to use this function. No module named 'greenlet'
```
Install it with:
```bash
pip install greenlet
```

### MacOS Issues
On macOS, if you get a `pg_config executable not found` error:
```bash
brew install postgresql@14
export PATH=$PATH:/opt/homebrew/opt/postgresql@14/bin
pip install psycopg2-binary
```

### Resetting the Database Configuration
If you need to reset the database configuration and force the app to create a new default connection:
```bash
rm -f data/config/databases.json
```

## Sample Database Schema

Here's a sample database schema for testing:

```sql
-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    inventory INTEGER DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL
);

-- Order items table
CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
```

## Using the Application with the Database

1. Start the application:
```bash 
python -m app.main
```

2. Navigate to http://localhost:8000 in your browser

3. Start asking questions about your database tables 