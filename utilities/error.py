class CustomApiResponseError(Exception):
    def __init__(self, data, status):
        self.data = data
        self.status = status
