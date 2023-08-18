"""Caching utilities."""

class FileManager:
    """
    Load file contents into memory as-needed.
    """
    def __init__(self):
        self.file_contents = dict()

    def get(self, path):
        try:
            return self.file_contents[path]
        except KeyError:
            with open(path, 'r') as f:
                contents = f.read()
            self.file_contents[path] = contents
            return self.file_contents[path]
