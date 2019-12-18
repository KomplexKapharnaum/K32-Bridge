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

        print(f"-- XLS: file loaded {path}")

        self.handler = XlsHandler(self)
        self.observer = Observer()

        # self.observer.schedule( self.handler, path='/Users/mat/Desktop/K32-Bridge/', recursive=False)
        self.observer.schedule( self.handler, path='./', recursive=False)
        self.observer.start()

    def getCell(self, sheet, colx, rowx):
        value = None
        if sheet == -1:
            sheet = len(self.workbook.sheet_names())-1  # last sheet
        if (colx >= 0): 
            if sheet >= 0 and sheet < len(self.workbook.sheet_names()):
                if rowx in range(self.worksheet[sheet].nrows):
                    value = self.worksheet[sheet].cell_value( rowx, colx )
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