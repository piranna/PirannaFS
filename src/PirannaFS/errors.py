"""Errors definitions

Error definitions "stolen" from the PyFilesystem project
"""


import sys


class FSError(Exception):
    """Base exception class for the FS module."""
    default_message = "Unspecified error"

    def __init__(self, msg=None, details=None):
        if msg is None:
            msg = self.default_message
        self.msg = msg
        self.details = details

    def __str__(self):
        keys = {}
        for k, v in self.__dict__.iteritems():
            if isinstance(v, unicode):
                v = v.encode(sys.getfilesystemencoding())
            keys[k] = v
        return str(self.msg % keys)

    def __unicode__(self):
        return unicode(self.msg) % self.__dict__

    def __reduce__(self):
        return (self.__class__, (), self.__dict__.copy(),)


class OperationFailedError(FSError):
    """Base exception class for errors associated with a specific operation."""
    default_message = "Unable to %(opname)s: unspecified error [%(errno)s - %(details)s]"

    def __init__(self, opname="", path=None, **kwds):
        self.opname = opname
        self.path = path
        self.errno = getattr(kwds.get("details", None), "errno", None)
        super(OperationFailedError, self).__init__(**kwds)

class ResourceError(FSError):
    """Base exception class for error associated with a specific resource."""
    default_message = "Unspecified resource error: %(path)s"

    def __init__(self, path="", **kwds):
        self.path = path
        self.opname = kwds.pop("opname", None)
        super(ResourceError, self).__init__(**kwds)


class ParentDirectoryMissingError(ResourceError):
    """Exception raised when a parent directory is missing."""
    default_message = "Parent directory is missing: %(path)s"

class ResourceInvalidError(ResourceError):
    """Exception raised when a resource is the wrong type."""
    default_message = "Resource is invalid: %(path)s"

class ResourceNotFoundError(ResourceError):
    """Exception raised when a required resource is not found."""
    default_message = "Resource not found: %(path)s"


class StorageSpace(OperationFailedError):
    """Exception raised when operations encounter storage space trouble."""
    default_message = "Unable to %(opname)s: insufficient storage space"