import os


def human_size(length: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    radix = 1024.0
    for i in range(len(units)):
        if (length / radix) < 1:
            return "%.2f%s" % (length, units[i])
        length = length / radix


class Record:
    SPLIT = '|||'

    def __init__(self, f:str='record.log') -> None:
        self.f=f

    def log(self, *info: str):
        """Append :param:`info` to the `self.f`."""
        with open(self.f, 'a', encoding='utf-8') as f:
            f.write(f'{Record.SPLIT.join(info)}\n')

    def all(self):
        """Get all records."""
        if not os.path.isfile(self.f):
            return []
        with open(self.f, 'r', encoding='utf-8') as f:
            return [i.strip().split(Record.SPLIT) for i in f.readlines()]

    def delete(self):
        """Delete records file."""
        if os.path.isfile(self.f):
            os.remove(self.f)

    def last(self, n: int = 1):
        """
        Read the last of :param:`n` records from FILE

        Ref
        -------------------
        https://www.cnblogs.com/liushaohui/p/9712687.html
        """
        def to_str(rs: list[bytes]) -> list[list[str]]:
            return [r.decode().strip().split(Record.SPLIT) for r in rs]
        if not os.path.isfile(self.f):
            return []
        with open(self.f, 'rb') as f:
            offset = -1
            while True:
                try:
                    f.seek(offset, 2)
                except OSError:
                    f.seek(0, 0)
                    return to_str(f.readlines()[-n:])
                lines = f.readlines()
                if len(lines) >= n+1:
                    return to_str(lines[-n:])
                offset *= 2
