#!/usr/bin/env python3

import os
import yaml

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(DIR_PATH), '../config.yaml')

def get_config(key=None):
  with open(CONFIG_PATH, 'r') as conf:
    try:
      config = yaml.load(conf)
    except yaml.YAMLError as exc:
      print('Error in configuration file: {}'.format(exc))

  if key is not None:
    return config[key]
  else:
    return config

