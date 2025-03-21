# Text2SQL

Text2SQL is an application that converts natural language queries into SQL, executes them against a database, and returns the results.

## TODO
- [ ] Improve Tracing
   - [ ] Expand the screen to take over and fill most of the screen
   - [ ] Tables tab should show the relevant tables, not all the tables
   - [ ] When reasoning is one line, it's really annoying. Maybe make a max width or something?
   - [ ] I'd really prefer a setup where it's more of an actual trace, where it shows the steps to get to the result in the order they happen. 
- [ ] Fix the settings page
   - [ ] Desired settings options
      - [ ] SQL DB settings
         - [ ] List of available databases, which db you're using and a way to add a database.
      - [ ] Vector DB Settings
         - [ ] List of available databases, which db you're using and a way to add a database. 
      - [ ] Model Settings
         - [ ] Available models and which model you're using. 
            - [ ] Later: add an endpoint. Perhaps good way to learn LiteLLM
         - [ ] max number of times the LLM retries
   - [ ] Persistent storage for settings
- [ ] Loading screen when first connect to get embedding model and other stuff loaded


## Features

- Natural language to SQL conversion using configurable LLM providers
- Semantic search for relevant table schemas
- Chat-style interface for query submission
- Tracing widget to view the reasoning, relevant schemas, generated SQL, and results
- Support for multiple database providers
- Docker deployment

## Setup

### Prerequisites

- Python 3.8+
- Docker (for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text2sql.git
cd text2sql
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

> **Note:** The `.env` file is excluded from version control in the `.gitignore` file to protect sensitive information like API keys. Always keep your API keys and database credentials private.

4. Create data directories:
```bash
mkdir -p data/config data/vectordb
```

> **Note:** The contents of `data/config/*.json` and `data/vectordb/` are excluded from version control. These will be generated automatically when you run the application.

### Setting Up a Development Database

For local development, you'll need a PostgreSQL database. There are two ways to set this up:

#### Using Docker (Recommended)

1. Start a PostgreSQL container:
```bash
docker run --name text2sql-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=postgres -p 5432:5432 -d postgres:14
```

2. Load sample data for testing:
```bash
# Create a sample_db.sql file with test data
docker exec -i text2sql-postgres psql -U postgres -d postgres < sample_db.sql
```

3. Verify the connection:
```bash
# Install required database drivers
pip install psycopg2-binary asyncpg

# Test the connection
python -c "from sqlalchemy import create_engine, text; engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres'); with engine.connect() as conn: print('Connection successful!')"
```

#### Using Local PostgreSQL Installation

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

4. Update your `.env` file with the connection string:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

### Testing Database Connectivity

The project includes two utility scripts to verify database connectivity:

1. **Quick check with default connection** (`db_quick_check.py`):
   - Tests a hardcoded PostgreSQL connection
   - Simple and direct, good for initial setup verification
   ```bash
   python db_quick_check.py
   ```

2. **Test configured database connection** (`db_config_test.py`):
   - Tests the database connection from your application's configuration
   - Supports both synchronous and asynchronous connection testing
   - Requires application to be configured first
   ```bash
   python db_config_test.py
   ```

### Running Locally

```bash
python -m app.main
```

### Docker Deployment

Build and run the Docker container:

```bash
docker build -t text2sql .
docker run -p 8000:8000 --env-file .env text2sql
```

## Usage

1. Navigate to http://localhost:8000 in your browser
2. Connect to your database in the settings
3. Start asking questions in natural language
4. View the generated SQL and results

## Project Structure

- `app/`: Main application code
  - `api/`: API endpoints
  - `core/`: Core business logic
  - `db/`: Database connection and models
  - `llm/`: LLM integration
  - `utils/`: Utility functions
  - `web/`: Web interface
- `tests/`: Test suite
- `data/`: 
  - `config/`: Database configuration files (not version controlled)
  - `vectordb/`: Vector database storage (not version controlled)
- `Dockerfile`: Docker configuration
- `requirements.txt`: Python dependencies
- `.gitignore`: Specifies intentionally untracked files to ignore
- `db_quick_check.py`: Simple database connectivity test script
- `db_config_test.py`: Tests database connection from application configuration