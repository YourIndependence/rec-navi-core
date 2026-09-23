# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Client Exceptions classes."""


class BaseClientExceptionError(Exception):
    """Base class for all Client custom_exceptions."""

    pass


class ClientIndexError(IndexError, BaseClientExceptionError):
    """Custom IndexError for Client."""

    pass


class ClientNameError(NameError, BaseClientExceptionError):
    """Custom NameError for Client."""

    pass


class ClientOSError(OSError, BaseClientExceptionError):
    """Custom OSError for Client."""

    pass


class ClientRuntimeError(RuntimeError, BaseClientExceptionError):
    """Custom RuntimeError for Client."""

    pass


class ClientResourcesNotFoundError(ClientRuntimeError):
    """Custom ResourcesNotFoundError for Client."""

    pass


class ClientTypeError(TypeError, BaseClientExceptionError):
    """Custom TypeError for Client."""

    pass


class ClientValueError(ValueError, BaseClientExceptionError):
    """Custom ValueError for Client."""

    pass


class ClientZeroDivisionError(ZeroDivisionError, BaseClientExceptionError):
    """Custom ZeroDivisionError for Client."""

    pass


class ClientFileExistsError(FileExistsError, BaseClientExceptionError):
    """Custom FileExistsError for Client."""

    pass


class ClientFileNotFoundError(FileNotFoundError, BaseClientExceptionError):
    """Custom FileNotFoundError for Client."""

    pass


class ClientPermissionError(PermissionError, BaseClientExceptionError):
    """Custom PermissionError for Client."""

    pass


class ClientKeyError(KeyError, BaseClientExceptionError):
    """Custom KeyError for Client."""

    pass


class ClientAttributeError(AttributeError, BaseClientExceptionError):
    """Custom AttributeError for Client."""

    pass


class ToolCallingError(RuntimeError, BaseClientExceptionError):
    """Custom RuntimeError for toolCalling."""

    pass


class WellKnownError(BaseClientExceptionError):
    """Custom RuntimeError for WellKnownError."""

    pass


class ClientAuthorizationError(BaseClientExceptionError):
    """User authorization/permission error (403 Forbidden)."""

    pass


class ClientNotFoundError(BaseClientExceptionError):
    """Resource not found error (404 Not Found)."""

    pass


class ClientConflictError(BaseClientExceptionError):
    """Conflict error for optimistic locking failure (409 Conflict)."""

    pass


class ClientPayloadTooLargeError(BaseClientExceptionError):
    """Payload too large error (413 Payload Too Large)."""

    def __init__(self, message: str = "Payload too large") -> None:
        super().__init__(message)
        self.status_code = 413


class ClientUnprocessableEntityError(BaseClientExceptionError):
    """Unprocessable entity error (422 Unprocessable Entity)."""

    def __init__(self, message: str = "Unprocessable entity") -> None:
        super().__init__(message)
        self.status_code = 422
