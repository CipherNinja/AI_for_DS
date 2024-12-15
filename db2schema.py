from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from pprint import pprint

def generate_schema_sql(database_url):
    """
    Generates the SQL schema for a given database and returns it as a string.

    :param database_url: The database connection URL.
    :return: A string containing the SQL schema for the database.
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

# Example usage
if __name__ == "__main__":
    DATABASE_URL = "sqlite:////home/arnv/Car_Database.db"  # Adjust for your database
    schema = generate_schema_sql(DATABASE_URL)

    # Print the schema (optional)
    print('\n'.join(schema))

