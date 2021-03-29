import logging
import yaml


LOG = logging.getLogger(__name__)


def get_dict_config_file(config_file: str, log_level: str = 'INFO') -> dict:
    if config_file is None:
        LOG.info(f'no config file supplied!')
        return {}
    LOG.info(f'opening configuration yaml at {config_file}')
    with open(config_file) as f:
            config = yaml.safe_load(f)
            LOG.info(f'successfully loaded yaml')
    return config
