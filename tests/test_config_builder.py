
from auditory_aphasia.config_builder import (ClassifierConfig, GeneralConfig,
                                             SystemConfig,
                                             build_classifier_config,
                                             build_general_config,
                                             build_system_config)


# just test that the initialization works
def test_build_general_config():
    general_config = build_general_config()
    assert isinstance(general_config, GeneralConfig)

def test_build_system_config():
    system_config = build_system_config()
    assert isinstance(system_config, SystemConfig)

def test_build_classifier_config():
    classifier_config = build_classifier_config()
    assert isinstance(classifier_config, ClassifierConfig)
