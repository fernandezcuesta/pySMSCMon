#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
*t4mon* - T4 monitoring **test functions** for gen_plot.py
"""
from __future__ import absolute_import

import pandas as pd
from matplotlib import pyplot as plt

from t4mon import df_tools, gen_plot

from .base import LOGGER, TEST_DATAFRAME, BaseTestClass


class TestGenPlot(BaseTestClass):

    """ Test functions for gen_plot.py """

    def test_tobase64(self):
        """ Test function for to_base64 """
        plot_fig = TEST_DATAFRAME.plot()
        self.assertIsInstance(gen_plot.to_base64(plot_fig), str)
        self.assertTrue(gen_plot.to_base64(plot_fig).
                        startswith('data:image/png;base64,'))
        # Converting an empty plot, should return an empty string
        self.assertEqual(gen_plot.to_base64(plt.figure().gca()), '')

    def test_plotvar(self):
        """ Test function for plot_var """
        dataframe = df_tools.consolidate_data(self.test_data, system='SYSTEM1')
        # make a plot filtering by system, uses dataframe.plot()
        myplot = gen_plot.plot_var(dataframe,
                                   'FRONTEND_11_OUTPUT_OK',
                                   system='SYSTEM1',
                                   logger=LOGGER)
        self.assertTrue(myplot.has_data())
        self.assertTrue(myplot.is_figure_set())

        # make a plot without filters, uses matplotlib.pyplot.plot()
        myplot = gen_plot.plot_var(dataframe,
                                   'FRONTEND_11_OUTPUT_OK',
                                   logger=LOGGER)
        self.assertTrue(myplot.has_data())
        self.assertTrue(myplot.is_figure_set())

        # Selecting a non exising system should return an empty plot
        voidplot = gen_plot.plot_var(dataframe,
                                     'FRONTEND_11_OUTPUT_OK',
                                     system='SYSTEM2',
                                     logger=LOGGER)
        self.assertFalse(voidplot.has_data())

        # now with an empty dataframe, should return None
        voidplot = gen_plot.plot_var(pd.DataFrame(),
                                     'DONTCARE',
                                     logger=LOGGER)
        self.assertFalse(voidplot.has_data())

        # same when trying to plot a non-existing variable
        voidplot = gen_plot.plot_var(dataframe,
                                     'DONTCARE',
                                     logger=LOGGER)
        self.assertFalse(voidplot.has_data())
