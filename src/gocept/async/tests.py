# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

from zope.testing import doctest
import StringIO
import ZODB.POSException
import cPickle
import gocept.async
import gocept.async.task
import logging
import lovely.remotetask
import lovely.remotetask.interfaces
import persistent
import pkg_resources
import time
import transaction
import unittest
import zope.app.testing.functional
import zope.component
import zope.publisher.browser
import zope.security.management
import zope.security.testing
import zope.site.testing


async_layer = zope.app.testing.functional.ZCMLLayer(
    pkg_resources.resource_filename(__name__, 'ftesting.zcml'),
    __name__, 'AsyncLayer', allow_teardown=True)


computings = []


class DataObject(persistent.Persistent):
    pass


def process(name='events'):
    # Start asynchronous processing in a new thread.
    transaction.commit()
    tasks = zope.component.getUtility(
        lovely.remotetask.interfaces.ITaskService, name=name)
    tasks.processorArguments['waitTime'] = 0
    last_job = tasks._queue[-1]
    tasks.startProcessing()
    try:
        while True:
            transaction.abort()
            if last_job.status == lovely.remotetask.interfaces.COMPLETED:
                break
            if last_job.status == lovely.remotetask.interfaces.ERROR:
                raise AssertionError("Task failed.")
            time.sleep(0.02)
    finally:
        tasks.stopProcessing()
        time.sleep(0.5)  # let the threads finish


def login(user):
    p = zope.security.testing.Principal(user)
    request = zope.publisher.browser.TestRequest()
    request.setPrincipal(p)
    zope.security.management.newInteraction(request)


def logout():
    zope.security.management.endInteraction()


class AsyncTest(zope.app.testing.functional.BrowserTestCase):

    layer = async_layer

    def setUp(self):
        super(AsyncTest, self).setUp()
        self.setSite(self.getRootFolder())
        computings[:] = []
        self.sm = zope.component.getSiteManager()
        self.tasks = self.getRootFolder()['tasks'] = (
            lovely.remotetask.TaskService())
        self.tasks.processorFactory = (
            lovely.remotetask.processor.MultiProcessor)
        self.tasks.processorArguments = {'maxThreads': 1}
        self.sm.registerUtility(
            self.tasks,
            lovely.remotetask.interfaces.ITaskService,
            name='events')

    def tearDown(self):
        self.sm.unregisterUtility(
            self.tasks,
            lovely.remotetask.interfaces.ITaskService,
            name='events')
        self.setSite(None)
        zope.security.management.endInteraction()
        super(AsyncTest, self).tearDown()



def raise_error(exception):
    computings.append(1)
    raise exception()


def increment_and_raise(obj):
    obj.count += 1
    raise ValueError(obj.count)


def increment(obj):
    obj.count += 1


class TestAsyncFunction(AsyncTest):

    def test_conflict_does_retry(self):
        desc = gocept.async.task.TaskDescription(
            raise_error, (ZODB.POSException.ConflictError,), {})
        self.tasks.add(u'gocept.async.function', desc)
        process()
        self.assertEquals([1, 1, 1], computings)

    def test_error_does_not_retry(self):
        desc = gocept.async.task.TaskDescription(
            raise_error, (ValueError,), {})
        self.tasks.add(u'gocept.async.function', desc)
        process()
        self.assertEquals([1], computings)

    def test_error_aborts(self):
        self.getRootFolder().count = 0
        desc = gocept.async.task.TaskDescription(
            increment_and_raise, (self.getRootFolder(),), {})
        self.tasks.add(u'gocept.async.function', desc)
        process()
        transaction.abort()  # abort to see changes
        self.assertEquals(0, self.getRootFolder().count)

    def test_no_error_commits(self):
        self.getRootFolder().count = 0
        desc = gocept.async.task.TaskDescription(
            increment, (self.getRootFolder(),), {})
        self.tasks.add(u'gocept.async.function', desc)
        process()
        transaction.abort()  # abort to see changes
        self.assertEquals(1, self.getRootFolder().count)



@gocept.async.function(service=u'events')
def compute_something(a, b=None):
    computings.append((a,b))


@gocept.async.function(service='does-not-exist')
def compute_now(a, b):
    computings.append((a,b))


class TestDecorator(AsyncTest):

    def test_simple(self):
        compute_something(5)
        self.assertEquals([], computings)
        process()
        self.assertEquals([(5, None)], computings)

    def test_persistent(self):
        data = self.getRootFolder()['data'] = DataObject()
        compute_something(5, data)
        self.assertEquals([], computings)
        process()
        # The "computed" data object is another instance therefore the lists
        # are not equal
        self.assertNotEquals([(5, data)], computings)
        # But the object has the same oid
        self.assertEquals(data._p_oid, computings[0][1]._p_oid)

    def test_unpickleable_fails(self):
        self.getRootFolder()['data'] = DataObject()
        data = zope.security.proxy.ProxyFactory(
            self.getRootFolder()['data'])
        compute_something(5, data)
        self.assertRaises(cPickle.UnpickleableError, process)

    def test_no_service_calls_synchronously(self):
        compute_now(4, 2)
        self.assertEquals([(4, 2)], computings)

    def test_no_service_logs_warning(self):
        logfile = StringIO.StringIO()
        log_handler = logging.StreamHandler(logfile)
        logging.root.addHandler(log_handler)
        old_log_level = logging.root.level
        logging.root.setLevel(logging.INFO)
        try:
            compute_now(6, 2)
            self.assertEquals(
                ("Cannot create asynchronous call to "
                 "gocept.async.tests.compute_now because TaskService "
                 "'does-not-exist' could not be found.\n"),
                logfile.getvalue())
        finally:
            logging.root.removeHandler(log_handler)
            logging.root.setLevel(old_log_level)


class LocalAuthenticationExample(object):

    zope.interface.implements(zope.authentication.interfaces.IAuthentication)

    def getPrincipal(self, id):
        return zope.security.testing.Principal(id)


task_result = None

@gocept.async.function('events')
def task_that_needs_site():
    global task_result
    task_result = 5


class TestSite(AsyncTest):

    def test_site_should_be_stored(self):
        root = self.getRootFolder()
        site = zope.site.folder.Folder()
        root['site'] = site
        site = root['site']
        zope.site.testing.createSiteManager(site)
        zope.site.hooks.setSite(site)
        site.getSiteManager().registerUtility(LocalAuthenticationExample())
        login('myuser')
        task_that_needs_site()
        process()
        self.assertEqual(5, task_result)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDecorator))
    suite.addTest(unittest.makeSuite(TestAsyncFunction))
    suite.addTest(unittest.makeSuite(TestSite))

    readme = zope.app.testing.functional.FunctionalDocFileSuite(
        'README.txt',
        optionflags=doctest.INTERPRET_FOOTNOTES)
    readme.layer = async_layer
    suite.addTest(readme)
    return suite
