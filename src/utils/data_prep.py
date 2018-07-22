#!/usr/bin/env python3
"""config.py

  This module provides utility functions to prepare data before committing it to
    the `mlbdb` database.
"""

import re
import pandas as pd

from datetime import datetime

def prep_statcast(data, schema):
  """Prepare a Statcast DataFrame

  Transforms the Statcast data to suit the `statcast` table schema. Adds
    an `event_id` field, to be used as a unique primary key in the database.
    Renames columns for results before April 24, 2017.

  Args:
    data (DataFrame): A DataFrame to prepare.
    schema (list): A schema list used to properly sort the DataFrame's
      columns.
  """

  data['event_id'] = data['game_pk'].astype(str) + '.' \
      + data['sv_id'].astype(str) + '.' \
      + data['pitch_number'].astype(str)

  data['load_time'] = datetime.utcnow()

  id_columns = [
      'sv_id',
      'batter',
      'pitcher',
      'game_pk',
      'umpire',
      'on_3b',
      'on_2b',
      'on_1b',
      'pos1_person_id',
      'pos2_person_id',
      'pos3_person_id',
      'pos4_person_id',
      'pos5_person_id',
      'pos6_person_id',
      'pos7_person_id',
      'pos8_person_id',
      'pos9_person_id'
  ]
  data = _clean_ids(data, id_columns)
  
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

  sorted_columns = [field['name'] for field in schema]
  data = data[sorted_columns]

  return data


def prep_players(data, schema):
  """Prepare a Player map DataFrame

  Transforms the Player data to suit the `players` table schema.

  Args:
    data (DataFrame): A DataFrame to prepare.
    schema (list): A schema list used to properly sort the DataFrame's
      columns.
  """

  data['load_time'] = datetime.utcnow()

  id_columns = [
      'mlb_id',
      'bp_id',
      'bref_id',
      'cbs_id',
      'espn_id',
      'fg_id',
      'lahman_id',
      'nfbc_id',
      'retro_id',
      'yahoo_id',
      'ottoneu_id',
      'rotowire_id'
  ]
  data = _clean_ids(data, id_columns)

  sorted_columns = [field['name'] for field in schema]
  data = data[sorted_columns]

  return data


def prep_players_historical(data, schema):
  """Prepare a Historical Player map DataFrame

  Transforms the Historical Player data to suit the `players` table schema.

  Args:
    data (DataFrame): A DataFrame to prepare.
    schema (list): A schema list used to properly sort the DataFrame's
      columns.
  """

  data['load_time'] = datetime.utcnow()

  data['mlb_name'] = data['FIRSTNAME'] + ' ' + data['LASTNAME']

  data.rename(columns={
      'MLBCODE': 'mlb_id',
      'RETROSHEETCODE': 'retro_id',
      'PLAYERID': 'bp_id'
  }, inplace=True)

  data.drop(columns=[
      'LASTNAME',
      'FIRSTNAME',
      'DAVENPORTCODE'
  ], inplace=True)

  id_columns = [
      'mlb_id',
      'retro_id',
      'bp_id'
  ]
  data = _clean_ids(data, id_columns)

  data = data[pd.notnull(data['mlb_id'])]

  sorted_columns = [field['name'] for field in schema]
  data = data.reindex(columns=sorted_columns)
  data = data[sorted_columns]

  return data


def _clean_ids(data, id_columns):
  """Clean the ID columns in a DataFrame

  Args:
    data (DataFrame): A DataFrame with ID columns to clean.
    id_columns (list): A list of ID column names.
  """

  data[id_columns] = data[id_columns].replace(r'(\.\d*)', '', regex=True)
  data[id_columns] = data[id_columns].astype(str)

  return data
