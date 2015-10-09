"""OpenDeep Dataset Implementation for LibriSpeech Corpus"""
import logging, os
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
    DEV_CLEAN: '337MB',
    DEV_OTHER: '314MB',
    TEST_CLEAN: '346MB',
    TEST_OTHER: '328MB',
    TRAIN_CLEAN_100:'6.3GB',
    TRAIN_CLEAN_360:'23GB',
    TRAIN_OTHER_500:'30GB',
    INTRO_DISCLAIMERS: '695MB',
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
        without_extension = final_filename[:-7]
        if not os.path.exists( without_extension ):
            if not os.path.exists( final_filename ):
                final_url = base_url + filename
                log.info("Need to download %s (%s)", final_url,filesize )
                file_ops.download_file(
                    final_url,
                    final_filename,
                )

def download_everything():
    ensure_downloads( ALL_FILES )
    

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    download_everything()
