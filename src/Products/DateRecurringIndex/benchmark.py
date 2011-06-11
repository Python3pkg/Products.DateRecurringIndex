#!/usr/bin/env python

import cProfile
import pytz
import calendar
import unittest
from time import time
from datetime import datetime

from Testing import ZopeTestCase as ztc
from Zope2.App import zcml
from Products.Five import fiveconfigure


class _BenchTestResult(unittest._TextTestResult):
    """Custom TestResult class to display the time each method consumed."""

    def startTest(self, test):
        test.start = time()
        super(_BenchTestResult, self).startTest(test)
        self.stream.write("%s " % test._testMethodName)
        self.stream.flush()

    def stopTest(self, test):
        super(_BenchTestResult, self).stopTest(test)
        test.stop = time()
        self.stream.write(' (time: %s)\n' % (test.stop - test.start))


class BenchTestRunner(unittest.TextTestRunner):
    """Overrides the TextTestRunner class so we can add the time info."""

    def _makeResult(self):
        return _BenchTestResult(self.stream, self.descriptions, self.verbosity)


class Dummy(object):
    """Some dummy with a start, delta and until attributes to index."""

    def __init__(self, id, start, recurdef, until, recurrence_type):
        self.id = id
        self.start = start
        self.recurdef = recurdef
        self.until = until
        self.recurrence_type = recurrence_type


class BenchTestCase(ztc.ZopeTestCase):
    """Benchmark TestCase for DateIndex and DateRecurringIndex."""

    def setUp(self):
        super(BenchTestCase, self).setUp()

        fiveconfigure.debug_mode = True
        import Products.Five
        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('configure.zcml', Products.Five)
        fiveconfigure.debug_mode = False

        # Create indexes
        from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
        from Products.DateRecurringIndex.index import DateRecurringIndex
        self.di = DateIndex('di')
        self.dri_timedelta = DateRecurringIndex('dri',
                extra=Dummy(None, 'start', 'delta', 'until', 'timedelta'))
        self.dri_ical = DateRecurringIndex('dri',
                extra=Dummy(None, 'start', 'delta', 'until', 'ical'))

        # Creates 365 items to be indexed
        self.items = []
        tz = pytz.timezone('CET')
        for month, days in enumerate(calendar.mdays):
            for day in range(days):
                self.items.append(datetime(2010,month,day+1,0,0,0,0,tz))

    def _run_over_items(self, function, total, name):
        n = 0
        for x in range(total):
            for day in self.items:
               n += 1
               function(n, day)

    def benchCache(self):
        """Dummy test to cache the self.items list."""

    def benchDateIndex(self, total=1000):
        self._run_over_items(
                self.di.index_object,
                total,
                'benchDateIndex',
                )


    def benchDateRecurringIndex_timedelta(self, total=1000):
        self._run_over_items(
                self.dri_timedelta.index_object,
                total,
                'benchDateRecurringIndex_timedelta',
                )


    def benchDateRecurringIndex_ical(self, total=1000):
        self._run_over_items(
                self.dri_ical.index_object,
                total,
                'benchDateRecurringIndex_ical',
                )


class BenchTestCaseProfile(BenchTestCase):
    """
    """

    def _run_over_items(self, function, total, name):
        profiler = cProfile.Profile()
        n = 0
        for x in range(total):
            for day in self.items:
               n += 1
               profiler.runcall(function, n, day)
        profiler.dump_stats(name+'.profile')

def benchmark():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BenchTestCase, prefix='bench'))
    return suite

def benchmark_profile():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BenchTestCaseProfile, prefix='bench'))
    return suite

def run(self, *args):
    print 'Running benchmark ...'
    defaultTest = 'benchmark'
    if '--profile' in args:
        defaultTest = 'benchmark_profile'
    unittest.main(
        module='Products.DateRecurringIndex.benchmark',
        defaultTest=defaultTest, testRunner=BenchTestRunner,
        argv=['benchmark_DateRecurringIndex_vs_DateIndex'],
        )

