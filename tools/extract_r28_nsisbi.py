#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Statically extract only the pinned official 0 A.D. R28 Windows payload.

No installer instructions are executed. Implements NSISBI 7405-1 fileform.h,
exehead/fileform.c (solid uint64 file lengths and CRC), and mtw/mtwdecompress.c
(u24 framed independent LZMA streams). Original tooling, GPL-2.0-or-later.
This is deliberately NOT a generic installer interpreter.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import struct
import time
import zlib

EXPECTED_SHA = '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1'
EXPECTED_BYTES = 1616727146
NSIS_OFFSET = 211456
VARIABLES = [str(i) for i in range(10)] + ['R'+str(i) for i in range(10)] + ['CMDLINE','INSTDIR','OUTDIR','EXEDIR','LANGUAGE','TEMP','PLUGINSDIR','EXEPATH','EXEFILE','HWNDPARENT','_CLICK','_OUTDIR']

def require(test, message):
    if not test:
        raise ValueError(message)

def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def decode_string(table, offset):
    require(0 <= offset*2 < len(table), 'String outside table')
    pos = offset*2
    output = ''
    while pos+2 <= len(table):
        unit = int.from_bytes(table[pos:pos+2], 'little'); pos += 2
        if not unit:
            return output
        if unit in (3,4):
            require(pos+2 <= len(table), 'Truncated encoded string')
            value = int.from_bytes(table[pos:pos+2], 'little'); pos += 2
            if unit == 4:
                output += chr(value)
            else:
                value = (value & 0x7f) | (((value >> 8) & 0x7f) << 7)
                require(value < len(VARIABLES), 'Unexpected installer variable')
                output += '$'+VARIABLES[value]
        else:
            require(unit >= 32, 'Unexpected control string')
            output += chr(unit)
    raise ValueError('Unterminated string')

class SolidStream:
    def __init__(self, source, compressed_end):
        self.source = source
        self.compressed_end = compressed_end
        self.buffer = b''
        self.pos = 0
        self.total = 0
        self.chunks = 0
        self.ended = False

    def refill(self):
        require(not self.ended, 'Unexpected end of solid stream')
        raw = self.source.read(3)
        require(len(raw)==3, 'Truncated chunk length')
        length = int.from_bytes(raw,'little')
        if not length:
            self.ended = True
            require(self.source.tell()==self.compressed_end, 'Chunk terminator not at declared end')
            return False
        require(5 < length <= 0xffffff and self.source.tell()+length <= self.compressed_end, 'Invalid chunk extent')
        data = self.source.read(length)
        require(len(data)==length,'Truncated chunk')
        prop = data[0]; lc=prop%9; lp=(prop//9)%5; pb=prop//45
        dictionary = int.from_bytes(data[1:5],'little')
        require(pb<=4 and lc+lp<=4 and 4096<=dictionary<=64*1024*1024,'Invalid LZMA properties')
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[dict(id=lzma.FILTER_LZMA1,dict_size=dictionary,lc=lc,lp=lp,pb=pb)])
        decoded = decoder.decompress(data[5:], max_length=8*1024*1024)
        require(decoder.eof and not decoder.unused_data, 'Invalid or oversized LZMA chunk')
        self.buffer = decoded
        self.chunks += 1
        self.total += len(decoded)
        return True

    def pieces(self, length):
        require(length>=0,'Negative stream read')
        while length:
            if not self.buffer:
                require(self.refill(), 'Unexpected solid terminator')
            take = min(length,len(self.buffer))
            block=self.buffer[:take]; self.buffer=self.buffer[take:]
            self.pos += take; length -= take
            yield block

    def read(self,length):
        require(length<=8*1024*1024,'Oversized memory read')
        return b''.join(self.pieces(length))

    def skip(self,length):
        for _ in self.pieces(length):
            pass

    def finish(self):
        self.skip(len(self.buffer))
        while not self.ended:
            if self.refill():
                self.skip(len(self.buffer))


def make_plan(header):
    blocks=[struct.unpack_from('<II',header,4+i*8) for i in range(7)]
    require(blocks==[(300,6),(684,1),(2756,779),(30800,0),(157330,28),(166346,0),(0,0)], 'Unexpected R28 compiled header layout')
    section=struct.unpack_from('<6i',header,684)
    require(section[3:5]==(434,247),'Unexpected game section')
    table=header[30800:157330]
    variables={'INSTDIR':'$INSTDIR','OUTDIR':'','_OUTDIR':''}
    def decode(offset):
        text=decode_string(table,offset)
        for name in ('_OUTDIR','OUTDIR'):
            text=text.replace('$'+name,variables[name])
        return text
    plan=[]
    for index in range(434,606):
        v=struct.unpack_from('<9i',header,2756+index*36)
        op=v[0]
        if op==11 and v[2]:
            variables['OUTDIR']=decode(v[1])
        elif op==27:
            require(v[1]==31 and v[3:5]==(0,0),'Unexpected path assignment')
            variables['_OUTDIR']=decode(v[2])
        elif op==20:
            name=decode(v[2])
            logical=variables['OUTDIR'].rstrip('\\')+'\\'+name
            require(logical.startswith('$INSTDIR\\'),'Non-install path')
            path=logical[len('$INSTDIR\\'):].replace('\\','/')
            path=PurePosixPath(path).as_posix()
            parts=PurePosixPath(path).parts
            require(parts and all(p not in ('','.','..') and not any(c in p for c in '$:') for p in parts),'Unsafe path')
            plan.append(dict(path=path,offset=(v[3]&0xffffffff)|((v[4]&0xffffffff)<<32),crc32=v[8]&0xffffffff,entry=index))
        else:
            raise ValueError('Unexpected opcode in file-only section: '+str(v))
    require(len({x['path'].lower() for x in plan})==len(plan),'Duplicate extraction paths')
    require([x['offset'] for x in plan]==sorted(x['offset'] for x in plan),'Unordered file offsets')
    return plan

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('installer',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    require(args.installer.stat().st_size==EXPECTED_BYTES,'Wrong installer size')
    require(digest_file(args.installer)==EXPECTED_SHA,'Wrong installer SHA256')
    require(not args.output.exists(),'Output must not exist; partial output is never reused')
    started=time.monotonic()
    with args.installer.open('rb') as source:
        source.seek(NSIS_OFFSET)
        first=struct.unpack('<II12sIIQ',source.read(36))
        require(first==(112,0xdeadbeef,b'NullsoftInst',166418,1616515690,4218030246),'Unexpected NSISBI firstheader')
        stream=SolidStream(source,EXPECTED_BYTES-8)
        require(int.from_bytes(stream.read(8),'little')==first[3],'Header length mismatch')
        header=stream.read(first[3]); plan=make_plan(header)
        args.output.mkdir(parents=True)
        data_base=stream.pos
        for item in plan:
            stream.skip(data_base+item['offset']-stream.pos)
            length_raw=stream.read(8); length=int.from_bytes(length_raw,'little')
            require(length<first[5] and data_base+item['offset']+8+length <= data_base+first[5],'File outside data block')
            destination=args.output/item['path']; destination.parent.mkdir(parents=True,exist_ok=True)
            sha=hashlib.sha256(); crc=0
            with destination.open('xb') as out:
                for block in stream.pieces(length):
                    out.write(block); sha.update(block); crc=zlib.crc32(block,crc)
            crc=zlib.crc32(length_raw,crc)&0xffffffff
            require(crc==item['crc32'],'File CRC mismatch: '+item['path'])
            item.update(bytes=length,sha256=sha.hexdigest(),crc_verified=True)
            print('Extracted',item['path'],length,flush=True)
        stream.finish()
        require(stream.pos==data_base+first[5], 'Solid stream total mismatch')
        header_crc, archive_crc=struct.unpack('<II',source.read(8))
        require(zlib.crc32(struct.pack('<Q',len(header)),zlib.crc32(header))&0xffffffff==header_crc,'Compiled header CRC mismatch')
        require(source.read(1)==b'','Trailing installer bytes')
        source.seek(512)
        stub=source.read(NSIS_OFFSET+36-512)
        require(zlib.crc32(struct.pack('<I',header_crc),zlib.crc32(stub))&0xffffffff==archive_crc, 'Installer stub CRC mismatch')
    report=dict(source_url='https://releases.wildfiregames.com/0ad-0.28.0-win64.exe',source_sha256=EXPECTED_SHA,source_bytes=EXPECTED_BYTES,nsisbi_source='https://sourceforge.net/projects/nsisbi/files/nsisbi3.09.1/nsis-code-7405-1-NSIS-trunk.zip/download',file_count=len(plan),files=plan,solid_chunks=stream.chunks,solid_uncompressed_bytes=stream.pos,all_file_crc_verified=True,header_crc_verified=True,installer_stub_crc_verified=True,installer_execution=False,elapsed_seconds=round(time.monotonic()-started,2))
    manifest=args.output.parent/(args.output.name+'-manifest.json')
    manifest.write_text(json.dumps(report,indent=2)+'\n')
    print('SUCCESS',len(plan),'files',stream.pos,'decoded bytes;',manifest,flush=True)

if __name__=='__main__':
    main()
