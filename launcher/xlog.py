import threading
import json
import oss2
from oss2.compat import to_unicode, str

class LogFileTailer:
    def __init__(self, file_name):
        self.mFileName = file_name
        self.buffer_lock = threading.Lock()

    def get_lines(self, from_no, last_pos):
        lines = {}
        self.buffer_lock.acquire()
        file = open(self.mFileName, 'r')
        file.seek(last_pos, 0)
        for line in file:
            from_no += 1
            try:
                lines[from_no] = str(line)
            except:
                lines[from_no] = ""

        new_pos = file.tell()
        jd = {"filePos": new_pos, "fileLines": lines}
        self.buffer_lock.release()
        return json.dumps(jd, sort_keys=True)
