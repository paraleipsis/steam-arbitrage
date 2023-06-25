import logging.config
import yaml

from pathlib import Path


def load_config():
    with open(Path(__file__).resolve().parent / 'config.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    configs = {
        'error': logging.getLogger('errorLogger'),
        'info': logging.getLogger('infoLogger'),
        'stdout_error': logging.getLogger('consoleErrorLogger'),
        'stdout_info': logging.getLogger('consoleInfoLogger')
    }

    return configs
