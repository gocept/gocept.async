# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

import ZODB.POSException
import decorator
import logging
import lovely.remotetask.interfaces
import lovely.remotetask.processor
import persistent
import random
import rwproperty
import time
import transaction
import zope.authentication.interfaces
import zope.component
import zope.dottedname
import zope.security.management
import zope.site.hooks


log = logging.getLogger(__name__)


class TaskDescription(persistent.Persistent):

    site = None

    def __init__(self, f, args, kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.principal = self.get_principal()
        self.site = zope.site.hooks.getSite()

    @staticmethod
    def get_principal():
        interaction = zope.security.management.queryInteraction()
        if interaction is None:
            return
        for p in interaction.participations:
            return p.principal.id

    @rwproperty.getproperty
    def f(self):
        return zope.dottedname.resolve.resolve(self._f)

    @rwproperty.setproperty
    def f(self, f):
        if not f.__module__:
            raise ValueError("Cannot use function without module.")
        self._f = '%s.%s' % (f.__module__, f.__name__)


class AsyncFunction(object):

    zope.interface.implements(lovely.remotetask.interfaces.ITask)

    def __call__(self, service, jobid, input):
        log.info("Running async function %s" % jobid)
        retries = 0
        while True:
            try:
                old_site = zope.site.hooks.getSite()
                if input.site is not None:
                    zope.site.hooks.setSite(input.site)
                self.login(input.principal)
                input.f(*input.args, **input.kwargs)
                transaction.commit()
            except ZODB.POSException.ConflictError, e:
                log.warning("Conflict error during async task", exc_info=True)
                transaction.abort()
                retries += 1
                if retries >= 3:
                    break
                # Stagger retry:
                time.sleep(random.uniform(0, 2**(retries)))
            except Exception:
                log.error("Error during async function", exc_info=True)
                transaction.abort()
                break
            else:
                # Everything okay.
                break
            finally:
                zope.site.hooks.setSite(old_site)

    @staticmethod
    def login(principal):
        if principal is None:
            return
        interaction = zope.security.management.getInteraction()
        participation = interaction.participations[0]
        auth = zope.component.getUtility(
            zope.authentication.interfaces.IAuthentication)
        participation.setPrincipal(auth.getPrincipal(principal))


def is_async():
    interaction = zope.security.management.queryInteraction()
    if interaction is None:
        return False
    try:
        request = interaction.participations[0]
    except IndexError:
        return False
    return isinstance(
        request, lovely.remotetask.processor.ProcessorRequest)


def function(service=u''):

    def decorated(f, *args, **kwargs):
        tasks = zope.component.queryUtility(
            lovely.remotetask.interfaces.ITaskService, name=service)
        if tasks is None:
            log.warning('Cannot create asynchronous call to %s.%s because '
                        'TaskService %r could not be found.' % (
                            f.__module__, f.__name__, service))
        if tasks is None or is_async():
            return f(*args, **kwargs)
        desc = TaskDescription(f, args, kwargs)
        tasks.add(u'gocept.async.function', desc)

    return decorator.decorator(decorated)


