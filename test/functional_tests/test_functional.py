#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import shutil
import tempfile
from os import path, remove
from unittest import skip

import pandas as pd

import pysmscmon
from pysmscmon import smscmon as smsc
from pysmscmon.sshtunnels.sftpsession import SftpSession

from .base import *


class TestMain(TestWithTempConfig):
    """ Set of test functions for interactive (ssh) methods of __init__.py """

    def test_start(self):
        """ Test function for main() and start() """

        self.conf.set('DEFAULT', 'folder', MY_DIR)

        # start() needs a file with the settings, and the files linked in that
        # settings file may be relative to the settings file location, so
        # work in a temporary directory
        with tempfile.NamedTemporaryFile() as temp_config:
            self.conf.write(temp_config)
            temp_config.seek(0)
            self.container.settings_file = temp_config.name
            self.container.check_files()

            pysmscmon.start(alldays=True,
                            loglevel='DEBUG',
                            settings_file=temp_config.name,
                            threads=True)

        # Returns nothing if non-existing or bad settings file
        with tempfile.NamedTemporaryFile() as temp_config:
            self.conf.write(temp_config)
            temp_config.seek(0)
            self.container.settings_file = temp_config.name
            self.container.check_files()
            # calc, graph and template are not in the same folder as settings
            self.assertIsNone(pysmscmon.start(settings_file=temp_config.name))


class TestSmscMon(TestWithSsh):
    """ Set of test functions for interactive (ssh) methods of smscmon.py """
    def test_inittunnels(self):
        """ Test function for init_tunnels """
        monitor = smsc.SMSCMonitor(settings_file=TEST_CONFIG, logger=LOGGER)
        monitor.conf.set('DEFAULT', 'folder', MY_DIR)
        monitor.init_tunnels()
        # before start, tunnel should not be started
        self.assertFalse(monitor.server.is_started)
        # Stopping it should not do any harm
        self.assertIsNone(monitor.stop_server())
        # Start and check tunnel ports
        self.assertIsNone(monitor.start_server())  # starting should be silent
        self.assertTrue(monitor.server.is_started)
        self.assertIsInstance(monitor.server.tunnel_is_up, dict)
        for port in monitor.server.tunnel_is_up:
            self.assertTrue(monitor.server.tunnel_is_up[port])
        monitor.stop_server()

    def test_getstatsfromhost(self):
        """ Test function for get_stats_from_host """
        test_system_id = 'System_1'
        monitor = smsc.SMSCMonitor(settings_file=TEST_CONFIG, logger=LOGGER)
        monitor.init_tunnels()
        monitor.start_server()
        monitor.conf.set('DEFAULT', 'folder', MY_DIR)
        with SftpSession(
            hostname='127.0.0.1',
            ssh_port=monitor.server.tunnelports[test_system_id]
                         ) as s:
            data = monitor.get_stats_from_host(
                monitor.conf.get(test_system_id, 'ip_or_hostname'),
                ['.csv'],
                sftp_session=s,
                logger=LOGGER,
                files_folder=monitor.conf.get(test_system_id, 'folder')
                                                )

            should_be_empty_data = monitor.get_stats_from_host(
                monitor.conf.get(test_system_id, 'ip_or_hostname'),
                ['i_do_not_exist'],
                sftp_session=s,
                logger=LOGGER,
                files_folder=monitor.conf.get(test_system_id, 'folder')
                                                )

        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertTrue(should_be_empty_data.empty)
        monitor.stop_server()

    def test_getsysdata(self):
        """ Test function for get_system_data """
        test_system_id = 'System_1'
        with smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                              logger=LOGGER) as monitor:
            monitor.alldays = True  # Ignore timestamp on test data
            monitor.conf.set('DEFAULT', 'folder', MY_DIR)
            with SftpSession(
                hostname='127.0.0.1',
                ssh_port=monitor.server.tunnelports[test_system_id],
                logger=LOGGER
                             ) as s:
                data = monitor.get_system_data(system=test_system_id,
                                               session=s)
                # When the folder does not exist it should return empty df
                monitor.conf.set('DEFAULT', 'folder', 'do-not-exist')
                self.assertTrue(monitor.get_system_data(system=test_system_id,
                                                        session=s).empty)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)

    def test_getsyslogs(self):
        """ Test function for get_system_logs """
        test_system_id = 'System_1'
        with smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                              logger=LOGGER) as monitor:
            with SftpSession(
                hostname='127.0.0.1',
                ssh_port=monitor.server.tunnelports[test_system_id],
                logger=LOGGER
                             ) as s:
                logs = monitor.get_system_logs(ssh_session=s.ssh_transport,
                                               system=test_system_id,
                                               log_cmd='netstat -nrt')
                self.assertIn('0.0.0.0', ''.join(logs))
                logs = monitor.get_system_logs(ssh_session=s.get_channel(),
                                               system=test_system_id)
                self.assertIsNone(logs)

    def test_collectsysdata(self):
        """ Test function for collect_system_data """
        with smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                              logger=LOGGER) as monitor:
            monitor.alldays = True  # Ignore timestamp on test data
            monitor.nologs = True  # Skip log collection
            (data, logs) = monitor.collect_system_data(system='System_1')
            self.assertIsInstance(data, pd.DataFrame)
            self.assertTrue(data.empty)  # sftp folder was not set
            self.assertIn('Log collection omitted', logs)
            monitor.nologs = False
            monitor.conf.set('DEFAULT', 'folder', MY_DIR)
            monitor.conf.set('MISC', 'smsc_log_cmd', 'netstat -nrt')
            (data, logs) = monitor.collect_system_data(system='System_1')
            self.assertFalse(data.empty)
            self.assertNotIn('Log collection omitted', logs)

    def test_serialmain(self):
        """ Test function for main_no_threads (serial mode) """
        monitor = smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                                   logger=LOGGER,
                                   alldays=True,
                                   nologs=True)
        monitor.conf.set('DEFAULT', 'folder', MY_DIR)
        all_systems = [item for item in monitor.conf.sections()
                       if item not in ['GATEWAY', 'MISC']]
        monitor.main_no_threads(all_systems)
        self.assertIsInstance(monitor.data, pd.DataFrame)
        self.assertFalse(monitor.data.empty)
        self.assertIsInstance(monitor.logs, dict)

    def test_threadedmain(self):
        """ Test function for main_threads (threaded mode) """
        monitor = smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                                   logger=LOGGER,
                                   alldays=True,
                                   nologs=True)
        monitor.conf.set('DEFAULT', 'folder', MY_DIR)
        all_systems = [item for item in monitor.conf.sections()
                       if item not in ['GATEWAY', 'MISC']]
        monitor.main_threads(all_systems)
        self.assertIsInstance(monitor.data, pd.DataFrame)
        self.assertFalse(monitor.data.empty)
        self.assertIsInstance(monitor.logs, dict)

    def test_main(self):
        """ Test function for main """
        monitor = smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                                   logger=LOGGER,
                                   alldays=True,
                                   nologs=True)
        monitor.main()
        # main reads by itself the config file, where the folder is not set
        # thus won't find the files and return an empty dataframe
        self.assertIsInstance(monitor.data, pd.DataFrame)
        self.assertTrue(monitor.data.empty)
        self.assertIsInstance(monitor.logs, dict)

        # Same by calling the threaded version
        monitor = smsc.SMSCMonitor(settings_file=TEST_CONFIG,
                                   logger=LOGGER,
                                   alldays=True,
                                   nologs=True)
        monitor.main(threads=True)
        self.assertIsInstance(monitor.data, pd.DataFrame)
        self.assertTrue(monitor.data.empty)
        self.assertIsInstance(monitor.logs, dict)