from sqlitedict import SqliteDict
from enum import Enum


class StorageModes(Enum):
    MEMORY = 1
    PERSISTENT = 2


class Storage:

    def __init__(self, mode=StorageModes.MEMORY):
        self.mode = mode
        if self.mode == StorageModes.PERSISTENT:
            self.cache = SqliteDict('../my_db.sqlite', autocommit=True)
        elif self.mode == StorageModes.MEMORY:
            self.cache = dict()

    def set(self, k, v):

        self.cache[k] = v
        if self.mode == StorageModes.PERSISTENT:
            # need to commit manually, as autocomit only commits with commit(blocking=False) and might not persist data
            self.cache.commit()

    def dump(self, k):
        self.cache.pop(k)
        if self.mode == StorageModes.PERSISTENT:
            # need to commit manually, as autocomit only commits with commit(blocking=False) and might not persist data
            self.cache.commit()

    def get(self, k):
        return self.cache.get(k)

    def append(self, k, v):
        current_data = self.cache.get(k)
        if not current_data:
            self.set(k, v)
        else:
            if not isinstance(current_data, list):
                current_data = [current_data]
            current_data.append(v)
            self.set(k, current_data)
