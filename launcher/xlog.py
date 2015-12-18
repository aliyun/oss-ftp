import threading
import json

class LogFileTailer:
    def __init__(self, file_name):
        self.mFileName = file_name
        self.mLastPos = 0
        self.buffer_lock = threading.Lock()
        
    def get_lines(self, from_no):
        jd = {}
        self.buffer_lock.acquire()
        if from_no == 1:
            self.mLastPos = 0
        file = open(self.mFileName, 'r')
        file.seek(self.mLastPos, 0)
        for line in file:
            try:
                jd[from_no] = unicode(line, errors='replace')
            except:
                jd[from_no] = ""
            from_no += 1
        self.mLastPos = file.tell()
        self.buffer_lock.release()
        return json.dumps(jd, sort_keys=True)
