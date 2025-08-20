#!/usr/bin/env python3
"""update.py

This module is used to update tables in the `mlbdb` database.

Example:
  $ python update.py --year=2018

Arguments:
  --year (int): A year to update for the `statcast` table. Defaults to the current year.
  --statcast: Updates the `statcast` table.
  --players: Updates the `players` table.
  --historical-players: Updates historical players.
"""

import os
import argparse
import logging
import re
import pandas as pd

from datetime import datetime
from pandas_gbq import to_gbq
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

from utils.config import get_config
from utils.data_prep import (
    prep_statcast,
    prep_players,
    prep_players_historical,
    prep_weather
)
from utils.schema import schema_subset, schema_to_dtypes

from urllib.error import HTTPError

BQ_CONFIG = get_config('bigquery')
CREDENTIALS_CONFIG = get_config('credentials')
API_CONFIG = get_config('api')
CONSTANTS = get_config('constants')

SERVICE_ACCOUNT_PATH = os.path.join(
    './credentials', CREDENTIALS_CONFIG['bigquery'])
BIGQUERY_CREDENTIALS = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_PATH)

logging.basicConfig(format='(%(asctime)s) %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _update_statcast(client, project_id, table_id, schema, year):
    """Update statcase table in database

    Queries the Baseball Savant CSV API for every team in the given year,
      then inserts the data in the `statcast` table.

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
    teams = CONSTANTS['teams']
    year = year or datetime.now().year

    for team in teams:
        params = {
            'team': team,
            'year': year
        }
        logger.info('UPDATING {team}, {year}'.format(**params))

        uri = base_uri.format(**params)
        dtypes = schema_to_dtypes(schema)
        data = _get_data(uri, dtypes=dtypes)

        if not data.empty:
            data = prep_statcast(data, schema)

            gbq_schema = schema_subset(schema, ['name', 'type'])
            to_gbq(dataframe=data,
                   destination_table=table_id,
                   project_id=project_id,
                   if_exists='append',
                   table_schema=gbq_schema,
                   location='US',
                   credentials=BIGQUERY_CREDENTIALS)

    _remove_bq_duplicates(client=client,
                          project_id=project_id,
                          table_id=table_id,
                          primary_key='event_id',
                          dedupe_value='load_time')


def _update_players(client, project_id, table_id, schema):
    """Update players table in database

    Queries the Crunchtime Baseball CSV API for every player in MLB,
        then inserts the data in the `players` table. 

    Args:
        client (BigQuery Client): A BigQuery client used to run the duplicate
            removal DML query.
        project_id (str): A BigQuery project to write to.
        table_id (str): A BigQuery table to write to. Should be formatted as
            `dataset_id.table_id`
        schema (dict): A schema dictionary for the target table.
    """

    uri = API_CONFIG['players']
    dtypes = schema_to_dtypes(schema)
    data = _get_data(uri, dtypes=dtypes, encoding='ISO-8859-1')

    if not data.empty:
        data = prep_players(data, schema)

        gbq_schema = schema_subset(schema, ['name', 'type'])
        to_gbq(dataframe=data,
               destination_table=table_id,
               project_id=project_id,
               if_exists='append',
               table_schema=gbq_schema,
               location='US',
               credentials=BIGQUERY_CREDENTIALS)

    _remove_bq_duplicates(client=client,
                          project_id=project_id,
                          table_id=table_id,
                          primary_key='mlb_id',
                          dedupe_value='load_time')


def _update_players_historical(project_id, table_id, schema):
    """Update players table in database

    Queries the Baseball Prospectus CSV API for every player in MLB history,
        then inserts the data in the `players` table. 

    Args:
        project_id (str): A BigQuery project to write to.
        table_id (str): A BigQuery table to write to. Should be formatted as
            `dataset_id.table_id`.
        schema (dict): A schema dictionary for the target table.
    """

    uri = API_CONFIG['players_historical']
    dtypes = schema_to_dtypes(schema)
    data = _get_data(uri, dtypes=dtypes, encoding='ISO-8859-1')

    if not data.empty:
        data = prep_players_historical(data, schema)

        gbq_schema = schema_subset(schema, ['name', 'type'])
        to_gbq(dataframe=data,
               destination_table=table_id,
               project_id=project_id,
               if_exists='replace',
               table_schema=gbq_schema,
               location='US',
               credentials=BIGQUERY_CREDENTIALS)


def _update_weather(project_id, table_id, schema):
    """Update weather table in database

    Queries the a Box file maintained by Bill Petti for gamneday weather,
        then inserts the data in the `weather` table. Data can be found
        here: https://app.box.com/v/gamedayboxscoredata

    Args:
        project_id (str): A BigQuery project to write to.
        table_id (str): A BigQuery table to write to. Should be formatted as
            `dataset_id.table_id`.
        schema (dict): A schema dictionary for the target table.
    """

    uri = API_CONFIG['weather']
    dtypes = schema_to_dtypes(schema)
    # `attendance`` uses commas as a thousand-separator
    dtypes['attendance'] = 'str'

    data = _get_data(uri, dtypes=dtypes)

    if not data.empty:
        data = prep_weather(data, schema)

        gbq_schema = schema_subset(schema, ['name', 'type'])
        to_gbq(dataframe=data,
               destination_table=table_id,
               project_id=project_id,
               if_exists='replace',
               table_schema=gbq_schema,
               location='US',
               credentials=BIGQUERY_CREDENTIALS)


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
            storage_options = {'User-Agent': 'Mozilla/9.0'}
            data = pd.read_csv(uri,
                               low_memory=False,
                               encoding=encoding,
                               dtype=dtypes,
                               float_precision='round_trip',
                               storage_options=storage_options)
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


def main():
    """Main"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--statcast',
                        help='Update the statcast table.', action='store_true')
    parser.add_argument('--players',
                        help='Update the players table.', action='store_true')
    parser.add_argument('--weather',
                        help='Update the weather table.', action='store_true')
    parser.add_argument('--historical-players',
                        help='Update the players table with historical IDs.', action='store_true')
    parser.add_argument('--year',
                        help='Enter the year to update. Defaults to current year.', type=int)
    args = parser.parse_args()

    client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
    project_id = BQ_CONFIG['project_id']
    dataset_id = BQ_CONFIG['dataset_id']

    if args.statcast:
        logger.info('UPDATING STATCAST')

        statcast_name = BQ_CONFIG['tables']['statcast']['name']
        statcast_schema = BQ_CONFIG['tables']['statcast']['fields']
        table_id = dataset_id + '.' + statcast_name

        _update_statcast(client=client, project_id=project_id, table_id=table_id,
                         schema=statcast_schema, year=args.year)

    if args.players:
        logger.info('UPDATING PLAYERS')

        player_name = BQ_CONFIG['tables']['players']['name']
        player_schema = BQ_CONFIG['tables']['players']['fields']
        table_id = dataset_id + '.' + player_name

        _update_players(client=client, project_id=project_id, table_id=table_id,
                        schema=player_schema)

    if args.weather:
        logger.info('UPDATING WEATHER')

        weather_name = BQ_CONFIG['tables']['weather']['name']
        weather_schema = BQ_CONFIG['tables']['weather']['fields']
        table_id = dataset_id + '.' + weather_name

        _update_weather(project_id=project_id,
                        table_id=table_id, schema=weather_schema)

    if args.historical_players:
        logger.info('UPDATING HISTORICAL PLAYERS')

        player_name = BQ_CONFIG['tables']['players']['name']
        player_schema = BQ_CONFIG['tables']['players']['fields']
        table_id = dataset_id + '.' + player_name

        _update_players_historical(project_id=project_id, table_id=table_id,
                                   schema=player_schema)


if __name__ == "__main__":
    main()
