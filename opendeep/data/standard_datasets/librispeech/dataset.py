"""OpenDeep Dataset Implementation for LibriSpeech Corpus

To pre-download:

    python -m opendeep.data.standard_datasets.librispeech.dataset

which will download a *very* large amount of data, 60GB+
and then unpack it to use 120+GB of disk space.

This dataset uses gstreamer's flac plugin to read the data-files.
"""
from __future__ import print_function
import logging, os, glob, shutil, tempfile, subprocess, sys
try:
    long 
except NameError:
    long = int
from . import DEFAULT_LIBRISPEECH_DATASET_PATH
from opendeep.utils import file_ops
log = logging.getLogger( __name__ )

HUMAN_URL = 'http://www.openslr.org/12/'
CITATION = '''LibriSpeech: an ASR corpus based on public domain audio books", 
Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015 (submitted)
http://www.danielpovey.com/files/2015_icassp_librispeech.pdf
'''
LICENSE = 'Public Domain'

BASE_URL = 'http://www.openslr.org/resources/12/'

DEV_CLEAN = 'dev-clean.tar.gz'
DEV_OTHER = 'dev-other.tar.gz'
TEST_CLEAN = 'test-clean.tar.gz'
TEST_OTHER = 'test-other.tar.gz'
TRAIN_CLEAN_100 = 'train-clean-100.tar.gz'
TRAIN_CLEAN_360 = 'train-clean-360.tar.gz'
TRAIN_OTHER_500 = 'train-other-500.tar.gz'

INTRO_DISCLAIMERS = 'intro-disclaimers.tar.gz'

FILE_SIZES = {
    DEV_CLEAN: 337926286,
    DEV_OTHER: 314305928,
    TEST_CLEAN: 346663984,
    TEST_OTHER: 328757843,
    TRAIN_CLEAN_100: 6387309499,
    TRAIN_CLEAN_360: 23049477885,
    TRAIN_OTHER_500: 30593501606,
    INTRO_DISCLAIMERS: 695964615,
}
DIRECTORY_NAMES = {
    INTRO_DISCLAIMERS: 'intro',
}
ALL_FILES = sorted(list(FILE_SIZES.keys()))

def ensure_downloads(files,base_url=BASE_URL,target_dir=DEFAULT_LIBRISPEECH_DATASET_PATH):
    """Ensure that all of the given files have been downloaded and/or unpacked"""
    log.info("Downloading librispeech to %s", target_dir )
    file_ops.mkdir_p( target_dir )
    for filename in files:
        final_filename = os.path.join( target_dir, filename )
        log.info("Ensuring download: %s", final_filename)
        filesize = FILE_SIZES.get( filename, 'Unknown Size')
        size_desc = file_ops.human_bytes(filesize) if isinstance(filesize,(long,int)) else filesize
        if filename in DIRECTORY_NAMES:
            without_extension = os.path.join( target_dir, DIRECTORY_NAMES[filename])
        else:
            without_extension = final_filename[:-7]
        
        if not os.path.exists( without_extension ):
            if (not os.path.exists( final_filename )) or not( os.stat(final_filename).st_size == filesize):
                final_url = base_url + filename
                log.info("Need to download %s (%s)", final_url,size_desc )
                if not file_ops.download_file(
                    final_url,
                    final_filename,
                ):
                    raise RuntimeError("Unable to download %s to %s"%(
                        final_url,final_filename,
                    ))
            working = tempfile.mkdtemp(dir=target_dir,prefix="unpack-",suffix="-tmp")
            try:
                file_ops.untar(final_filename, working)
                text_files = []
                for name in glob.glob(os.path.join(working,'LibriSpeech','*')):
                    if os.path.basename( name ) == os.path.basename(without_extension):
                        os.rename( name, without_extension )
                    elif os.path.splitext(name)[1].upper() == '.TXT':
                        text_files.append( name )
                    else:
                        log.warn("Unexpected directory in %s: %r",final_filename, name)
                for text_file in text_files:
                    os.rename( text_file, os.path.join( without_extension, os.path.basename(text_file)))
                if not os.path.exists( without_extension ):
                    raise RuntimeError(
                        "Unable to find the directory %s expected from %s"%(
                            without_extension,
                            final_filename,
                        )
                    )
            finally:
                shutil.rmtree( working )

class FlacReader( object ):
    """Reader for a Flac-encoded data-file"""
    def __init__(self, filename ):
        """Read a Flac-encoded file into memory as a numpy array"""
        self.filename = os.path.normpath( filename )
    _audio_array = None
    def audio_array(self):
        import numpy as np
        if self._audio_array is None:
            pipe = subprocess.Popen([
                'gst-launch',
                    '-q',
                    'filesrc','location=%s'%(self.filename,),'!',
                    'flacdec','!',
                    'audiorate','!',
                    'audioconvert','!',
                    # for gstreamer 1.0 this should be audio/x-raw likely...
                    'audio/x-raw-int,width=16,channels=1,format=U16LE','!',
                    'fdsink', 'fd=1',
            ], stdout=subprocess.PIPE)
            converted,_ = pipe.communicate()
            self.audio_array = np.fromstring(
                converted,
                dtype='<H',
            )
        return self.audio_array

def download_everything():
    ensure_downloads( ALL_FILES )

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    #download_everything()
    f = FlacReader( sys.argv[1] )
    audio = f.audio_array()
    print(audio)
