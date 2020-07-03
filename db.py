from uuid import uuid4
from json import dump, load
from json.decoder import JSONDecodeError
from os.path import isfile as exists


def gen_str():
    return uuid4().hex


class DB:
    def __init__(self, fn):
        self.fn = fn
        if exists(fn):
            with open(self.fn, 'r') as f:
                try:
                    self.db = load(f)
                except JSONDecodeError:
                    self.db = {}
        else:
            self.db = {}

        self.commit()

    def append(self, obj):
        id = gen_str()
        while id in self.db:
            id = gen_str()

        self.db[id] = obj
        self.commit()
        return id

    def __getitem__(self, item):
        return self.db[item]

    def delete(self, id):
        self.db.pop(id)
        self.commit()

    def commit(self):
        with open(self.fn, 'w') as f:
            dump(self.db, f)
