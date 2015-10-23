"""OpenDeep Dataset Implementation for CodeGolf Yes/No

To pre-download:

    python -m opendeep.data.standard_datasets.codegolfyesno.dataset

which will download a 95MB data-file. Unfortunately, that file is 
lzma (xz) compressed, so while it will unpack on Linux (likely Mac too)
or Python 3.x it won't properly unpack automatically on Windows with 2.7.

The dataset is composed of .wav files with 400 yes and 400 no 
utterances. There is a single speaker just with varied intonations
and the like, it is basically a "toy" dataset to get started with 
processing Audio and checking that we are getting real results
from a pipeline. There are no separate valid/train/test sets 
as the original data-set was actually a train-only set with a 
hidden test set.

All files are 16-bit LE encoded Wav files (according to documentation)
"""
from __future__ import print_function
import logging, os, sys, subprocess, math
try:
    long 
except NameError:
    long = int
from opendeep.data.dataset import Dataset
from opendeep.data.standard_datasets.codegolfyesno import DEFAULT_CODEGOLF_DATASET_PATH
from opendeep.utils import file_ops
import numpy
log = logging.getLogger( __name__ )
try:
    from scipy.io import wavfile
except ImportError:
    log.warn("Could not load the scipy.io.wavfile module to read the utterances")
    wavfile = None
    import wave

HUMAN_URL = 'https://github.com/vi/codegolf-jein'
CITATION = '''https://github.com/vi/codegolf-jein'''
# See http://codegolf.stackexchange.com/questions/37160/voice-recognition-yes-or-no
# where the (apparent) author posts the original question and declares the 
# samples "CC-0 (Public Domain)"
LICENSE = 'Public Domain'

TAR_FILE = 'codegolf-jein-train.tar.xz'
DATA_URL = 'http://vi-server.org/pub/%s'%(TAR_FILE,)
FILE_SIZE = 98689248 # Bytes

YES = 1.0
NO = 0.0

def ensure_downloads(url=DATA_URL,target_dir=DEFAULT_CODEGOLF_DATASET_PATH):
    """Ensure that all of the given files have been downloaded and/or unpacked"""
    file_ops.mkdir_p( target_dir )
    expected = os.path.join( target_dir, 'train','yes0.wav')
    if not os.path.exists( expected ):
        archive = os.path.join( target_dir, TAR_FILE )
        if not os.path.exists( archive ) or os.stat( archive ).st_size != FILE_SIZE:
            log.info("Downloading codegolf dataset to %s", target_dir )
            if not file_ops.download_file(
                DATA_URL,
                archive,
            ):
                raise RuntimeError( "Unable to download %s to %s"%(
                    DATA_URL,
                    archive,
                ))
        if sys.version_info.major == 3:
            log.info("Using Python 3.x lzma support to unpack")
            file_ops.untar(archive, target_dir, mode='r:xz')
        else:
            log.warn("Attempting decompresion/unpacking via tar command" )
            subprocess.check_call( ['tar', '-xJf', archive])
        if not os.path.exists( expected ):
            raise RuntimeError("Untarring the source file did not create %s"%(expected,))
    log.info("CodeGolf Yes/No dataset is installed in %s"%(target_dir,))
    return True

def read_wave( filename ):
    """Read a wave file into a numpy array
    
    TODO: Should be over in util.audio or something like that,
    along with the Flac, SPH and the like readers...
    """
    if wavfile:
        rate,data =  wavfile.read( filename )
        assert rate == 16000, rate
        return data
    else:
        fh = wave.open( filename, 'rb' )
        binary = fh.readframes(fh.getnframes())
        return numpy.fromstring( binary, '<H' )

class AudioSet( object ):
    def __init__(self, numbers, directory, window_size=256 ):
        self.numbers = numbers 
        self.directory = directory
    def friendly_data(self,data):
        data = data[:-(len(data)%self.window_size)]
        return data.reshape((-1,self.window_size))
    def __iter__(self):
        yes_template = os.path.join( self.directory, 'yes%s.wav' )
        no_template = os.path.join( self.directory, 'no%s.wav' )
        for number in self.numbers:
            yield self.friendly_data( read_wave( yes_template%number ) )
            yield self.friendly_data( read_wave( no_template%number ) )

class TargetSet( object ):
    def __init__(self,numbers):
        self.numbers = numbers 
    def __iter__(self):
        for number in self.numbers:
            yield YES
            yield NO

class CodeGolfDataset(Dataset):
    """Provides the OpenDeep-specific DataSet objects"""
    def __init__(
        self,
        path=DEFAULT_CODEGOLF_DATASET_PATH,
        url=DATA_URL,
        window_duration = 0.01,
        test_fraction = .2,
        valid_fraction = .05,
    ):
        """Initialize the Dataset with a given storage for TEDLIUM
        
        path -- target path for the TED LIUM data storage
        window_duration -- duration of the audio window in seconds
        test_fraction -- fraction of data-set to use for test 
        valid_fraction -- fraction of data-set to use for training validation
        """
        self.window_size = 2**int(math.ceil(math.log(int(window_duration * 16000),2)))
        ensure_downloads(url,path)
        path = os.path.realpath(path)
        
        numbers = list(range(1,401))
        valid = numbers[-int(400*valid_fraction):]
        numbers = numbers[:-len(valid)]
        test = numbers[-int(400*test_fraction):]
        numbers = numbers[:-len(test)]
        
        train_inputs = AudioSet( numbers, path, self.window_size )
        train_targets = TargetSet( numbers )
        
        valid_inputs = AudioSet( valid, path, self.window_size )
        valid_targets = TargetSet( valid )
        
        test_inputs = AudioSet( test, path, self.window_size )
        test_targets = TargetSet( test )
        
        log.info("Initializing the OpenDeep dataset %s train %s valid %s test",len(numbers),len(valid),len(test))
        super(CodeGolfDataset,self).__init__(
            train_inputs=train_inputs,train_targets=train_targets,
            valid_inputs=valid_inputs,valid_targets=valid_targets,
            test_inputs=test_inputs,test_targets=test_targets,
        )

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    ensure_downloads()
