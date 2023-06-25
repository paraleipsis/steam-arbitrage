class AccountAlreadyExists(Exception):
    def __init__(
            self,
            message='Account already exists',
            *args,
            **kwargs):
        super().__init__(message)


class AccountDoesNotExist(Exception):
    def __init__(
            self,
            message='Account does not exist',
            *args,
            **kwargs):
        super().__init__(message)
