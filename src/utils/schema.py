#!/usr/bin/env python3
"""schema.py

  This module provides utility functions to manage table schemas.
"""

import numpy as np

from copy import deepcopy


def schema_subset(schema, keys):
    """Gets a subset of keys from a schema dictionary

    Args:
        schema (list): A schema to get the keys from.
        keys (list): A list of keys names to get.
    """

    if not isinstance(keys, list):
        keys = [keys]

    output = [{k: v for k, v in field.items() if k in keys}
              for field in schema]

    return output


def schema_to_dtypes(schema):
    """Converts a schema to a Pandas dtypes dictionary

    Notes:
    - Integers use 'Int64' instead of 'int64' to handle NaN values.
    - Floats use 'str' instead of 'float64' to play nicely with Parquet conversion.
    This would be a problem were there to be any computation on these columns before
    transferring the data to BigQuery.

    Args:
        schema (list): A schema to get the dtypes from.
    """

    dtypes = {}

    for item in schema:
        name = item['name']
        type = item['type']

        if type == 'STRING':
            dtypes[name] = 'str'

        elif type == 'INTEGER':
            dtypes[name] = 'Int64'

        elif type == 'BIGNUMERIC':
            dtypes[name] = 'str'
        
        elif type == 'BIGNUMERIC':
            dtypes[name] = 'str'

        elif type == 'DATETIME':
            dtypes[name] = 'str'

        elif type == 'DATE':
            dtypes[name] = 'str'

    return dtypes
