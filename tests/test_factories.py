import pytest
from pyclf.lda.classification import ToeplitzLDA
from sklearn.pipeline import Pipeline

from auditory_aphasia.factories import (calibration_data_provider_factory,
                                        classification_pipeline_factory)
from auditory_aphasia.logging.logger import get_logger


def test_classification_factory():
    mandatory_kwargs = {
        'n_channels': 5
    }

    clf_pipeline = classification_pipeline_factory("ToeplitzLDAPipeline", **mandatory_kwargs)

    assert isinstance(clf_pipeline, Pipeline)
    assert clf_pipeline.steps[0][1].n_channels == 5
    assert isinstance(clf_pipeline.steps[0][1], ToeplitzLDA)

    with pytest.raises(ValueError):
        classification_pipeline_factory("OtherPL", **mandatory_kwargs)

def test_calibration_data_provider_factory():

    kwargs = {
        'logger': get_logger(),
        'n_sessions': 5,
        'data_dir': 'data_dir',
        'subject_code': 'subject_code',
        'channel_labels_online': ['ch1', 'ch2'],
        'file_name_prefix': 'prefix',
        'filter_freq': [1, 20],
        'filter_order': 5,
        'markers_to_epoch': [1, 2],
        'tmin': -1,
        'tmax': 3,
    }

    # this currently requires psychopy (double check if this is really necessary!!!)
    calibration_data_provider = calibration_data_provider_factory("CalibrationDataProvider" , **kwargs)

    with pytest.raises(ValueError):
        calibration_data_provider_factory("OtherCDP", **kwargs)
