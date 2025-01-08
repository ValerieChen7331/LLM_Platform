from langchain_community.utilities import SQLDatabase

def db_connection(db_name,db_source):

    # sqlite
    # db = SQLDatabase.from_uri("sqlite:///Chinook.db")
    if db_source == "Oracle":
        username = 'U2NBC2S7'
        password = 'w2g7k335'
        host = '10.1.3.15'
        port = '1521'  # Default port for Oracle
        database = 'tprs05u'
        conn_str = f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}"
        db = SQLDatabase.from_uri(conn_str)
    elif db_source == "MSSQL":
        server = "10.3.96.168"
        database = db_name
        username = "NPC02"
        password = "0100NPC^&*("
        driver = '{/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.6.1}'
        conn_str = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        db = SQLDatabase.from_uri(conn_str)
    elif db_source == "SQLITE":
        db = SQLDatabase.from_uri(f"sqlite:///{db_name}.db")
        

    return db
