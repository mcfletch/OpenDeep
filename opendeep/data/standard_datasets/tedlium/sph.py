"""Loader for .sph files such as found in TEDLium dataset"""
import logging
import numpy
log = logging.getLogger(__name__)

def parse_sph_header( fh ):
    """Read the file-format header for an sph file"""
    file_format = {
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
    return file_format

def sph_audio_data( fh, header ):
    """Given header and a file handle, load the audio data in expected format
    
    Assumes the TED LIUM data-format is loosely followed, so
    if the file isn't quite correct we'll just error out.
    """
