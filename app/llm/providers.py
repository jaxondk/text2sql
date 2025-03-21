import os
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage

import instructor
from pydantic import BaseModel, Field
from openai import OpenAI

from app.core.models import TableSchema

logger = logging.getLogger(__name__)


class SQLOutput(BaseModel):
    """Structured output for SQL generation"""

    reasoning: str = Field(
        ..., description="Step-by-step reasoning about how to convert the query to SQL"
    )
    sql: str = Field(
        ...,
        description="The SQL query to execute (without any explanation or comments)",
    )


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

    def _extract_clean_sql(self, sql_text: str) -> str:
        """
        Extract clean SQL from text, removing comments and explanations
        """
        # Remove markdown code blocks if present
        if "```sql" in sql_text:
            # Extract content between ```sql and ```
            pattern = r"```sql\s*([\s\S]*?)\s*```"
            matches = re.findall(pattern, sql_text)
            if matches:
                sql_text = matches[0]
        elif "```" in sql_text:
            # Extract content between ``` and ```
            pattern = r"```\s*([\s\S]*?)\s*```"
            matches = re.findall(pattern, sql_text)
            if matches:
                sql_text = matches[0]

        # Split by lines and process
        lines = sql_text.splitlines()
        clean_lines = []
        for line in lines:
            # Skip comment lines
            if line.strip().startswith("--") or line.strip().startswith("#"):
                continue

            # Add non-empty lines
            if line.strip():
                clean_lines.append(line)

            # Stop at semicolon if it's at the end of a line
            if line.strip().endswith(";"):
                break

        # Join lines and clean up
        sql = "\n".join(clean_lines)

        # If there's still text after a semicolon, it's likely explanation
        if ";" in sql:
            sql = sql.split(";")[0] + ";"

        return sql


class OpenAIProvider(LLMProvider):
    """OpenAI provider using Instructor, with LangChain as a backup for parsing the response"""

    def __init__(self, model: str = "gpt-4o", **kwargs):
        self.model = model

        # Get API key from environment or kwargs
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided")

        # Initialize client with instructor
        self.openai_client = OpenAI(api_key=api_key)
        self.instructor_client = instructor.patch(self.openai_client)

        # Keep langchain client for older implementations
        self.langchain_client = ChatOpenAI(
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
        Generate SQL from natural language query using OpenAI with Instructor
        """
        # Format table schemas
        tables_str = self._format_tables(tables)

        # Create prompt
        if error:
            # Correction prompt with error information
            system_message = """You are an expert SQL writer who fixes incorrect SQL queries. 
You are given information about database tables, a natural language query, 
a previous SQL attempt, and an error message.
Your task is to generate a corrected SQL query that fixes the error.
Provide your reasoning step-by-step followed by the corrected SQL query.
The SQL query must not include any comments or explanation text - just the pure SQL.
"""
            user_message = f"""User query: {query}

Available tables:

{tables_str}

Previous SQL attempt:
```sql
{previous_sql}
```

Error message:
{error}

Please fix the SQL query to resolve the error."""

        else:
            # Normal conversion prompt
            system_message = """You are an expert SQL writer who converts natural language queries to SQL. 
You are given information about database tables and need to generate a working SQL query.
Provide your reasoning step-by-step followed by the SQL query.
The SQL query must not include any comments or explanation text - just the pure SQL."""

            user_message = f"""User query: {query}

Available tables:

{tables_str}

Based on the user query and available tables, generate a working SQL query.
Think carefully about the database schema and the relationships between tables."""

        # Generate SQL using instructor to ensure we get structured output
        try:
            response = self.instructor_client.chat.completions.create(
                model=self.model,
                response_model=SQLOutput,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
            )

            # Since we're using structured output, we can directly access the fields
            reasoning = response.reasoning
            sql = response.sql

            return reasoning, sql

        except Exception as e:
            # Fallback to langchain if instructor fails
            logger.warning(
                f"Error using instructor: {str(e)}. Falling back to LangChain."
            )

            # Create prompt for LangChain
            prompt = ChatPromptTemplate.from_messages(
                [("system", system_message), ("human", user_message)]
            )

            # Generate SQL using LangChain
            prompt_value = await prompt.ainvoke({})
            response = await self.langchain_client.ainvoke(prompt_value)

            # Parse response
            response_text = response.content

            # Extract reasoning and SQL
            reasoning = ""
            sql = ""

            if "Reasoning:" in response_text and "SQL:" in response_text:
                reasoning_part = response_text.split("SQL:")[0]
                reasoning = reasoning_part.replace("Reasoning:", "").strip()

                sql_part = response_text.split("SQL:")[1]
                sql = self._extract_clean_sql(sql_part.strip())
            else:
                # Fallback if format is different
                if "SELECT" in response_text.upper():
                    # Try to extract just the SQL query
                    sql_start_index = response_text.upper().find("SELECT")
                    potential_sql = response_text[sql_start_index:]
                    sql = self._extract_clean_sql(potential_sql)
                    reasoning = response_text[:sql_start_index].strip()
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
                    + (" (PK)" if col.is_primary_key else "")
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

        if error:
            # Correction prompt with error information
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert SQL writer who fixes incorrect SQL queries. 
You are given information about database tables, a natural language query, 
a previous SQL attempt, and an error message.
Your task is to generate a corrected SQL query that fixes the error.
Always respond with a detailed reasoning step-by-step followed by the corrected SQL query.
Format your response as follows:

Reasoning: <your reasoning here>

SQL: <your corrected SQL query here>

Always generate standard SQL that's compatible with most database engines.
The SQL query must contain ONLY the SQL code, with no explanatory text or comments.""",
                    ),
                    (
                        "human",
                        f"""User query: {query}

Available tables:

{tables_str}

Previous SQL attempt:
```sql
{previous_sql}
```

Error message:
{error}

Please fix the SQL query to resolve the error.""",
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

Always generate standard SQL that's compatible with most database engines.
The SQL query must contain ONLY the SQL code, with no explanatory text or comments.""",
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
            sql = self._extract_clean_sql(sql_part.strip())
        else:
            # Fallback if format is different
            if "SELECT" in response_text.upper():
                # Try to extract just the SQL query
                sql_start_index = response_text.upper().find("SELECT")
                potential_sql = response_text[sql_start_index:]
                sql = self._extract_clean_sql(potential_sql)
                reasoning = response_text[:sql_start_index].strip()
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
    """Local LLM provider (e.g., using LM Studio or Ollama)"""

    def __init__(self, model: str = "openhermes", **kwargs):
        self.model = model
        self.api_base = kwargs.get("api_base") or os.getenv(
            "LOCAL_LLM_API_BASE", "http://localhost:1234/v1"
        )
        self.api_key = kwargs.get("api_key") or "not-needed"

        from langchain_openai import ChatOpenAI

        # Initialize LangChain client with local settings
        self.client = ChatOpenAI(
            model=model,
            openai_api_key=self.api_key,
            openai_api_base=self.api_base,
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
        Generate SQL from natural language query using local model
        """
        # Format table schemas
        tables_str = self._format_tables(tables)

        if error:
            # Correction prompt with error information
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert SQL writer who fixes incorrect SQL queries. 
You are given information about database tables, a natural language query, 
a previous SQL attempt, and an error message.
Your task is to generate a corrected SQL query that fixes the error.
Always respond with a detailed reasoning step-by-step followed by the corrected SQL query.
Format your response as follows:

Reasoning: <your reasoning here>

SQL: <your corrected SQL query here>

Always generate standard SQL that's compatible with most database engines.
The SQL query must contain ONLY the SQL code, with no explanatory text or comments.""",
                    ),
                    (
                        "human",
                        f"""User query: {query}

Available tables:

{tables_str}

Previous SQL attempt:
```sql
{previous_sql}
```

Error message:
{error}

Please fix the SQL query to resolve the error.""",
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

Always generate standard SQL that's compatible with most database engines.
The SQL query must contain ONLY the SQL code, with no explanatory text or comments.""",
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
            sql = self._extract_clean_sql(sql_part.strip())
        else:
            # Fallback if format is different
            if "SELECT" in response_text.upper():
                # Try to extract just the SQL query
                sql_start_index = response_text.upper().find("SELECT")
                potential_sql = response_text[sql_start_index:]
                sql = self._extract_clean_sql(potential_sql)
                reasoning = response_text[:sql_start_index].strip()
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
