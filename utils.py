import os


class Util(object):

    FILE_FLAGS = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    def __init__(self):
        self.dir_list = ["logs", "CodeGenerator/media", "CodeGenerator/staticfiles", "CodeGenerator/static"]
        self.file_list = ["logs/logfile.txt"]

    def run(self):
        for _dir in self.dir_list:
            if not os.path.exists(_dir):
                os.makedirs(_dir)
        for file in self.file_list:
            if not os.path.exists(file):
                os.open(file, self.FILE_FLAGS)
