#!/usr/bin/env python3
"""setup.py

This module is used to set up the mlb-db tables in a BigQuery.

Example:
$ python setup.py
"""

import os
from google.cloud import bigquery

from utils.config import get_config

BQ_CONFIG = get_config('bigquery')
CREDENTIALS_CONFIG = get_config('credentials')
SERVICE_ACCOUNT_PATH = os.path.join('./credentials', CREDENTIALS_CONFIG['bigquery'])

def main():
    """Main

    Creates tables in BigQuery based on schema configurations in `config.yaml`.
     """

    client = bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)

    dataset_ref = client.dataset(BQ_CONFIG['dataset_id'])

    tables = list(client.list_tables(dataset_ref))
    table_ids = [item.table_id for item in tables]
    tables = BQ_CONFIG['tables']

    for table in tables:
        _table = tables[table]
        table_name = _table['name']
        table_fields = _table['fields']
        
        if not (table_name in table_ids):
            table_ref = dataset_ref.table(table_name)
            schema = []

            for field in table_fields:
                field = bigquery.SchemaField(name=field['name'],
                                            field_type=field['type'],
                                            mode=field['mode'])
                schema.append(field)

            table = bigquery.Table(table_ref, schema=schema)
            table = client.create_table(table)

if __name__ == "__main__":
    main()
