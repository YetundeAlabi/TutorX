class InvalidToken(Exception):
    pass


class ExpiredTokenError(Exception):
    """
    ### Token has expired
    """
    pass


class EmptyAuthorizationHeader(Exception):
    """
    Raise if no authorization header is set
    """

