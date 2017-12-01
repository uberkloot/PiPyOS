'''
Initfs file format:


main table:
    int,int,int (3x4 bytes): offset of filename, offset of data, file size

names table:
    chars (null-terminated)
    
data:
    bytes (not terminated)

The main table also includes directory listings, these are automatically generated
These are identified by a file size of 0xffffffff

'''

import struct
import os


class InitFS:
    recordformat = 'III' # name offset, data offset, file size
    def __init__(self):
        
        self.clear()
    def clear(self):
        self.filetable = []
        self.data = b''
    def addfile(self, localfile, destfile):
        with open(localfile, 'rb') as file:
            data = file.read()
        self.filetable.append((destfile, len(self.data), len(data)))
        self.data+=data
        
    def tostring(self):
        # Add directory names
        
        
        filetable = self.filetable.copy()
        newdirs = { os.path.dirname(f[0]) for f in filetable }
        dirs = newdirs
        
        # Recursively find all parent dirs of all files
        while True:
            newdirs = { os.path.dirname(d) for d in newdirs }
            if not newdirs - dirs:
                break # No new dirs found
            dirs |= newdirs
        
        
        for dir in dirs:
            if dir == '/':
                # For consistency: no file or dir ends with /, including root
                dir = ''
            filetable.append((dir, 0, 0xffffffff))
            
        
        # Sort filetable to allow for proper directory listing:
        # For each directory, first the file, then subdir
        filetable.sort(key=lambda x: (os.path.dirname(x[0]), x[2]==0xffffffff, x[0]))
        
        print(filetable)
        
        # Calculate number of bytes required for main table (add 1 for 0,0,0 sentinel)
        maintablesize = (len(filetable) + 1) * struct.calcsize(self.recordformat)
        
        # Build name string table
        nameoffsets = []
        nametable = b''
        
        for filename, dataoffset, size in filetable:
            nameoffsets.append(len(nametable))
            nametable += filename.encode('ascii')+b'\x00'
            
        maintable = b''
        for (filename, dataoffset, size), nameoffset in zip(filetable, nameoffsets):
            maintable += struct.pack(self.recordformat, 
                                     nameoffset + maintablesize, 
                                     dataoffset + len(nametable) + maintablesize,
                                     size)
        
        maintable += struct.pack(self.recordformat, 0, 0, 0) # Add sentinel
        assert len(maintable) == maintablesize
        return maintable + nametable + self.data
        
        
fs = InitFS()


for file in [
    'encodings/__init__.py',
    'encodings/ascii.py',
    'encodings/aliases.py',
    'encodings/utf_8.py',
    'encodings/latin_1.py',
    'io.py',
    'abc.py',
    '_weakrefset.py',
    'site.py',
    '_sitebuiltins.py',
    'os.py',
    'stat.py',
    'genericpath.py', 
    '_collections_abc.py',

    'codecs.py']:
        fs.addfile('../deps/cpython/Lib/' + file, '/boot/' + file)

# 
fs.addfile('../lib/posixpath.py','/boot/posixpath.py') 
fs.addfile('../lib/sysconfig.py','/boot/sysconfig.py') 
fs.addfile('../python/_readline.py','/boot/_readline.py') 

# fs.addfile('../deps/cpython/Lib/encodings/ascii.py', '/boot/encodings/ascii.py')
# fs.addfile('../deps/cpython/Lib/encodings/ascii.py', '/boot/test.py')
# fs.addfile('../deps/cpython/Lib/codecs.py', '/boot/codecs.py')

with open('../initfs.bin', 'wb') as file:
    file.write(fs.tostring())


        
    