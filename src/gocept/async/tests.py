# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

import cPickle
import gocept.async
import time
import lovely.remotetask
import lovely.remotetask.interfaces
import persistent
import pkg_resources
import transaction
import unittest
import zope.app.testing.functional
import zope.component
import zope.security.management


async_layer = zope.app.testing.functional.ZCMLLayer(
    pkg_resources.resource_filename(__name__, 'ftesting.zcml'),
    __name__, 'AsyncLayer', allow_teardown=True)


computings = []

@gocept.async.function(service=u'events')
def compute_something(a, b=None):
    computings.append((a,b))


class DataObject(persistent.Persistent):
    pass



def process():
    # Start asynchronous processing in a new thread.
    transaction.commit()
    tasks = zope.component.getUtility(
        lovely.remotetask.interfaces.ITaskService, name='events')
    tasks.processorArguments = {'waitTime': 0.0}
    tasks.startProcessing()
    while tasks.hasJobsWaiting():
        time.sleep(0.1)
        transaction.abort()
    tasks.stopProcessing()
    transaction.commit()
    time.sleep(0.02)


class AsyncTest(zope.app.testing.functional.BrowserTestCase):

    layer = async_layer

    def setUp(self):
        super(AsyncTest, self).setUp()
        self.setSite(self.getRootFolder())
        computings[:] = []
        self.sm = zope.component.getSiteManager()
        self.tasks = self.getRootFolder()['tasks'] = (
            lovely.remotetask.TaskService())
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


class TestAsyncFunction(unittest.TestCase):

    def test_login(self):
        self.fail()

    def test_no_login(self):
        self.fail()

    def test_conflict(self):
        self.fail()


class TestDecorator(AsyncTest):

    def test_reentrant(self):
        pass

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
        # The "computed" data object is another instnace therefore the lists
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

    def test_service_not_found(self):
        self.fail()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDecorator))
    suite.addTest(unittest.makeSuite(TestAsyncFunction))
    readme = zope.app.testing.functional.FunctionalDocFileSuite(
        'README.txt')
    readme.layer = async_layer
    readme.test_class = AsyncTest
    suite.addTest(readme)
    return suite
