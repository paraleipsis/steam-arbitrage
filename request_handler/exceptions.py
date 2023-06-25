class TooManyRequestsError(Exception):
    def __init__(
            self,
            message='Client has sent too many requests in a given amount of time ("rate limiting")',
            *args,
            **kwargs):
        super().__init__(message)
