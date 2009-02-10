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
    >>> sm.registerUtility(
    ...     tasks, lovely.remotetask.interfaces.ITaskService, name='events')

When the decorated function is called it returns nothing:

>>> heavy_computing(2, 7)

When we start the processing of the task service, the function is called:

>>> gocept.async.tests.process()
Computing 2 + 7 = 9

[#cleanup]_

.. [#cleanup] ..
    >>> sm.registerUtility(
    ...     tasks, lovely.remotetask.interfaces.ITaskService, name='events')
