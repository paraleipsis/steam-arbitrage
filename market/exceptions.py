class NoSuchCurrency(Exception):
    def __init__(
            self,
            message='No such currency',
            *args,
            **kwargs):
        super().__init__(message)
