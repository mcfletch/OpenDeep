"""Loader for NIST .sph files *as found in TEDLium dataset*

Header is a 1024-byte null padded textual format, rest is samples
in the format specified in the header.
"""
import logging
import numpy
import struct
import math
log = logging.getLogger(__name__)
try:
    long
except NameError:
    long = int

MACHINE_LE = struct.pack("@i",1) == b'\x01\x00\x00\x00'

class SPHFile( object ):
    """Wrap up an SPHFile in a convenient format"""
    def __init__(self,filename,window_size=256):
        """Initialize with filename and audio window size (in samples)"""
        self.filename = filename
        self.window_size = window_size
    def __str__(self):
        return '%s(%s)'%(self.__class__.__name__,self.filename)
    _byte_array = None
    _format = None
    window_size=None
    @property
    def byte_array(self):
        """Get our raw byte array (uint8 type), which includes our header"""
        if self._byte_array is None:
            self._byte_array = numpy.memmap( self.filename, dtype=numpy.uint8, mode='r')
        return self._byte_array
    def close(self):
        if self._byte_array is not None:
            if hasattr( self._byte_array, '_mmap' ):
                self._byte_array._mmap.close()
            elif hasattr( self._byte_array, 'close' ):
                self._byte_array.close()
            del self._byte_array
    @property
    def audio_array(self):
        """Get our audio array in its appropriate format, with the header stripped"""
        dtype = ('>' if self.format['big_endian'] else '<') + 'H'
        return self.byte_array[1024:].view(dtype)
    @property
    def format(self):
        """Get our parsed format header (from the first 1024 bytes of the audio file)"""
        if self._format is None:
            content = self.byte_array[:1024].tobytes()
            self._format = parse_sph_header(content)
        return self._format
    @property
    def needs_byteswap(self):
        """Do we need to byte-swap the array if we want to represent in native format?

        This is only necessary if, for instance, we want to pass in a
        raw array to e.g. gstreamer, or we want to pass the data directly
        to Theano without doing an FFT first...
        """
        return self.format['big_endian'] == MACHINE_LE
    def audio_segment(self, start, stop):
        """Given floating-point start/stop offsets in seconds get audio data-slice

        This uses self.window_size to produce arrays that are a multiple of
        self.window_size whenever possible, which should be in all cases for TEDLIUM,
        but might not be the case if there a *very* short data file involved.

        TODO: this likely *isn't* the right way to produce the audio segments, it
        should be a sliding window across the arrays where we overlap considerably
        rather than having hard edges between the samples.
        """
        rate = self.format['sample_rate']
        length = int(math.ceil(((stop-start) * rate)/self.window_size)) * self.window_size
        start = long(start*rate)
        stop = start + length
        data = self.audio_array
        if stop >= data.shape[0]:
            stop = data.shape[0]
            start = stop-length
        return self.audio_array[start:stop].reshape((-1,self.window_size))

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
            assert format['sample_rate'] == 16000, content
            assert format['sample_coding'] == 'pcm', format
            assert format['channel_count'] == 1, (sph,format)
            assert format['sample_n_bytes'] == 2, format
            log.info("%s format %s",full_path,format)
    log.info("Parsed format for %s files", count )

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    _parse_all_sphs( sys.argv[1] )
