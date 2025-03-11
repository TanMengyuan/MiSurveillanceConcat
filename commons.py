import configparser

AGGREGATOR_SLICE_MAPPING = {
    "BY_DAYS": 8,  # YYYYMMDD
    "BY_HOURS": 10  # YYYYMMDDHH
}

def get_date_from_dir(dir_name, aggregator):
    slice_length = AGGREGATOR_SLICE_MAPPING[aggregator]
    return dir_name[:slice_length]

def load_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    root_dir = config.get('paths', 'root_dir', fallback='')
    output_dir = config.get('paths', 'output_dir', fallback='')
    cpu_cores = config.get('settings', 'cpu_cores', fallback=4)
    aggregator = config.get('settings', 'aggregator', fallback='BY_DAYS')
    if aggregator not in AGGREGATOR_SLICE_MAPPING:
        aggregator = 'BY_DAYS'

    return {
            'root_dir': root_dir.strip(),
            'output_dir': output_dir.strip(),
            'cpu_cores': cpu_cores,
            'aggregator': aggregator
        }
