#
# Helper imports:
#  This allows you to use the select.poll functionality 
#  ( http://docs.python.org/2/library/select.html#poll-objects )
#  While automatically using epoll if it's available.
#  .. Keep in mind to multiply the timeeout for poll.poll()
#     with  POLL_MOD
#

USES_POLL = USES_EPOLL = False
try:
    from select import epoll as poll, EPOLLIN as POLLIN, \
                       EPOLLOUT as POLLOUT, EPOLLERR as POLLERR, \
                       EPOLLHUP as POLLHUP, EPOLLPRI as POLLPRI
    POLL_MOD   = 1.0
    USES_EPOLL = True
except ImportError:
    try:
        from select import poll, POLLIN, POLLOUT, POLLERR, POLLHUP, POLLPRI
        POLL_MOD   = 1000.0
        USES_POLL  = True
    except ImportError:
        pass

from .adminconnection import AdminConnection

class AdminClient(AdminConnection):
    pass