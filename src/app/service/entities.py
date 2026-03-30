import os
import uuid
from collections import namedtuple
from app import config

ExecuteResult = namedtuple('ExecuteResult', ('result', 'error'))


def opener(path, flags):
    return os.open(path, flags, mode=0o777)


class CSharpFile:

    """ Описывает файлы, необходимые для запуска программы """

    def __init__(self, code: str):
        file_id = uuid.uuid4()
        self.filepath_csharp = os.path.join(
            config.SANDBOX_DIR, f'{file_id}.cs'
        )
        self.filepath_out = os.path.join(
            config.SANDBOX_DIR, f'{file_id}.out'
        )
        with open(self.filepath_csharp, 'w') as file:
            file.write(code)
        with open(self.filepath_out, 'w', opener=opener) as _:
            pass

    def remove(self):
        try:
            os.remove(self.filepath_csharp)
            os.remove(self.filepath_out)
        except:
            pass