"""Loader for NIST .sph files *as found in TEDLium dataset*

Header is a 1024-byte null padded textual format, rest is samples
in the format specified in the header.
"""
import logging
import numpy
import struct
log = logging.getLogger(__name__)
try:
    long
except NameError:
    long = int

MACHINE_LE = struct.pack("@i",1) == b'\x01\x00\x00\x00'

class SPHFile( object ):
    """Wrap up an SPHFile in a convenient format"""
    def __init__(self,filename):
        self.filename = filename
    def __str__(self):
        return '%s(%s)'%(self.__class__.__name__,self.filename)
    _byte_array = None
    _format = None
    @property
    def byte_array(self):
        if self._byte_array is None:
            self._byte_array = numpy.memmap( self.filename, dtype=numpy.uint8, mode='r')
        return self._byte_array
    @property
    def audio_array(self):
        """Get our audio array in its appropriate format"""
        dtype = ('>' if self.format['big_endian'] else '<') + 'H'
        return self.byte_array[1024:].view(dtype)
    @property
    def format(self):
        """Get our parsed format header"""
        if self._format is None:
            content = self.byte_array[:1024].tobytes()
            self._format = parse_sph_header(content)
        return self._format
    @property
    def needs_byteswap(self):
        """Do we need to byte-swap the array if we want to represent in native format?"""
        return self.format['big_endian'] == MACHINE_LE
    def audio_segment(self, start, stop):
        """Given floating-point start/stop offsets in seconds get audio data-slice"""
        rate = self.format['sample_rate']
        return self.audio_array[long(start*rate):long(stop*rate)+1]

def parse_sph_header( content ):
    """Read the file-format header for an sph file"""
    file_format = {
        # there are the sphere defaults, though the real content
        # isn't going to have this format, normally...
        'sample_rate':8000,
        'channel_count':1,
        'sample_byte_format': '01', # little-endian
        'sample_n_bytes':2,
        'sample_sig_bits': 16,
        'sample_coding': 'pcm',
    }
    end = 'end_head'
    for line in content.strip(b'\000').splitlines():
        if line.startswith(end):
            break
        for key in file_format.keys():
            if line.startswith(key):
                _, format, value = line.split(None, 3)
                if format == '-i':
                    value = int(value, 10)
                file_format[key] = value
    if file_format['sample_byte_format'] == '01':
        file_format['big_endian'] = False
    else:
        file_format['big_endian'] = True
    if MACHINE_LE:
        file_format['gst_format'] = 'U16LE'
    else:
        file_format['gst_format'] = 'U16BE'
    return file_format

def _parse_all_sphs( filepath ):
    """Trivial "does it crash" manual test operation

    This just confirms that all of the TED LIUM corpus can
    be format-parsed. It doesn't necessarily mean that the parsing
    is *correct*
    """
    import os
    count = 0
    for path,dirs,files in os.walk(filepath):
        sphs = [x for x in files if x.lower().endswith('.sph')]
        for sph in sphs:
            full_path = os.path.join(path,sph)
            handler = SPHFile(full_path)
            format = handler.format
            count += 1
            content = handler.byte_array[:1024].tobytes()
            assert format['sample_rate'] in (8000,16000), content
            assert format['sample_coding'] == 'pcm', format
            assert format['channel_count'] == 1, (sph,format)
            assert format['sample_n_bytes'] == 2, format
            log.info("%s format %s",full_path,format)
    log.info("Parsed format for %s files", count )

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    _parse_all_sphs( sys.argv[1] )
