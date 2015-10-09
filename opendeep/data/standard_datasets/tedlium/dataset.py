"""OpenDeep-specific DataSet API for the TEDLIUM corpus"""
from __future__ import print_function
import os, logging, math
from opendeep.data.dataset import Dataset
from opendeep.utils import file_ops
from opendeep.data.standard_datasets.tedlium import DEFAULT_TEDLIUM_DATASET_PATH
from opendeep.data.standard_datasets.tedlium import tedlium

log = logging.getLogger(__name__)

LIUM_BASE = 'http://www-lium.univ-lemans.fr'
TEDLIUM_DOWNLOAD_URL = '/en/content/form-downloads?equipe=parole&projet=tedlium&fichier=TEDLIUM_release2.tar.gz'
# LIUM doesn't want to allow redistribution, so argh,
# every user needs to download all 40GB themselves
# It is trivial to script up the request to /logadd to pull
# the dataset, but I don't want to do so since LIUM
# seems to want everyone to go through their web site

def all_segments( speeches ):
    """Iterate over segments of all speeches"""
    for speech in speeches:
        for segment in speech:
            yield segment

def inputs_and_targets( speeches, skip_count=1 ):
    """Create input and target iterables from speeches"""
    return AudioStream(
        speeches, 
        skip_count=skip_count,
    ),TranscriptStream(
        speeches,
        skip_count=skip_count,
    )

class AudioStream(object):
    def __init__(self,speeches,skip_count=1):
        self.speeches = speeches
        self.skip_count = skip_count
    def __iter__(self):
        last = None
        for i,segment in enumerate(all_segments(self.speeches)):
            if not i%self.skip_count:
                for fragment in segment.audio_data.astype('f'):
                    yield fragment
            if last and segment.speech != last:
                log.info("Finished: %s", segment.speech.stm_file)
                last.sph_file.close()
            last = segment.speech

class TranscriptStream(object):
    def __init__(self,speeches,skip_count=1):
        self.speeches = speeches
        self.skip_count = skip_count
    def __iter__(self):
        for i,segment in enumerate(all_segments(self.speeches)):
            if not i%self.skip_count:
                yield segment.transcript


class TEDLIUMDataset(Dataset):
    """Provides the OpenDeep-specific DataSet objects"""
    def __init__(
        self,
        path=DEFAULT_TEDLIUM_DATASET_PATH,
        window_duration = 0.01,
        skip_count = 1,
        max_speeches = None,
    ):
        """Initialize the Dataset with a given storage for TEDLIUM
        
        path -- target path for the TED LIUM data storage
        window_duration -- duration of the audio window in seconds
        skip_count -- step size across the segments in the repo
                      used to do a very small subset of the dataset 
                      when doing testing iterations. This allows you
                      to test an "epoch" across a small subset of the 
                      40GB data-file
        """
        self.window_size = 2**int(math.ceil(math.log(int(window_duration * 16000),2)))
        source_filename = path + '.tar.gz'
        if not os.path.exists(path):
            if os.path.exists(source_filename):
                # Note: this could, in theory overwrite anything on disk, as the Python
                # tarfile module doesn't prevent writing outside the root directory
                # (according to its docs).
                file_ops.untar(source_filename, destination_dir=os.path.dirname(path))
        if not os.path.exists(path):
            raise RuntimeError(
                "You need to download the TEDLIUM corpus (v2) from %(url)s and save it to %(path)s"%{
                    'url': LIUM_BASE + TEDLIUM_DOWNLOAD_URL,
                    'path': source_filename,
                }
            )
        path = os.path.realpath(path)
        log.info("Searching for speeches")
        self.train_speeches = [
            tedlium.Speech( sph, window_size=self.window_size )
            for sph in file_ops.find_files(
                path, '.*[/]train[/]sph[/].*[.]sph',
            )
        ]
        if max_speeches:
            self.train_speeches = self.train_speeches[:max_speeches]
        self.test_speeches = [
            tedlium.Speech( sph, window_size=self.window_size )
            for sph in file_ops.find_files(
                path, '.*[/]test[/]sph[/].*[.]sph',
            )
        ]
        if max_speeches:
            self.test_speeches = self.test_speeches[:max_speeches]
        self.valid_speeches = [
            tedlium.Speech( sph, window_size=self.window_size )
            for sph in file_ops.find_files(
                path, '.*[/]dev[/]sph[/].*[.]sph',
            )
        ]
        if max_speeches:
            self.valid_speeches = self.valid_speeches[:max_speeches]
        log.info(
            "Creating speech segments (utterance records using 1/%s of the utterances)",
            skip_count,
        )
        train_inputs,train_targets = inputs_and_targets( self.train_speeches )
        valid_inputs,valid_targets = inputs_and_targets( self.valid_speeches )
        test_inputs,test_targets = inputs_and_targets( self.test_speeches )
        log.info("Initializing the OpenDeep dataset")
        super(TEDLIUMDataset,self).__init__(
            train_inputs=train_inputs,train_targets=train_targets,
            valid_inputs=valid_inputs,valid_targets=valid_targets,
            test_inputs=test_inputs,test_targets=test_targets,
        )

def test_minibatch():
    """Test that we get real minibatches across the dataset"""
    import numpy
    from opendeep.utils.batch import minibatch
    dataset = TEDLIUMDataset()
    inputs = dataset.train_inputs
    first = iter(minibatch( inputs, batch_size=128 )).next()
    assert isinstance(first, numpy.ndarray), first
    assert first.shape == (128,dataset.window_size), first.shape

def test_all_audio():
    """Test that we can iterate without having too many open files"""
    dataset = TEDLIUMDataset()
    for i,audio in enumerate(dataset.train_inputs):
        if not i%10000:
            print(i)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_all_audio()
    
