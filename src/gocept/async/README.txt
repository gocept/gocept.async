Details
+++++++

It is often desirable to process computations asynchronously. Until there was
`lovely.remotetask` this was not so easy to achieve in a Zope 3 application due
to transaction integration issues.

`gocept.async` makes the task even easier:

>>> import gocept.async
>>> @gocept.async.function(service='events')
... def heavy_computing(a, b):
...     print "Computing", a, "+", b, "=", a + b

The decorator ``gocept.async.function`` takes exactly one argument, the name of
a lovely.remotetask.interfaces.ITaskService utility. Note that `gocept.async`
does **not** define any task service by
itself[#test-task-service]_[#importable]_. 

.. [#importable] Note that the decorated function must have an importable
    module to be usable:

    >>> import gocept.async.tests
    >>> heavy_computing.undecorated.__module__ = 'gocept.async.tests'
    >>> gocept.async.tests.heavy_computing = heavy_computing

.. [#test-task-service] We defined task-service called ``events`` in
    this test:

    >>> import zope.component
    >>> import lovely.remotetask
    >>> import lovely.remotetask.interfaces
    >>> import lovely.remotetask.processor
    >>> sm = zope.component.getSiteManager()
    >>> getRootFolder()['tasks'] = tasks = lovely.remotetask.TaskService()
    >>> tasks.processorFactory = lovely.remotetask.processor.MultiProcessor
    >>> tasks.processorArguments = {'maxThreads': 1}
    >>> sm.registerUtility(
    ...     tasks, lovely.remotetask.interfaces.ITaskService, name='events')

When the decorated function is called it returns nothing:

>>> heavy_computing(2, 7)

When we start the processing of the task service, the function is called:

>>> gocept.async.tests.process()
Computing 2 + 7 = 9

When the function is called while a user is logged in, the function will be
called as that user[#proxy]_:

>>> @gocept.async.function('events')
... def who_am_i():
...     print gocept.async.task.TaskDescription.get_principal()
...
>>> who_am_i.undecorated.__module__ = 'gocept.async.tests'
>>> gocept.async.tests.who_am_i = who_am_i
>>> who_am_i()
>>> gocept.async.tests.process()

Now login:

>>> gocept.async.tests.login('zope.user')
>>> who_am_i()
>>> gocept.async.tests.process()
zope.user

>>> gocept.async.tests.logout()

.. [#proxy] Note that it might be necessary to manually create security proxies
    to enable security in the async function.


[#cleanup]_

.. [#cleanup] ..
    >>> sm.registerUtility(
    ...     tasks, lovely.remotetask.interfaces.ITaskService, name='events')
    >>> del gocept.async.tests.heavy_computing
    >>> del gocept.async.tests.who_am_i