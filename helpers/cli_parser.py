import argparse

def get_arguments_from_cli():
    cli_parser = argparse.ArgumentParser(
        description='script that grabs data from a Forza Motorsport stream and dumps it to a TSV or CSV file'
    )

    # Verbosity option
    cli_parser.add_argument('-ll', '--log_level', type=str, default='INFO',
                            choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
                            help='which logging log level to use')

    cli_parser.add_argument('-a', '--append', action='store_true',
                            default=False, help='if set, data will be appended to the given file')

    cli_parser.add_argument('-of', '--output_format', type=str, default='csv',
                            choices=['tsv', 'csv'],
                            help='what format to write out, "tsv" means tab-separated, "csv" comma-separated; default is "csv"')

    cli_parser.add_argument('-pf', '--packet_format', type=str, default='dash',
                            choices=['sled', 'dash', 'fh4'],
                            help='what format the packets coming from the game is, either "sled" or "dash"')

    cli_parser.add_argument('-c', '--config_file', type=str,
                            help='path to the YAML configuration file')

    cli_parser.add_argument('-p', '--port', type=int, default='4843',
                            help='port number to listen on')

    cli_parser.add_argument('-o', '--output_filename', type=str, default='forza_data.csv',
                            help='path to the file we will output')

    return cli_parser.parse_args()