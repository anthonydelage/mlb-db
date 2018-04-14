#!/usr/bin/env python3
"""update.py

This module is used to update tables in the `mlbdb` database.

Example:
  $ python update.py --year=2018

Arguments:
  --year (int): A year to update for the `statcast` table. Defaults to the current year.
  --no-statcast: Skips updating the `statcast` table.
  --no-players: Skips updating the `players` table.
"""

import os
import argparse
import datetime
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

import utils.config as config

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
    data = _get_data(uri)

    if not data.empty:
      data = _prep_statcast(data)
      _to_db_with_temp(data, engine, table_name=DB_CONFIG['statcast_table'])

def update_players(engine):
  """Update players table in database

  Queries the Crunchtime Baseball CSV API for every player in MLB,
    then inserts the data in the MySQL `mlbdb` database's `players` table. 

  Args:
    engine (engine): A SQLAlchemy engine connected to the database to update.
  """

  uri = API_CONFIG['players']
  data = _get_data(uri, encoding='ISO-8859-1')

  if not data.empty:
    _to_db_with_temp(data, engine, table_name=DB_CONFIG['players_table'])

def _get_data(uri, max_tries=10, encoding='utf-8'):
  """Get pandas DataFrame from URI

  Queries provided URI for a CSV, then returns it as a DataFrame. Exponentially
    backs off.

  Args:
    uri (string): A URI identifying the data's location.
    max_tries (int): A maximum number of tries to query the URI. Defaults to 10.
    encoding (string): An encoding string that determines how the URI resource is 
      intepreted. Defaults to 'utf-8'.
  """

  successful = False
  backoff_time = 30
  tries = 0
  data = pd.DataFrame()

  while not successful and tries <= max_tries:
      try:
          data = pd.read_csv(uri, low_memory=False, encoding=encoding)
          successful = True
      except HTTPError:
          backoff_time = min(backoff_time * 2, 60*60)
          tries += 1

  return data

def _prep_statcast(data):
  """Prepare a Statcast DataFrame

  Transforms the Statcast data to suit the `statcast` table schema. Adds
    an `event_id` field, to be used as a unique primary key in the database.
    Renames columns for results before April 24, 2017.
  """

  data['event_id'] = data['game_pk'].astype(str) + '.' \
      + data['sv_id'].astype(str) + '.' \
      + data['pitch_number'].astype(str)
  data.drop('pos2_person_id.1', axis=1, inplace=True)

  data.rename(columns={
      'start_speed': 'release_speed',
      'x0': 'release_pos_x',
      'z0': 'release_pos_z',
      'spin_rate': 'spin_rate_deprecated',
      'break_angle': 'break_angle_deprecated',
      'break_length': 'break_length_deprecated',
      'inning_top_bottom': 'inning_topbot',
      'tfs': 'tfs_deprecated',
      'tfs_zulu': 'tfs_zulu_deprecated',
      'catcher': 'pos2_person_id',
      'hit_speed': 'launch_speed',
      'hit_angle': 'launch_angle',
      'px': 'plate_x',
      'pz': 'plate_z'
  }, inplace=True)

  return data

def _to_db_with_temp(data, engine, table_name, chunksize=5000):
  """Insert data in database using a temporary table

  Creates a temporary table in the database to write to before committing to
    the correct table via 'REPLACE INTO' syntax. Prevents duplicate records
    in the database.

  Args:
    data (DataFrame): A DataFrame to insert into the database.
    engine (engine): A SQLAlchemy engine connected to the database.
    table_name (string): A name of the database table to write to.
    chunksize (int): A number of records to insert into the database at once.
  """

  engine.execute('SET GLOBAL MAX_ALLOWED_PACKET=67108864;')
  engine.execute('DROP TABLE IF EXISTS temp;')
  engine.execute('CREATE TABLE temp SELECT * FROM {} WHERE 1=0;'.format(table_name))

  data.to_sql(name='temp', con=engine, if_exists='append',
              index=False, chunksize=chunksize)

  engine.execute('REPLACE INTO {} SELECT * FROM temp;'.format(table_name))
  engine.execute('DROP TABLE temp;')

def main():
  """Main"""
  parser = argparse.ArgumentParser()
  parser.add_argument('--no-statcast', help='Do not update the statcast table.', action='store_true')
  parser.add_argument('--no-players', help='Do not update the players table.', action='store_true')
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

if __name__ == "__main__":
  main()
