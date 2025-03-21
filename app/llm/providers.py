import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage

from app.core.models import TableSchema

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Base LLM provider class"""

    @abstractmethod
    async def generate_sql(
        self,
        query: str,
        tables: List[TableSchema],
        error: Optional[str] = None,
        previous_sql: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate SQL from natural language query
        Returns a tuple of (reasoning, sql)
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider using LangChain"""

    def __init__(self, model: str = "gpt-4o", **kwargs):
        self.model = model

        # Get API key from environment or kwargs
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided")

        # Initialize LangChain client
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=0,
        )

    async def generate_sql(
        self,
        query: str,
        tables: List[TableSchema],
        error: Optional[str] = None,
        previous_sql: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate SQL from natural language query using OpenAI
        """
        # Format table schemas
        tables_str = self._format_tables(tables)

        # Create prompt
        if error and previous_sql:
            # Error correction prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert SQL writer who converts natural language queries to SQL. 
You are given information about database tables and need to generate a working SQL query.
Always respond with a detailed reasoning step-by-step followed by the SQL query.
Format your response as follows:

Reasoning: <your reasoning here>

SQL: <your SQL query here>

Always generate standard SQL that's compatible with most database engines.""",
                    ),
                    (
                        "human",
                        f"""User query: {query}

Available tables:

{tables_str}

I tried the following SQL query but got an error:

```sql
{previous_sql}
```

Error: {error}

Please correct the SQL query to fix this error. Think carefully about the database schema and generate a working SQL query.""",
                    ),
                ]
            )
        else:
            # Normal conversion prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert SQL writer who converts natural language queries to SQL. 
You are given information about database tables and need to generate a working SQL query.
Always respond with a detailed reasoning step-by-step followed by the SQL query.
Format your response as follows:

Reasoning: <your reasoning here>

SQL: <your SQL query here>

Always generate standard SQL that's compatible with most database engines.""",
                    ),
                    (
                        "human",
                        f"""User query: {query}

Available tables:

{tables_str}

Based on the user query and available tables, generate a working SQL query.
Think carefully about the database schema and the relationships between tables.""",
                    ),
                ]
            )

        # Generate SQL
        # Convert the ChatPromptTemplate to a PromptValue
        prompt_value = await prompt.ainvoke({})
        response = await self.client.ainvoke(prompt_value)

        # Parse response
        response_text = response.content

        # Extract reasoning and SQL
        reasoning = ""
        sql = ""

        if "Reasoning:" in response_text and "SQL:" in response_text:
            reasoning_part = response_text.split("SQL:")[0]
            reasoning = reasoning_part.replace("Reasoning:", "").strip()

            sql_part = response_text.split("SQL:")[1]
            sql = sql_part.strip()

            # Clean up SQL (remove markdown code blocks if present)
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            elif sql.startswith("```"):
                sql = sql.replace("```", "").strip()
        else:
            # Fallback if format is different
            if "SELECT" in response_text.upper():
                # Try to extract just the SQL query
                lines = response_text.splitlines()
                sql_lines = []
                capture = False

                for line in lines:
                    if line.strip().upper().startswith("SELECT") or capture:
                        capture = True
                        sql_lines.append(line)

                sql = "\n".join(sql_lines)
                reasoning = response_text.replace(sql, "").strip()
            else:
                # If all else fails, use the whole response as reasoning
                reasoning = response_text
                sql = ""

        return reasoning, sql

    def _format_tables(self, tables: List[TableSchema]) -> str:
        """Format tables for prompt"""
        result = []

        for table in tables:
            columns_str = "\n".join(
                [
                    f"- {col.name}: {col.data_type}"
                    + (f" (PK)" if col.is_primary_key else "")
                    + (f" (FK to {col.references})" if col.is_foreign_key else "")
                    for col in table.columns
                ]
            )

            result.append(f"Table: {table.name}\nColumns:\n{columns_str}\n")

        return "\n".join(result)


class AnthropicProvider(LLMProvider):
    """Anthropic provider using LangChain"""

    def __init__(self, model: str = "claude-3-opus-20240229", **kwargs):
        self.model = model

        # Get API key from environment or kwargs
        api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not provided")

        # Initialize LangChain client
        self.client = ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=0,
        )

    async def generate_sql(
        self,
        query: str,
        tables: List[TableSchema],
        error: Optional[str] = None,
        previous_sql: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate SQL from natural language query using Anthropic
        """
        # Format table schemas
        tables_str = self._format_tables(tables)

        # Create prompt
        if error and previous_sql:
            # Error correction prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert SQL writer who converts natural language queries to SQL. 
You are given information about database tables and need to generate a working SQL query.
Always respond with a detailed reasoning step-by-step followed by the SQL query.
Format your response as follows:

Reasoning: <your reasoning here>

SQL: <your SQL query here>

Always generate standard SQL that's compatible with most database engines.""",
                    ),
                    (
                        "human",
                        f"""User query: {query}

Available tables:

{tables_str}

I tried the following SQL query but got an error:

```sql
{previous_sql}
```

Error: {error}

Please correct the SQL query to fix this error. Think carefully about the database schema and generate a working SQL query.""",
                    ),
                ]
            )
        else:
            # Normal conversion prompt
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert SQL writer who converts natural language queries to SQL. 
You are given information about database tables and need to generate a working SQL query.
Always respond with a detailed reasoning step-by-step followed by the SQL query.
Format your response as follows:

Reasoning: <your reasoning here>

SQL: <your SQL query here>

Always generate standard SQL that's compatible with most database engines.""",
                    ),
                    (
                        "human",
                        f"""User query: {query}

Available tables:

{tables_str}

Based on the user query and available tables, generate a working SQL query.
Think carefully about the database schema and the relationships between tables.""",
                    ),
                ]
            )

        # Generate SQL
        # Convert the ChatPromptTemplate to a PromptValue
        prompt_value = await prompt.ainvoke({})
        response = await self.client.ainvoke(prompt_value)

        # Parse response
        response_text = response.content

        # Extract reasoning and SQL
        reasoning = ""
        sql = ""

        if "Reasoning:" in response_text and "SQL:" in response_text:
            reasoning_part = response_text.split("SQL:")[0]
            reasoning = reasoning_part.replace("Reasoning:", "").strip()

            sql_part = response_text.split("SQL:")[1]
            sql = sql_part.strip()

            # Clean up SQL (remove markdown code blocks if present)
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            elif sql.startswith("```"):
                sql = sql.replace("```", "").strip()
        else:
            # Fallback if format is different
            if "SELECT" in response_text.upper():
                # Try to extract just the SQL query
                lines = response_text.splitlines()
                sql_lines = []
                capture = False

                for line in lines:
                    if line.strip().upper().startswith("SELECT") or capture:
                        capture = True
                        sql_lines.append(line)

                sql = "\n".join(sql_lines)
                reasoning = response_text.replace(sql, "").strip()
            else:
                # If all else fails, use the whole response as reasoning
                reasoning = response_text
                sql = ""

        return reasoning, sql

    def _format_tables(self, tables: List[TableSchema]) -> str:
        """Format tables for prompt"""
        result = []

        for table in tables:
            columns_str = "\n".join(
                [
                    f"- {col.name}: {col.data_type}"
                    + (f" (PK)" if col.is_primary_key else "")
                    + (f" (FK to {col.references})" if col.is_foreign_key else "")
                    for col in table.columns
                ]
            )

            result.append(f"Table: {table.name}\nColumns:\n{columns_str}\n")

        return "\n".join(result)


class LocalProvider(LLMProvider):
    """
    Local provider for development/testing
    Always returns a simple SQL query without actually using an LLM
    """

    def __init__(self, model: str = "mock", **kwargs):
        self.model = model

    async def generate_sql(
        self,
        query: str,
        tables: List[TableSchema],
        error: Optional[str] = None,
        previous_sql: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate a mock SQL query for testing
        """
        # If we have tables, use the first one for a simple query
        if tables:
            table = tables[0]
            columns = [col.name for col in table.columns]

            # Build a simple SELECT query
            sql = f"SELECT {', '.join(columns[:3])} FROM {table.name} LIMIT 10"
            reasoning = f"This is a mock query using the {table.name} table for testing purposes."
        else:
            # Default mock query
            sql = "SELECT 1 AS test"
            reasoning = (
                "This is a mock query for testing purposes with no tables available."
            )

        return reasoning, sql


def get_llm_provider(provider: str, model: str, **kwargs) -> LLMProvider:
    """
    Get LLM provider based on provider name
    """
    if provider.lower() == "openai":
        return OpenAIProvider(model=model, **kwargs)
    elif provider.lower() == "anthropic":
        return AnthropicProvider(model=model, **kwargs)
    elif provider.lower() == "local":
        return LocalProvider(model=model, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
