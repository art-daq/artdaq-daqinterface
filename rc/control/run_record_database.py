
"""
Database helper functions for saving run records to PostgreSQL.

"""

import os


def get_db_connection(self):
    """
    Get or create database connection. Returns None if database saving is disabled.
    
    Connection is stored in self._run_record_db_conn for reuse.
    Database settings are read from instance variables by read_settings().
    
    Returns:
        psycopg2.connection or None: Database connection if enabled and successful, None otherwise
    """
    # Check if database saving is enabled (from settings file)
    if not hasattr(self, 'enable_run_record_database') or not self.enable_run_record_database:
        return None
    
    # Return existing connection if available (stored in instance)
    if hasattr(self, '_run_record_db_conn') and self._run_record_db_conn is not None:
        return self._run_record_db_conn
    
    # Try to import psycopg2
    try:
        import psycopg2
    except ImportError:
        self.print_log(
            "w",
            "psycopg2 module not available. Database saving disabled. "
            "Install psycopg2 to enable database saving."
        )
        return None
    
    # Get database configuration from instance variables (set by read_settings())
    conn_params = {
        'host': getattr(self, 'run_record_database_host', ''),
        'port': getattr(self, 'run_record_database_port', ''),
        'dbname': getattr(self, 'run_record_database_name', 'run_info'),
        'user': getattr(self, 'run_record_database_user', ''),
        'password': getattr(self, 'run_record_database_pwd', ''),
    }
    
    # Build connection string - only add parameters if they are set (non-empty)
    conn_info_parts = ["%s=%s" % (k, v) for k, v in conn_params.items() if v]
    conn_info_parts.append("connect_timeout=10")
    conn_info = " ".join(conn_info_parts)
    
    try:
        self._run_record_db_conn = psycopg2.connect(conn_info)
        self.print_log(
            "d",
            "Database connection opened successfully for run record saving",
            2,
        )
        return self._run_record_db_conn
    except Exception as e:
        self.print_log(
            "w",
            "Failed to connect to database for run record saving: %s. "
            "Database saving will be skipped." % str(e)
        )
        self._run_record_db_conn = None
        return None


def get_db_schema(self):
    """Get database schema name from instance variable (set by read_settings())."""
    return getattr(self, 'run_record_database_schema', 'test')


def is_database_enabled(self):
    """Check if database saving is enabled via instance variable (set by read_settings())."""
    return hasattr(self, 'enable_run_record_database') and self.enable_run_record_database


def get_db_prefix(self):
    """Get database table prefix from instance variable (set by read_settings())."""
    return getattr(self, 'run_record_database_prefix', 'artdaq')


def create_tables_if_not_exist(cursor, dbschema, prefix="artdaq"):
    """Create database tables if they don't exist.
    
    Creates two tables:
    - {prefix}_components: stores process information (procinfo) per run
    - {prefix}_fcl: stores FHiCL content per run
    
    Args:
        cursor: psycopg2 cursor object
        dbschema: Database schema name
        prefix: Table name prefix (defaults to 'artdaq')
    """
    from psycopg2 import sql

    # Create {prefix}_components table
    # Uses run_number as primary key (saved during do_start_running when run_number is available)
    components_table = sql.Identifier(dbschema, "%s_components" % prefix)
    create_components_table = sql.SQL(
        "CREATE TABLE IF NOT EXISTS {table} ("
        "run_number INTEGER NOT NULL, "
        "name VARCHAR(255) NOT NULL, "
        "rank INTEGER NOT NULL, "
        "host VARCHAR(255) NOT NULL, "
        "port VARCHAR(50) NOT NULL, "
        "label VARCHAR(255) NOT NULL, "
        "subsystem VARCHAR(50), "
        "allowed_processors VARCHAR(255), "
        "target VARCHAR(255), "
        "insertion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "PRIMARY KEY (run_number, label)"
        ")"
    ).format(table=components_table)
    
    cursor.execute(create_components_table)
    
    # Create index on run_number
    components_index = sql.Identifier(dbschema, "%s_components_run_number_idx" % prefix)
    create_components_index = sql.SQL(
        "CREATE INDEX IF NOT EXISTS {index} ON {table} (run_number)"
    ).format(index=components_index, table=components_table)
    cursor.execute(create_components_index)
    
    # Create composite index on (run_number, name) for efficient queries by run and process type
    components_run_name_index = sql.Identifier(dbschema, "%s_components_run_name_idx" % prefix)
    create_components_run_name_index = sql.SQL(
        "CREATE INDEX IF NOT EXISTS {index} ON {table} (run_number, name)"
    ).format(index=components_run_name_index, table=components_table)
    cursor.execute(create_components_run_name_index)
    
    # Create {prefix}_fcl table
    # Uses run_number as primary key (saved during do_start_running when run_number is available)
    fcl_table = sql.Identifier(dbschema, "%s_fcl" % prefix)
    create_fcl_table = sql.SQL(
        "CREATE TABLE IF NOT EXISTS {table} ("
        "run_number INTEGER NOT NULL, "
        "name VARCHAR(255) NOT NULL, "
        "label VARCHAR(255) NOT NULL, "
        "content TEXT NOT NULL, "
        "insertion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "PRIMARY KEY (run_number, label)"
        ")"
    ).format(table=fcl_table)
    
    cursor.execute(create_fcl_table)
    
    # Create index on run_number 
    fcl_index = sql.Identifier(dbschema, "%s_fcl_run_number_idx" % prefix)
    create_fcl_index = sql.SQL(
        "CREATE INDEX IF NOT EXISTS {index} ON {table} (run_number)"
    ).format(index=fcl_index, table=fcl_table)
    cursor.execute(create_fcl_index)
    
    # Create composite index on (run_number, name) for efficient queries by run and process type
    fcl_run_name_index = sql.Identifier(dbschema, "%s_fcl_run_name_idx" % prefix)
    create_fcl_run_name_index = sql.SQL(
        "CREATE INDEX IF NOT EXISTS {index} ON {table} (run_number, name)"
    ).format(index=fcl_run_name_index, table=fcl_table)
    cursor.execute(create_fcl_run_name_index)

