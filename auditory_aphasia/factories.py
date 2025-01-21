
def classification_pipeline_factory(pipeline_name: str, **kwargs):
    if pipeline_name == "ToeplitzLDAPipeline":

        from auditory_aphasia.classifier.toeplitz_LDA_pipeline import \
            get_toeplitz_LDA_pipeline

        return get_toeplitz_LDA_pipeline(**kwargs)
    else:
        raise ValueError(f"Unknown pipeline name: {pipeline_name}")


def calibration_data_provider_factory(provider_name: str, **kwargs):
    if provider_name == "CalibrationDataProvider":
        from auditory_aphasia.classifier.calibration_data_provider import \
            CalibrationDataProvider

        return CalibrationDataProvider(**kwargs)
    else:
        raise ValueError(f"Unknown provider name: {provider_name}")
