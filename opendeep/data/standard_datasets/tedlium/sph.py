"""Loader for NIST .sph files *as found in TEDLium dataset*

Header is a 1024-byte null padded textual format, rest is samples
in the format specified in the header.
"""
import logging
import numpy
log = logging.getLogger(__name__)

def parse_sph_header( fh ):
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
    for line in fh.read(1024).splitlines():
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
    return file_format

def load_audio_data( fh, format, force_native=False ):
    """Given format and a file handle, load the audio data in expected format
    
    Assumes the TED LIUM data-format is loosely followed, so
    if the file isn't quite correct we'll just error out.
    """
    fh.seek(1024)
    array = numpy.fromfile( fh, dtype = ('>' if format['big_endian'] else '<') + 'H' )
    if force_native:
        if not array.dtype.byteorder == '=':
            array.byteswap( True )
    return array

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
            source = open(os.path.join(path,sph))
            format = parse_sph_header( source )
            count += 1
            assert source.tell() == 1024, source.tell()
            source.seek(0)
            content = source.read(1024)
            assert format['sample_rate'] in (8000,16000), content
            assert format['sample_coding'] == 'pcm', format
            assert format['channel_count'] == 1, (sph,format)
            assert format['sample_n_bytes'] == 2, format
            #print(format)
            log.info("Loading audio for: %s",sph)
            array = load_audio_data( source, format )
            log.info("  %s samples loaded", len(array) )
    log.info("Parsed format for %s files", count )

if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    _parse_all_sphs( sys.argv[1] )
