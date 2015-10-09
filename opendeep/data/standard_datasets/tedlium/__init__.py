"""Loader for the TEDLium dataset

Note that this dataset is *not* directly downloadable,
as it requires a registration step. It is *also* a
40GB dataset, which is a rather large download on
slow connections.
"""
import os
from .. import DEFAULT_DATASET_PATH
DEFAULT_TEDLIUM_DATASET_PATH = os.path.join(DEFAULT_DATASET_PATH,'TEDLIUM_release2')
