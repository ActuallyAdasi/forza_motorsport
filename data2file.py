#!/usr/env/python
# -*- coding: utf-8 -*-
'''
Script to listen on a given port for UDP packets sent by a Forza Motorsport 7
"data out" stream and write the data to a TSV file.

Copyright (c) 2018 Morten Wang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import sys
import csv
import logging
import socket

import datetime as dt

from fdp import ForzaDataPacket
from helpers import cli_parser, config_parser

logging.basicConfig(filename=f'data2file-{dt.date.now().date()}.log', level=logging.INFO)
LOG = logging.getLogger(__name__)
console_log_handler = logging.StreamHandler(sys.stdout)
console_log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_log_handler.setFormatter(formatter)
LOG.addHandler(console_log_handler)


def dump_stream(port=None, output_filename=None, output_format='tsv',
                append=False, packet_format='dash', log_level=logging.INFO, config_file=None):
    '''
    Opens the given output filename, listens to UDP packets on the given port
    and writes data to the file.

    :param port: listening port number
    :type port: int

    :param output_filename: path to the file we will write to
    :type output_filename: str

    :param output_format: what output_format to write out, either 'tsv' or 'csv'
    :type output_format: str

    :param append: if set, the output file will be opened for appending and
                   the header with column names is not written out
    :type append: bool

    :param packet_format: the packet format sent by the game, one of either
                          'sled' or 'dash'
    :type packet_format str

    :param log_level: the log level to use, see https://docs.python.org/3/library/logging.html#levels
    :type log_level str

    :param config_file: path to the YAML configuration file
    :type config_file: str
    '''
    LOG.info("Dumping stream...")
    params = None
    LOG.setLevel(log_level)
    console_log_handler.setLevel(log_level)

    if config_file:
        LOG.info(f'Checking configuration file for parameters and overrides...')
        config = config_parser.get_dict_config_file(config_file, log_level)

        # TODO: refactor this spaghetti code elsewhere
        ## The configuration can override everything
        if 'port' in config:
            port = config['port']
            LOG.info(f"set port to {port}")

        if 'output_filename' in config:
            output_filename = config['output_filename']
            LOG.info(f"set output_filename to {output_filename}")

        if 'output_format' in config:
            output_format = config['output_format']
            LOG.info(f"set output_format to {output_format}")

        if 'append' in config:
            append = config['append']
            LOG.info(f"set append to {append}")

        if 'packet_format' in config:
            packet_format = config['packet_format']
            LOG.info(f"set packet_format to {packet_format}")

        if 'log_level' in config:
            log_level = config['log_level']
            LOG.setLevel(log_level)
            console_log_handler.setLevel(log_level)
            LOG.info(f"set log_level to {log_level}")

        if 'parameter_list' in config:
            params = config['parameter_list']
            LOG.info(f"set parameter_list to {params}")

        LOG.info(f'Done checking configuration file for parameters and overrides.')

    if not port or not output_filename:
        raise Exception(f"ERROR: could not determine port and output filename from CLI or config file!")

    if not params:
        LOG.info(f"did not find parameter list in configuration file. Using all properties")
        params = ForzaDataPacket.get_all_props(packet_format = packet_format)

    # TODO: refactor log_wall_clock, it seems unnecessary
    log_wall_clock = False
    if 'wall_clock' in params:
        log_wall_clock = True

    open_mode = ['w', 'a'][append]

    with open(output_filename, open_mode, buffering=1) as outfile:
        # TODO: refactor the following two blocks as well, they seem awkward
        if output_format == 'csv':
            csv_writer = csv.writer(outfile)
            if not append:
                csv_writer.writerow(params)

        ## If we're not appending, add a header row:
        # TODO: consider scenario where we are appending, but the list of parameters changes
        if output_format == 'tsv' and not append:
            outfile.write('\t'.join(params))
            outfile.write('\n')

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('', port))

        LOG.info(f'listening on port {port}')

        n_packets = 0

        # TODO: run this in a separate thread, and grant another thread the power to start and stop this loop
        # TODO: profile the performance of this loop
        # TODO: move this into a tick function
        while True:
            message, _ = server_socket.recvfrom(1024)
            fdp = ForzaDataPacket(message, packet_format = packet_format)
            tick_time = dt.datetime.now()
            if log_wall_clock:
                fdp.wall_clock = tick_time
            LOG.DEBUG(f'tick: {tick_time}')

            # TODO: refactor this if/else block
            if fdp.__getattribute__('is_race_on'):
                if n_packets == 0:
                    LOG.info(f'{dt.datetime.now()}: in race, logging data')

                if output_format == 'csv':
                    csv_writer.writerow(fdp.to_list(params))
                else:
                    outfile.write('\t'.join([f'{v}' for v in fdp.to_list(params)]) + '\n')

                n_packets += 1
                if n_packets % 60 == 0:
                    LOG.info(f'{dt.datetime.now()}: logged {n_packets} packets')
            else:
                if n_packets > 0:
                    LOG.info(f'{dt.datetime.now()}: out of race, stopped logging data')
                n_packets = 0


def main():
    LOG.info(f"Hanging out in my pants")
    args = cli_parser.get_arguments_from_cli()
    LOG.info(f"set args from CLI: {args}")
    dump_stream(args.port, args.output_filename, args.output_format, args.append,
                args.packet_format, args.log_level, args.config_file)
    LOG.info(f"DONE!")
    return()


if __name__ == "__main__":
    main()
