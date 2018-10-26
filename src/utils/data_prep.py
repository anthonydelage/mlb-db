#!/usr/bin/env python3
"""data_prep.py

  This module provides utility functions to prepare data before committing it
  to the `mlbdb` database.
"""

import re
import pandas as pd
import numpy as np

from copy import copy
from datetime import datetime


def prep_statcast(data, schema):
    """Prepare a Statcast DataFrame

    Transforms the Statcast data to suit the `statcast` table schema. Adds
        an `event_id` field, to be used as a unique primary key in the
        database. Renames columns for results before April 24, 2017.

    Args:
        data (DataFrame): A DataFrame to prepare.
        schema (list): A schema used to properly sort the DataFrame's columns.
    """

    output = data.copy()

    output['event_id'] = output['game_pk'].astype(str) + '.' \
        + output['at_bat_number'].apply(lambda x: _float_to_string(x)) + '.' \
        + output['pitch_number'].apply(lambda x: _float_to_string(x))

    output['load_time'] = datetime.utcnow()
    
    output.drop('pos2_person_id.1', axis=1, inplace=True)

    output.rename(columns={
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
    output[id_columns] = output[id_columns].fillna('')
    output[id_columns] = output[id_columns].applymap(
        lambda x: _float_to_string(x))

    sorted_columns = [field['name'] for field in schema]
    output = output[sorted_columns]

    return output


def prep_players(data, schema):
    """Prepare a Player map DataFrame

    Transforms the Player data to suit the `players` table schema.

    Args:
      data (DataFrame): A DataFrame to prepare.
      schema (list): A list used to properly sort the DataFrame's columns.
    """

    output = data.copy()

    output['load_time'] = datetime.utcnow()

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
    output[id_columns] = output[id_columns].fillna('')
    output[id_columns] = output[id_columns].applymap(
        lambda x: _float_to_string(x))

    sorted_columns = [field['name'] for field in schema]
    output = output[sorted_columns]

    return output


def prep_players_historical(data, schema):
    """Prepare a Historical Player map DataFrame

    Transforms the Historical Player data to suit the `players` table schema.

    Args:
      data (DataFrame): A DataFrame to prepare.
      schema (list): A list used to properly sort the DataFrame's columns.
    """

    output = data.copy()

    output['load_time'] = datetime.utcnow()

    output['mlb_name'] = output['FIRSTNAME'] + ' ' + output['LASTNAME']

    output.rename(columns={
        'MLBCODE': 'mlb_id',
        'RETROSHEETCODE': 'retro_id',
        'PLAYERID': 'bp_id'
    }, inplace=True)

    output.drop(columns=[
        'LASTNAME',
        'FIRSTNAME',
        'DAVENPORTCODE'
    ], inplace=True)

    id_columns = [
        'mlb_id',
        'retro_id',
        'bp_id'
    ]
    output[id_columns] = output[id_columns].fillna('')
    output[id_columns] = output[id_columns].applymap(
        lambda x: _float_to_string(x))

    output = output[pd.notnull(output['mlb_id'])]

    sorted_columns = [field['name'] for field in schema]
    output = output[sorted_columns]

    return output


def prep_weather(data, schema):
    """Prepare a Weather DataFrame

    Transforms the Weather data to suit the `weather` table schema.

    Args:
      data (DataFrame): A DataFrame to prepare.
      schema (list): A list used to properly sort the DataFrame's columns.
    """

    data['load_time'] = datetime.utcnow()

    data['attendance'] = data['attendance'].map(lambda x: _remove_thousand_sep(x))\
                                           .astype('int64')
    
    return data


def _float_to_string(value):
    """Convert floating point number to a string without decimal places

    Args:
        value (float64): A floating point number
    """

    output = copy(value)

    if type(output) == 'float' and np.isnan(output):
        return ''
    else:
        return re.sub(r'(\.\d*)', '', str(output))


def _remove_thousand_sep(value):
    """Removes thousand-separators in floats

    Args:
        value (float64): A floating point number
    """

    output = copy(value)

    return re.sub(r'\,', '', str(output))


def _clean_ids(data, id_columns):
    """Clean the ID columns in a DataFrame

    Args:
        data (DataFrame): A DataFrame with ID columns to clean.
        id_columns (list): A list of ID column names.
    """

    output = data.copy()

    output[id_columns] = output[id_columns].apply(lambda x: _float_to_string(x))

    return output
