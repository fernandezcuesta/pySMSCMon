#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys
import logging
import argparse

import six

from .logger import DEFAULT_LOGLEVEL

__all__ = ('get_absolute_path',
           'parse_arguments_cli',
           'parse_arguments_local',
           'parse_arguments_main'
           )

TITLE = 'T4 collector and report generator script'

DESCRIPTION = """

Additional tools:
 --config: dump the configuration defaults
 --local: create reports from local data (typically under 'store/' folder)
 --localcsv: create reports from local CSV (typically under 'store/' folder)
"""

DEFAULT_SETTINGS_FILE = os.path.join(os.getcwd(), 'settings.cfg')
if not os.path.exists(DEFAULT_SETTINGS_FILE):
    DEFAULT_SETTINGS_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'conf',
        'settings.cfg'
    )


class ConfigReadError(Exception):

    """
    Exception subclass (dummy) raised while reading configuration file
    """
    pass


def get_input(text):
    return six.input(text)


def get_absolute_path(filename='', settings_file=None):
    """
    Get the absolute path if relative to the settings file location
    """
    if os.path.isabs(filename):
        return filename
    else:
        relative_path = os.path.dirname(
            os.path.abspath(settings_file or DEFAULT_SETTINGS_FILE)
        )
        return os.path.join(relative_path, filename)


def read_config(settings_file=None, **kwargs):
    """
    Return ConfigParser object from configuration file
    """
    config = six.moves.configparser.SafeConfigParser()
    try:
        settings_file = settings_file or DEFAULT_SETTINGS_FILE
        settings = config.read(settings_file)
    except six.moves.configparser.Error as _exc:
        raise ConfigReadError(repr(_exc))

    if not settings or not config.sections():
        raise ConfigReadError('Could not read configuration {0}!'
                              .format(settings_file))
    return config


def check_for_sysargs(parser, args=None):
    """
    Check if relevant parameters were specified or ask the user to proceed
    with defaults
    """
    # Default for collector is 'settings.cfg' in /conf
    if not args:
        # parser.parse_args(args)
        parser.print_help()
        six.print_('')
        while True:
            ans = get_input('No arguments were specified, continue with '
                            'defaults (check running with --config)? (y|[N]) ')
            if ans in ('y', 'Y'):
                six.print_('Proceeding with default settings')
                break
            elif not ans or ans in ('n', 'N'):
                sys.exit('Aborting')
            six.print_('Please enter y or n.')
    return vars(parser.parse_args(args))


def create_parser(args=None, prog=None):
    """
    Common parser parts for parse_arguments_local and parse_arguments_main
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.
                                     RawTextHelpFormatter,
                                     description=TITLE,
                                     add_help=False,
                                     prog=prog)
    parser.add_argument('--safe', action='store_true', dest='safe',
                        help='Serial mode, increasing execution time by 2x, '
                             'more stable under Windows environment')
    parser.add_argument(
        '--settings', dest='settings_file',
        default=DEFAULT_SETTINGS_FILE,
        help='Settings file (check defaults with --config)'
    )
    parser.add_argument('--loglevel', default=DEFAULT_LOGLEVEL,
                        choices=['DEBUG',
                                 'INFO',
                                 'WARNING',
                                 'ERROR',
                                 'CRITICAL'],
                        help='Debug level (default: {0})'
                        .format(logging.getLevelName(DEFAULT_LOGLEVEL)),
                        nargs='?')
    return parser


def parse_arguments_cli(args=None):
    """
    Parse arguments directly passed from CLI
    """
    parser = create_parser()
    parser.add_argument('--config', action='store_true',
                        help='Show current configuration')
    parser.add_argument('--local', action='store_true',
                        help='Render a report from local data')
    parser.add_argument('--localcsv', action='store_true',
                        help='Make a report from local CSV data')
    # Additional arguments passed to other parsers, ignored on this parser
    parser.add_argument('dummy', type=str, nargs='?',
                        help=argparse.SUPPRESS)
    parser.add_argument('--system', help=argparse.SUPPRESS)
    for null_argument in ['help', 'all', 'noreports', 'nologs']:
        parser.add_argument('--{0}'.format(null_argument),
                            action='store_true',
                            help=argparse.SUPPRESS)
    return check_for_sysargs(parser, args)


def parse_arguments_local(args=None, prog=None, pkl=True):
    """
    Argument parser for create_reports_from_local
    """
    parser = create_parser(prog=prog)
    parser.add_argument("-h", "--help",
                        action="help",
                        help="show this help message and exit")
    filetype = 'pkl' if pkl else 'csv'
    parser.add_argument('{0}_file'.format(filetype),
                        type=str,
                        metavar='input_{0}_file'.format(filetype),
                        help='Pickle (optionally gzipped) data file' if pkl
                        else 'Plain CSV file')
    parser.add_argument('--system',
                        type=str,
                        help='System for which generate the report. '
                             'Defaults to all')
    return check_for_sysargs(parser, args)


def parse_arguments_main(args=None):
    """
    Argument parser for main method
    """
    parser = create_parser()
    parser.description += DESCRIPTION
    parser.add_argument("-h", "--help",
                        action="help",
                        help="show this help message and exit")
    parser.add_argument('--all', action='store_true', dest='alldays',
                        help='Collect all data available on remote hosts'
                             'not just for today')
    parser.add_argument('--noreports', action='store_true',
                        help='Skip report creation, files are just gathered '
                             'and stored locally')
    parser.add_argument('--nologs', action='store_true',
                        help='Skip log collection from remote hosts')
    return check_for_sysargs(parser, args)