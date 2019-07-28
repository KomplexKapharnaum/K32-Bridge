import os
import xlrd

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#
# XLS Read and Parse
#
class XlsParser():
    def __init__(self, path, parent=None):
        self.path = path
        self.parent = parent
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = [self.workbook.sheet_by_index(0), self.workbook.sheet_by_index(1)]

        self.offset = [0,0]
        self.bank(0,1)
        self.bank(1,1)
        print(f"-- XLS: file loaded {path}")

        self.handler = XlsHandler(self)
        self.observer = Observer()

        # self.observer.schedule( self.handler, path='/Users/mat/Desktop/K32-Bridge/', recursive=False)
        self.observer.schedule( self.handler, path='./', recursive=False)
        self.observer.start()

    def bank(self, ws, b):
        self.offset[ws] = max(1, 16*(b)+1)

    def note2txt(self, sheet, noteabs, octave):
        value = None

        if octave >= 0:
            # C1 = 24 // C2 = 36
            colx = octave 
            rowx = self.offset[sheet] + noteabs + 1
            if rowx in range(self.worksheet[sheet].nrows):
                value = self.worksheet[sheet].cell_value( rowx, colx )
            # print('Parser:', value, rowx, colx)
        return value

    def reload(self):
        self.workbook.release_resources()
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = [self.workbook.sheet_by_index(0), self.workbook.sheet_by_index(1)]

    
#
# XLS Watchdog handler
#
class XlsHandler(FileSystemEventHandler):
    def __init__(self, parser):
        super().__init__()
        self.parser = parser

    def on_modified(self, event):
        if os.path.basename(event.src_path) == self.parser.path:
            print(f'-- XLS: {self.parser.path} modified')
            if self.parser.parent:
                self.parser.parent.clear()
            self.parser.reload()