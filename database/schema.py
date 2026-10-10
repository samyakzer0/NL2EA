import warnings
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SAWarning

warnings.filterwarnings(
    "ignore",
    message="Did not recognize type 'vector' of column 'embedding'",
    category=SAWarning
)


def extract_database_schema(
    db_url,
    allowed_tables=None,
    schema_name="public"
):
    engine = create_engine(db_url)
    inspector = inspect(engine)

    schema = {}

    for table_name in inspector.get_table_names(schema=schema_name):

        if allowed_tables and table_name not in allowed_tables:
            continue

        columns = inspector.get_columns(
            table_name,
            schema=schema_name
        )

        full_table_name = f"{schema_name}.{table_name}"

        schema[full_table_name] = []

        for column in columns:

            # Do not expose vector embeddings to the SQL agent
            if column["name"] == "embedding":
                continue

            schema[full_table_name].append({
                "name": column["name"],
                "type": str(column["type"])
            })

    engine.dispose()

    return schema


def format_schema(schema):

    formatted = []

    for table, columns in schema.items():

        formatted.append(f"Table: {table}")

        for column in columns:

            formatted.append(
                f"  Column: {column['name']} - Type: {column['type']}"
            )

    return "\n".join(formatted)