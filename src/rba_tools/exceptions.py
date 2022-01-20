# User-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass

class KrakenFileNotFoundError(Error):
    """Raised when the kraken file cannot be found"""
    pass