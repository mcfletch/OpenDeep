"""OpenDeep-specific DataSet API for the TEDLIUM corpus"""
import os
from opendeep.data.dataset import Dataset
from opendeep.utils import file_ops

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
def raw_audio( segments ):
    """Iterate over audio arrays of all segments"""
    for segment in segments:
        yield segment.audio_data
def transcripts( segments ):
    """Iterate over all transcripts of all segments"""
    for segment in segments:
        yield segment.transcript

def inputs_and_targets( speeches ):
    """Create input and target iterables from speeches"""
    inputs,targets = itertools.tee(all_segments(speeches))
    inputs,targets = raw_audio(inputs),transcripts(targets)
    return inputs,targets

class TEDLIUMDataSet(DataSet):
    """Provides the OpenDeep-specific DataSet objects"""
    def __init__(
        self,
        path='datasets/TEDLIUM_release2',
        window_duration = 0.01,
    ):
        if not os.path.exists(path):
            if os.path.exists(path+'.tar.gz'):
                # Note: this could, in theory overwrite anything on disk, as the Python
                # tarfile module doesn't prevent writing outside the root directory
                # (according to its docs).
                file_ops.untar(source_filename, destination_dir=os.path.dirname(path))
        if not os.path.exists(path):
            raise RuntimeError(
                "You need to download the TEDLIUM corpus (v2) from %(url)s and save it to %(path)s"%{
                    'url': LIUM_BASE + TEDLIUM_DOWNLOAD_URL,
                    'path': path+'.tar.gz',
                }
            )
        path = os.path.realpath(path)
        self.train_speeches = train_speeches = [
            tedlium.Speech( sph )
            for sph in file_ops.find_files(
                path, '.*[/]train[/]sph[/].*[.]sph',
            )
        ]
        self.test_speeches = test_speeches = [
            tedlium.Speech( sph )
            for sph in file_ops.find_files(
                path, '.*[/]test[/]sph[/].*[.]sph',
            )
        ]
        self.valid_speeches = valid_speeches = [
            tedlium.Speech( sph, window_duration=window_duration )
            for sph in file_ops.find_files(
                path, '.*[/]dev[/]sph[/].*[.]sph',
            )
        ]
        train_inputs,train_targets = inputs_and_targets( train_speeches )
        valid_inputs,valid_targets = inputs_and_targets( valid_speeches )
        test_inputs,test_targets = inputs_and_targets( test_speeches )
        super(TEDLIUMDataSet,self).__init__(
            path = path,
            train_inputs=train_inputs,train_targets=train_targets,
            valid_inputs=valid_inputs,valid_targets=valid_targets,
            test_inputs=test_inputs,test_targets=test_targets,
        )
