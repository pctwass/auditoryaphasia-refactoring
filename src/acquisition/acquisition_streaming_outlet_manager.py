import numpy as np
import pylsl

# TODO once the number of features and classes can be passed by the AcquisitionSystemController, make these parameters requried and remove conditions to initalizing the outlets
# this includes initalizing them when they are None in the push_*_to_lsl() functions.
class AcquisitionStreamingOutletManager():
    def __init__(self, n_features : int = None, n_classes : int = None) -> None:
        if n_features is not None:
            self.init_feature_outlet()
        if n_classes is not None:
            self.init_distance_outlet()


    def push_features_to_lsl(self, vec : np.ndarray, y : np.ndarray, index : int):
        if self.feature_outlet is None:
            self.init_feature_outlet(vec.shape[1])

        self.feature_outlet.push_chunk(
            # this should get to a matrix with inc_idx in the first column and y labels in the last column
            np.hstack([[index] * len(vec), vec.T, y]).T
        )


    def push_distances_to_lsl(self, scores, index : int):
        if self.distance_outlet is None:
            self.init_distance_outlet(len(scores))

        # TODO: add info about the target / non-target, needs to understand the
        # `conf_system` variable and where it is coming from
        self.distance_function_outlet.push_sample(
            np.hstack([index, scores])
        )


    def init_feature_outlet(self, n_features: int):
        # create feature outlet
        feature_info = pylsl.StreamInfo(
            name="AphasiaFeature",
            type="EEG",
            channel_count=n_features + 2,  # +2 for inc_idx and the classification (y)
            nominal_srate=pylsl.IRREGULAR_RATE,
            channel_format=pylsl.cf_double64,
            source_id="feature_outlet",
        )
        self.feature_outlet = pylsl.StreamOutlet(feature_info)


    def init_distance_outlet(self, n_classes: int):
        # create distance outlet
        distance_info = pylsl.StreamInfo(
            name="AphasiaClassifierDistances",
            type="Classifier",
            channel_count=n_classes + 1,  # +1 for inc_idx
            nominal_srate=pylsl.IRREGULAR_RATE,
            channel_format=pylsl.cf_double64,
            source_id="distance_outlet",
        )
        self.distance_outlet = pylsl.StreamOutlet(distance_info)