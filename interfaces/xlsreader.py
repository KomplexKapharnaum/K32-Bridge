import os
import xlrd

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

#
# XLS Read and Parse
#
class XlsParser():
    def __init__(self, path, sheet, parent=None):
        self.path = path
        self.sheet = sheet
        self.parent = None
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = self.workbook.sheet_by_index(sheet)
        self.bank(1)
        print(f"-- XLS: file loaded {path}")

        self.observer = Observer()
        self.observer.schedule( XlsHandler(self), path='/Users/mat/Desktop/K32-Bridge/', recursive=False)
        self.observer.start()

    def bank(self, b):
        self.offset = max(1, 16*(b)+1)

    def note2txt(self, noteabs, octave):
        value = None

        if octave >= 0:
            # C1 = 24 // C2 = 36
            colx = octave 
            rowx = self.offset + noteabs + 1
            if rowx in range(self.worksheet.nrows):
                value = self.worksheet.cell_value( rowx, colx )
            # print('Parser:', value, rowx, colx)
        return value

    def reload(self):
        self.workbook.release_resources()
        self.workbook = xlrd.open_workbook(self.path)
        self.worksheet = self.workbook.sheet_by_index(self.sheet)

    
#
# XLS Watchdog handler
#
class XlsHandler(FileSystemEventHandler):
    def __init__(self, parser):
        super().__init__()
        self.parser = parser

    def on_modified(self, event):
        if os.path.basename(event.src_path) == 'MidiMapping.xls':
            print('-- XLS: MidiMapping.xls modified')
            if self.parser.parent:
                self.parser.parent.clear()
            self.parser.reload()