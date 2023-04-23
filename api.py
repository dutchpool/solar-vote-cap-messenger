class Pagination(object):
    def __init__(self, first_uri: str, next_uri: str = None, result: [] = None):
        if result is None:
            result = []
        self.first_uri = first_uri
        self.next_uri = next_uri
        self.result = result

    def to_next(self, next_uri: str, result: []):
        return Pagination(self.first_uri, next_uri, self.to_result(result))

    def to_result(self, result: []):
        self.result.extend(result)
        return self.result

    def get_uri(self, *args):
        if self.next_uri is None:
            return self.first_uri.format(*args)
        else:
            return self.next_uri
