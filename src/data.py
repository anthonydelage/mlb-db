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
import pandas as pd
from datetime import datetime
from pandas_gbq import to_gbq
from google.cloud import bigquery

from utils.config import get_config
from utils.data_prep import prep_statcast, prep_players, prep_players_historical

from urllib.error import HTTPError

BQ_CONFIG = get_config('bigquery')
CREDENTIALS_CONFIG = get_config('credentials')
API_CONFIG = get_config('api')
SERVICE_ACCOUNT_PATH = os.path.join(
    './credentials', CREDENTIALS_CONFIG['bigquery'])


def _update_statcast(client, project_id, table_id, schema, year):
  """Update statcase table in database

  Queries the Baseball Savant CSV API for every team in the given year,
    then inserts the data in a BigQuery table.

  Args:
    client (BigQuery Client): A BigQuery client used to run the duplicate
      removal DML query.
    project_id (str): A BigQuery project to write to.
    table_id (str): A BigQuery table to write to. Should be formatted as
      `dataset_id.table_id`.
    schema (dict): A schema dictionary for the target table.
    year (int): A year to update. Defaults to the current year.
  """

  base_uri = API_CONFIG['statcast']
  year = year or datetime.now().year
  teams = ['ARI', 'ATL', 'BAL', 'BOS', 'CHC',
           'CIN', 'CLE', 'COL', 'CWS', 'DET',
           'HOU', 'KC', 'LAA', 'LAD', 'MIA',
           'MIL', 'MIN', 'NYM', 'NYY', 'OAK',
           'PHI', 'PIT', 'SD', 'SEA', 'SF',
           'STL', 'TB', 'TEX', 'TOR', 'WSH']

  for team in teams:
    params = {
      'team': team,
      'year': year,
      'time': datetime.now().strftime('%H:%M:%S')
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
      data = prep_statcast(data, schema)

      to_gbq(dataframe=data, destination_table=table_id, project_id=project_id,
             if_exists='append', table_schema=schema, chunksize=5000, location='US',
             private_key=SERVICE_ACCOUNT_PATH)

  _remove_bq_duplicates(client=client, project_id=project_id, table_id=table_id,
                        primary_key='event_id', dedupe_value='load_time')

def _update_players(client, project_id, table_id, schema):
  """Update players table in database

  Queries the Crunchtime Baseball CSV API for every player in MLB,
    then inserts the data in the MySQL `mlbdb` database's `players` table. 

  Args:
    client (BigQuery Client): A BigQuery client used to run the duplicate
      removal DML query.
    project_id (str): A BigQuery project to write to.
    table_id (str): A BigQuery table to write to. Should be formatted as
      `dataset_id.table_id`
    schema (dict): A schema dictionary for the target table.
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
    data = prep_players(data, schema)
    
    to_gbq(dataframe=data, destination_table=table_id, project_id=project_id,
           if_exists='append', table_schema=schema, chunksize=5000, location='US',
           private_key=SERVICE_ACCOUNT_PATH)
          
  _remove_bq_duplicates(client=client, project_id=project_id, table_id=table_id,
                        primary_key='mlb_id', dedupe_value='load_time')


def _update_players_historical(project_id, table_id, schema):
  """Update players table in database

  Queries the Crunchtime Baseball CSV API for every player in MLB,
    then inserts the data in the MySQL `mlbdb` database's `players` table. 

  Args:
    project_id (str): A BigQuery project to write to.
    table_id (str): A BigQuery table to write to. Should be formatted as
      `dataset_id.table_id`.
    schema (dict): A schema dictionary for the target table.
  """

  uri = API_CONFIG['players_historical']
  dtypes = {
    'MLBCODE': 'str',
    'RETROSHEETCODE': 'str',
    'PLAYERID': 'str'
  }
  data = _get_data(uri, dtypes=dtypes, encoding='ISO-8859-1')

  if not data.empty:
    data = prep_players_historical(data, schema)
    
    to_gbq(dataframe=data, destination_table=table_id, project_id=project_id,
           if_exists='replace', table_schema=schema, chunksize=5000, location='US',
           private_key=SERVICE_ACCOUNT_PATH)

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

def _remove_bq_duplicates(client, project_id, table_id, primary_key, dedupe_value):
  """Removes duplicates from a BigQuery table using a DML operation

  Args:
    client (BigQuery Client): A BigQuery client used to run the duplicate
      removal DML query.
    project_id (str): A BigQuery project to write to.
    table_id (str): A BigQuery table to write to. Should be formatted as
      `dataset_id.table_id`.
    primary_key (str): A table field that cannot be duplicated.

  """

  _delete_query = \
  """
  DELETE FROM `{project_id}.{table_id}`
  WHERE STRUCT({key}, {dedupe_value}) NOT IN (
          SELECT AS STRUCT
            {key},
            MAX({dedupe_value}) AS {dedupe_value}
          FROM `{project_id}.{table_id}`
          GROUP BY 1
        )
  """.format(project_id=project_id, table_id=table_id, key=primary_key,
             dedupe_value=dedupe_value)

  client.query(_delete_query)

def _remove_key(schema, key):
  """Removes a key from a schema dictionary

  Args:
    schema (list): A schema to remove the key from.
    key (str): A key name to remove.
  """

  for item in schema:
    del item[key]

  return schema

def main():
  """Main"""
  parser = argparse.ArgumentParser()
  parser.add_argument('--no-statcast', help='Do not update the statcast table.', action='store_true')
  parser.add_argument('--no-players', help='Do not update the players table.', action='store_true')
  parser.add_argument('--historical-players', help='Update the players table with historical IDs.', action='store_true')
  parser.add_argument('--year', help='Enter the year to update. Defaults to current year.', type=int)
  args = parser.parse_args()

  client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
  project_id = BQ_CONFIG['project_id']
  dataset_id = BQ_CONFIG['dataset_id']

  if not args.no_statcast:
    print('\nUPDATING STATCAST\n')

    _statcast_name = BQ_CONFIG['tables']['statcast']['name']
    _statcast_schema = _remove_key(
        BQ_CONFIG['tables']['statcast']['fields'], 'mode')
    _table_id = dataset_id + '.' + _statcast_name

    _update_statcast(client=client, project_id=project_id, table_id=_table_id,
                     schema=_statcast_schema, year=args.year)

  if not args.no_players:
    print('\nUPDATING PLAYERS\n')

    _player_name = BQ_CONFIG['tables']['players']['name']
    _player_schema = _remove_key(
        BQ_CONFIG['tables']['players']['fields'], 'mode')
    _table_id = dataset_id + '.' + _player_name

    _update_players(client=client, project_id=project_id, table_id=_table_id,
                    schema=_player_schema)

  if args.historical_players:
    print('\nUPDATING HISTORICAL PLAYERS\n')

    _player_name = BQ_CONFIG['tables']['players']['name']
    _player_schema = _remove_key(
        BQ_CONFIG['tables']['players']['fields'], 'mode')
    _table_id = dataset_id + '.' + _player_name

    _update_players_historical(project_id=project_id, table_id=_table_id,
                               schema=_player_schema)

if __name__ == "__main__":
  main()
