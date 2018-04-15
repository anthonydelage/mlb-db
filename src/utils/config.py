#!/usr/bin/env python3
"""config.py

  This module provides utility functions to interact with the `config.yaml` file.
"""

import os
import yaml

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(DIR_PATH), '../config.yaml')

def get_config(key=None):
  """Get configuration

  Returns a dict containing the configuration requested.
  
  Args:
    key (str): A key to extract from the configuration file.
  """
  with open(CONFIG_PATH, 'r') as conf:
    try:
      config = yaml.load(conf)
    except yaml.YAMLError as exc:
      print('Error in configuration file: {}'.format(exc))

  if key is not None:
    return config[key]
  else:
    return config

