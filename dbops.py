from sqlalchemy import create_engine, MetaData, text
from typing import List
from sqlalchemy.schema import CreateTable
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional
from pprint import pprint

def generate_schema_sql(database_url:str) -> List[str]:
    """Generates the SQL schema for a given database and returns it as a string.

    Args:
    database_url: The database connection URL
    """
    engine = create_engine(database_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    schema_statements = []

    for table_name, table in metadata.tables.items():
        # Add table creation SQL
        table_sql = str(CreateTable(table).compile(engine))
        schema_statements.append(f"-- Table: {table_name} --\n{table_sql}\n")

        # Add foreign key constraints
        for fk in table.foreign_keys:
            fk_sql = (
                f"ALTER TABLE {table_name} "
                f"ADD FOREIGN KEY ({fk.parent.name}) REFERENCES "
                f"{fk.target_fullname};"
            )
            schema_statements.append(
                f"-- Foreign Key: {fk.parent.name} -> {fk.target_fullname} --\n{fk_sql}\n"
            )

    return schema_statements

def simpleAskFunction(**kwargs):
    print(kwargs['query'])
    r = input('Do you want to Execute this Query? (y/n)')
    return ('y' in r.lower())

def queryRunner(database_url: str, sql_query: str, ask_function = simpleAskFunction) -> Dict[str, Optional[Any]]:
    """
    Execute a SQL query using SQLAlchemy.

    Args:
        database_url (str): The database connection URL.
        sql_query (str): The SQL query to execute.

    Returns:
        Dict[str, Optional[Any]]: A dictionary containing the data and any error message.
    """
    engine = create_engine(database_url)
    if not ask_function(query=sql_query):
        return {"data": []}
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            # Fetch all results if it's a SELECT query
            if sql_query.strip().lower().startswith('select'):
                data = [list(x) for x in result.fetchall()]
            else:
                data = None
        return {'data': data, 'error': None}
    except SQLAlchemyError as e:
        return {'data': None, 'error': str(e)}

# Example usage
"""
if __name__ == "__main__":
    DATABASE_URL = "sqlite:///sakila_master.db"  # Adjust for your database
    schema = generate_schema_sql(DATABASE_URL)

    # Print the schema (optional)
    print('\n'.join(schema))
"""
