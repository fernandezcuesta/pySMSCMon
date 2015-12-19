#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
 T4Monitor: T4-compliant CSV processor and visualizer for OpenVMS
 -----------------------------------------------------------------------------
 2014-2015 (c) J.M. Fernández - fernandez.cuesta@gmail.com

 t4 input_file
 CSV file header may come in 2 different formats:

  ** Format 1: **
  The first four lines are header data:

  line0: Header information containing T4 revision info and system information

  line1: Collection date   (optional line)

  line2: Start time        (optional line)

  line3: Parameter Heading (comma separated)

 or

  ** Format 2: **

 line0: Header information containing T4 revision info and system information
 line1: <delim> START COLUMN HEADERS  <delim>  where <delim> is a triple `$`
 line2: parameter headings (comma separated)
 ...

  line 'n': <delim> END COLUMN HEADERS  <delim>  where <delim> is a triple `$`

  The remaining lines are the comma separated values. The first column is the
  sample time. Each line represents a sample, typically 60 seconds apart.
  However T4 incorrectly places an extra raw line with the column averages
  almost at the end of the file. That line will be considered as a closing
  hash and contents followed by it (sometimes even more samples...) is ignored

isort:skip_file
"""

from __future__ import print_function, absolute_import

import os
import sys

import matplotlib  # isort:skip
# Set matplotlib's backend before first import of pyplot or pylab,
# Qt4 doesn't like threads
if os.name == 'posix':
    matplotlib.use('Cairo')
else:
    matplotlib.use('TkAgg')
    import FileDialog  # Required by matplotlib when using TkAgg backend

from .collector import add_methods_to_pandas_dataframe, read_config
from .gen_plot import plot_var

from .orchestrator import Orchestrator
from .arguments_parser import (parse_arguments_local,
                               parse_arguments_main)


__version_info__ = (0, 11, 1)
__version__ = '.'.join(str(i) for i in __version_info__)
__author__ = 'fernandezjm'

__all__ = ('main',
           'dump_config')


def dump_config(output=None, **kwargs):
    """ Dump current configuration to screen, useful for creating a new
    settings.cfg file """
    conf = read_config()
    conf.write(output or sys.stdout)


def main():  # pragma: no cover
    arguments = parse_arguments_main(sys.argv[1:])
    if arguments.get('config', False):
        dump_config(**arguments)
        return
    if arguments.get('local', False):
        create_reports_from_local(sys.argv[1:],
                                  prog='{} --local'.format(sys.argv[0]))
        return
    if arguments.get('localcsv', False):
        create_reports_from_local(sys.argv[1:],
                                  prog='{} --localcsv'.format(sys.argv[0]),
                                  pkl=False)
        return
    _orchestrator = Orchestrator(**arguments)
    _orchestrator.start()


def create_reports_from_local(arguments, prog=None, pkl=True):  # pragma: no cover
    """ Create HTML reports from local stored data """
    arguments = parse_arguments_local(sys.argv[1:], prog=prog, pkl=pkl)
    _orchestrator = Orchestrator(**arguments)
    if pkl:
        _orchestrator.create_reports_from_local_pkl(arguments.pop('pkl_file'))
    else:
        _orchestrator.create_reports_from_local_csv(arguments.pop('csv_file'))
