import zipfile
from io import BytesIO


class InMemoryZip(object):
    def __init__(self):
        self.in_memory_zip = BytesIO()

    def append(self, filename_in_zip, file_contents):
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)
        zf.writestr(filename_in_zip, file_contents)
        for z_file in zf.filelist:
            z_file.create_system = 0

        return self

    def read(self):
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def write_to_file(self, filename):
        f = open(filename, "wb")
        f.write(self.read())
        f.close()
