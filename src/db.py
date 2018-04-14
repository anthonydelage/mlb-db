#!/usr/bin/env python3
"""db.py

This module is used to initialize tables in the `mlbdb` database.

Example:
  $ python db.py
"""

import os
import pymysql

import utils.config as config

DB_CONFIG = config.get_config('database')
TABLES_SQL_PATH = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'db/tables.sql')

def _run_sql(cursor, sql_path):
  """Run SQL from file in database

  Gets a SQL file and runs it in the database.

  Args:
    cursor (cursor): A PyMySQL cursor connected to the database.
    sql_path (string): A path to a SQL file containing table creation statements.
  """

  with open(sql_path, 'r') as sql:
    sql = sql.read().replace('\n', ' ')
    statements = sql.split(';')[:-1]

    for statement in statements:
      cursor.execute(statement)

def main():
  """Main

    Creates tables based on SQL statements in `db/tables.sql`.
  """
  db = pymysql.connect(
      DB_CONFIG['host'], DB_CONFIG['username'], DB_CONFIG['password'], DB_CONFIG['db'])
  cursor = db.cursor()

  _run_sql(cursor, TABLES_SQL_PATH)

if __name__ == "__main__":
  main()

