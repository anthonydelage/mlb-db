#!/usr/bin/env python3
"""update.py

This module is used to update tables in the `mlbdb` database.

Example:
  $ python update.py --year=2018

Arguments:
  --year (int): A year to update for the `statcast` table. Defaults to the current year.
  --no-statcast: Skips updating the `statcast` table.
  --no-players: Skips updating the `players` table.
  --historical-players: Enables historical player updates (backfills old IDs).
"""

import os
import argparse
import re
import datetime
import pandas as pd
import numpy as np
import mysql.connector
from sqlalchemy import create_engine

import utils.config as config
import utils.data_prep as data_prep

from urllib.error import HTTPError

DB_CONFIG = config.get_config('database')
API_CONFIG = config.get_config('api')
CURRENT_YEAR = datetime.datetime.now().year

TEAMS = ['ARI', 'ATL', 'BAL', 'BOS', 'CHC',
         'CIN', 'CLE', 'COL', 'CWS', 'DET',
         'HOU', 'KC', 'LAA', 'LAD', 'MIA',
         'MIL', 'MIN', 'NYM', 'NYY', 'OAK',
         'PHI', 'PIT', 'SD', 'SEA', 'SF',
         'STL', 'TB', 'TEX', 'TOR', 'WSH']


def update_statcast(engine, year):
  """Update statcase table in database

  Queries the Baseball Savant CSV API for every team in the given year,
    then inserts the data in the MySQL `mlbdb` database's `statcast` table. 

  Args:
    engine (engine): A SQLAlchemy engine connected to the database to update.
    year (int): A year to update. Defaults to the current year.
  """

  base_uri = API_CONFIG['statcast']
  year = year or CURRENT_YEAR

  for team in TEAMS:
    params = {
      'team': team,
      'year': year,
      'time': datetime.datetime.now().strftime('%H:%M:%S')
    }
    print('UPDATING {team}, {year} AT {time}'.format(**params))

    uri = base_uri.format(**params)
    dtypes = {
      'sv_id': 'str',
      'batter': 'str',
      'pitcher': 'str',
      'game_pk': 'str',
      'umpire': 'str',
      'on_3b': 'str',
      'on_2b': 'str',
      'on_1b': 'str',
      'pos1_person_id': 'str',
      'pos2_person_id': 'str',
      'pos3_person_id': 'str',
      'pos4_person_id': 'str',
      'pos5_person_id': 'str',
      'pos6_person_id': 'str',
      'pos7_person_id': 'str',
      'pos8_person_id': 'str',
      'pos9_person_id': 'str'
    }
    data = _get_data(uri, dtypes=dtypes)

    if not data.empty:
      data = data_prep.prep_statcast(data)
      _to_db_with_temp(data=data, engine=engine, table_name=DB_CONFIG['statcast_table'])


def update_players(engine):
  """Update players table in database

  Queries the Crunchtime Baseball CSV API for every player in MLB,
    then inserts the data in the MySQL `mlbdb` database's `players` table. 

  Args:
    engine (engine): A SQLAlchemy engine connected to the database to update.
  """

  uri = API_CONFIG['players']
  dtypes = {
    'mlb_id': 'str',
    'bp_id': 'str',
    'bref_id': 'str',
    'cbs_id': 'str',
    'espn_id': 'str',
    'fg_id': 'str',
    'lahman_id': 'str',
    'nfbc_id': 'str',
    'retro_id': 'str',
    'yahoo_id': 'str',
    'ottoneu_id': 'str',
    'rotowire_id': 'str'
  }
  data = _get_data(uri, dtypes=dtypes, encoding='ISO-8859-1')

  if not data.empty:
    data = data_prep.prep_players(data)
    _to_db_with_temp(data=data, engine=engine, table_name=DB_CONFIG['players_table'])


def update_players_historical(engine):
  """Update players table in database

  Queries the Crunchtime Baseball CSV API for every player in MLB,
    then inserts the data in the MySQL `mlbdb` database's `players` table. 

  Args:
    engine (engine): A SQLAlchemy engine connected to the database to update.
  """

  uri = API_CONFIG['players_historical']
  dtypes = {
    'MLBCODE': 'str',
    'RETROSHEETCODE': 'str',
    'PLAYERID': 'str'
  }
  data = _get_data(uri, dtypes=dtypes, encoding='ISO-8859-1')

  if not data.empty:
    data = data_prep.prep_players_historical(data)
    _to_db_with_temp(data=data, engine=engine, table_name=DB_CONFIG['players_table'], method='ignore')


def _get_data(uri, max_tries=10, encoding='utf-8', dtypes={}):
  """Get pandas DataFrame from URI

  Queries provided URI for a CSV, then returns it as a DataFrame. Exponentially
    backs off.

  Args:
    uri (string): A URI identifying the data's location.
    max_tries (int): A maximum number of tries to query the URI. Defaults to 10.
    encoding (string): An encoding string that determines how the URI resource is 
      intepreted. Defaults to 'utf-8'.
    dtypes (dict): A dict defining the data types for any columns that need
      to be manually specified.
  """

  successful = False
  backoff_time = 30
  tries = 0
  data = pd.DataFrame()

  while not successful and tries <= max_tries:
      try:
          data = pd.read_csv(uri, low_memory=False, encoding=encoding, dtype=dtypes)
          successful = True
      except HTTPError:
          backoff_time = min(backoff_time * 2, 60*60)
          tries += 1

  return data


def _to_db_with_temp(data, engine, table_name, method='replace', chunksize=5000):
  """Insert data in database using a temporary table

  Creates a temporary table in the database to write to before committing to
    the correct table. Prevents duplicate records
    in the database.

  Args:
    data (DataFrame): A DataFrame to insert into the database.
    engine (engine): A SQLAlchemy engine connected to the database.
    table_name (string): A name of the database table to write to.
    method (string): A string determining how duplicate records are handled.
      'replace' forces new duplicate records to overwrite existing ones.
      'ignore' prevents new duplicate records from overwriting existing ones.
    chunksize (int): A number of records to insert into the database at once.
  """

  engine.execute('SET GLOBAL MAX_ALLOWED_PACKET=67108864;')
  engine.execute('DROP TABLE IF EXISTS temp;')
  engine.execute('CREATE TABLE temp SELECT * FROM {} WHERE 1=0;'.format(table_name))

  data.to_sql(name='temp', con=engine, if_exists='append',
              index=False, chunksize=chunksize)

  if method == 'replace':
    engine.execute('REPLACE INTO {} SELECT * FROM temp;'.format(table_name))
  elif method == 'ignore':
    engine.execute('INSERT IGNORE INTO {} SELECT * FROM temp;'.format(table_name))
  
  engine.execute('DROP TABLE temp;')


def main():
  """Main"""
  parser = argparse.ArgumentParser()
  parser.add_argument('--no-statcast', help='Do not update the statcast table.', action='store_true')
  parser.add_argument('--no-players', help='Do not update the players table.', action='store_true')
  parser.add_argument('--historical-players', help='Update the players table with historical IDs.', action='store_true')
  parser.add_argument('--year', help='Enter the year to update. Defaults to current year.', type=int)
  args = parser.parse_args()

  engine = create_engine('mysql+mysqlconnector://{username}:{password}@{host}/{db}'.format(**{
    'username': DB_CONFIG['username'],
    'password': DB_CONFIG['password'],
    'host': DB_CONFIG['host'],
    'db': DB_CONFIG['db']
  }), echo=False)

  if not args.no_statcast:
    print('\nUPDATING STATCAST\n')
    update_statcast(engine, args.year)
  if not args.no_players:
    print('\nUPDATING PLAYERS\n')
    update_players(engine)
  if args.historical_players:
    print('\nUPDATING HISTORICAL PLAYERS\n')
    update_players_historical(engine)

if __name__ == "__main__":
  main()
