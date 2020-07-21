import json
import logging.config
import yaml
import csv
from io import StringIO


def get_value_deserializer(data_input_format):
    if data_input_format == 'json':
        return json.loads

    if data_input_format == 'csv':
        def unpack_csv(msg):
            csv_file = StringIO(msg)
            reader = csv.reader(csv_file)
            headers = next(reader)
            values = next(reader)
            return dict(zip(headers, values))
        return unpack_csv


def get_logger(log_config_path='utils/logger_config.yml'):
    with open(log_config_path, 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)
        logging.config.dictConfig(config)
        logger = logging.getLogger('default_logger')
        logger.debug('logger initialized.')
    return logger
