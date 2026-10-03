from sqlalchemy import create_engine, inspect

def extract_database_schema(db_url):
     engine = create_engine(db_url)
     inspector = inspect(engine)
     schema = {}

     for table_name in inspector.get_table_names():
          columns = inspector.get_columns(table_name)
          schema[table_name]=[]
          for column in columns:
             schema[table_name].append({
               "name": column["name"],
               "type": str(column["type"])
          })
     engine.dispose()          
     return schema


def format_schema(schema):
     formatted=[]

     for table,columns in schema.items():
          formatted.append(f"Table: {table}")
          for column in columns:
               formatted.append(f"  Column: {column['name']} - Type: {column['type']}")
     return "\n".join(formatted)