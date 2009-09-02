# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

import zope.deferredimport

zope.deferredimport.define(
    function='gocept.async.task:function',
    is_async='gocept.async.task:is_async')
