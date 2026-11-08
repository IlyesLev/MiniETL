import os
import pyodbc


def get_connection():
    trusted = os.getenv(
        "SQLSERVER_TRUSTED_CONNECTION", "true"
    ).lower() == "true"

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={os.environ['SQLSERVER_HOST']};"
        f"DATABASE={os.environ['SQLSERVER_DATABASE']};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    if trusted:
        connection_string += "Trusted_Connection=yes;"
    else:
        connection_string += (
            f"UID={os.environ['SQLSERVER_USERNAME']};"
            f"PWD={os.environ['SQLSERVER_PASSWORD']};"
        )

    return pyodbc.connect(connection_string)
