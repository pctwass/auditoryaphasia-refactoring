import datetime
import os
import traceback
import matplotlib
import mne
import numpy as np
import pylsl
import logging

from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from pyclf.lda.classification import EpochsVectorizer
from scipy import stats

matplotlib.use("tkagg")
import matplotlib.pyplot as plt
import pylsl

import src.config.config as config
import src.config.system_config as system_config
import src.config.classifier_config as classifier_config
import src.common.utils as utils
import src.common.LSL_streaming as streaming
import src.acquisition.epoch_container as epoch_container
import src.acquisition.OnlineDataAcquire as OnlineDataAcquire

from src.common.pandas_save_utility import PandasSaveUtility
from src.acquisition.acquisition_streaming_outlet_manager import AcquisitionStreamingOutletManager
from src.process_management.state_dictionaries import *
from src.process_management.process_communication_enums import *

logger = logging.getLogger(__name__)


class AcquisitionSystemController:

    def __init__(
        self,
        state_dict : dict[str,any],
        live_barplot_state_dict : dict[str,any],
        clf : Pipeline,
        markers : dict[str,int],
        tmin : float,
        tmax : float,
        baseline : str,
        filter_freq : enumerate[float],
        filter_order : int|float,
        ivals : enumerate[enumerate[float]],
        n_class : int,
        adaptation : bool = False,
        dynamic_stopping : bool = False,
        dynamic_stopping_params : dict[str,int|float] = None,
        max_n_stims : int = None,
    ):
        self.state_dict = state_dict
        self.live_barplot_state_dict = live_barplot_state_dict
        self.clf = clf
        self.markers = markers
        self.ivals = ivals
        self.adaptation = adaptation
        self.adaptation_available_new = False
        self.dynamic_stopping = dynamic_stopping
        self.dynamic_stopping_params = dynamic_stopping_params
        self.max_n_stims = max_n_stims
        self.n_class = n_class

        # below function sets: 
        # - self.eeg_stream
        # - self.eeg_inlet
        # - self.sampling_freq
        # - self.channel_names
        # - self.channels_to_acquire
        # - self.n_channels
        self._connect_LSL_acquisition_inlet()

        # TODO find a way to pass the number of features and classes so that the outlets can be initalized alongside the manager
        # NOTE at the moment the outlets are initialized the first time features or distances/classifications are pushed to them
        self.streaming_outlet_manager = AcquisitionStreamingOutletManager()

        self.incrementing_idx = 0  # index to track LSL packages, belonging to a single decoding set
        self.feature_outlet: pylsl.StreamOutlet | None = None
        self.distance_outlet: pylsl.StreamOutlet | None = None

        markers_to_epoch = markers['target'] + markers['nontarget']
        n_sessions = utils.get_n_sessions(system_config.data_dir, config.subject_code, system_config.datestr)
        
        self.epochs = epoch_container.EpochContainer(
            self.n_channels,
            self.sampling_freq,
            markers_to_epoch,
            tmin,
            tmax,
            baseline
        )

        formatting_client = system_config.FormattingClient()
        self.online_data_acquisitioner = OnlineDataAcquire.OnlineDataAcquire(
            self.epochs,
            self.eeg_inlet,
            self.marker_inlet,
            self.channels_to_acquire,
            self.n_channels,
            self.sampling_freq,
            formatting_client.eeg_format_convert,
            formatting_client.marker_format_convert,
            filter_freq=filter_freq,
            filter_order=filter_order,
            new_trial_markers=self.markers["new-trial"],
        )

        self.vectorizer = EpochsVectorizer(
            jumping_mean_ivals=self.ivals, sfreq=self.sampling_freq, t_ref=tmin
        )

        self.calibration_data_provider = system_config.CallibrationDataProviderClass(
            logger = logger,
            n_sessions = n_sessions,
            data_dir = system_config.data_dir,
            subject_code = config.subject_code,
            tmin = tmin,
            tmax = tmax,
            baseline = baseline,
            channel_labels_online = config.channel_labels_online,
            file_name_prefix = config.callibration_file_name_prefix,
            filter_freq = filter_freq,
            filter_order = filter_order,
            markers_to_epoch = markers_to_epoch
        )

    
    def _connect_LSL_acquisition_inlet(self):
        # ------------------------------------------------------------------------------------------------
        # find/connect eeg outlet

        logger.info("looking for an EEG stream...")
        
        self.eeg_stream, self.eeg_inlet = streaming.resolve_stream(
            system_config.eeg_acquisition_stream_name,
            system_config.eeg_acquisition_stream_type
        )

        self.sampling_freq = self.eeg_stream[0].nominal_srate()
        self.channel_names = streaming.get_LSL_channel_names(self.eeg_inlet)

        channel_indices_to_acquire = self._get_channel_indices_to_acquire()
        self.n_channels = len(channel_indices_to_acquire)
        logger.debug("number of channels (n_channels) for online session : %d" % self.n_channels)

        # ------------------------------------------------------------------------------------------------
        # find/connect marker outlet

        logger.info("looking for a marker stream...")
        self.marker_stream, self.marker_inlet = streaming.init_LSL_inlet(
            system_config.marker_acquisition_stream_name,
            system_config.marker_acquisition_stream_type,
            await_stream = True,
            timeout = system_config.marker_stream_await_timeout_ms
        )
        logger.info("Configuration Done.")


    def _get_channel_indices_to_acquire(self) -> list[int]:
        channel_indices_to_acquire = list()
        for idx, channel in enumerate(self.channel_names):
            if channel in config.channel_labels_online:
                channel_indices_to_acquire.append(idx)

        self.channels_to_acquire = np.array(channel_indices_to_acquire)
        logger.debug("ch_names_LSL : %s" % str(self.channel_names))
        logger.debug(
            "channels_to_acquire (idx) : %s" % str(channel_indices_to_acquire)
        )
        logger.debug(
            "channels_to_acquire : %s"
            % str(np.array(self.channel_names)[self.channels_to_acquire])
        )

        return channel_indices_to_acquire


    def fit_classifier(self, epochs):
        X = self.vectorizer.transform(epochs)

        events = epochs.events
        events = mne.merge_events(
            events,
            self.markers["target"],
            classifier_config.labels_binary_classification["target"],
        )
        events = mne.merge_events(
            events,
            self.markers["nontarget"],
            classifier_config.labels_binary_classification["nontarget"],
        )

        Y = events[:, -1]

        self.clf.fit(X, Y)


    def calibration(self, params:dict[str,any]):
        """
        Parameters
        =========
        """
        logger.info("start calibration")
        epochs = self.calibration_data_provider.get_calibration_data(params)
        epochs.load_data()
        self.fit_classifier(epochs)

        logger.info("classifier was calibrated.")

        
    def main(self):
        logger.info("Acquisition System Controller was started.")

        if self.adaptation:
            pandas_save_utility = self._prepare_panda_save_util_for_adaptation()

        labels = list()
        preds = list()

        self.live_barplot_state_dict["display_barplot"] = True
       
        if not os.path.exists(
            os.path.join(system_config.repository_dir_base, "media", "tmp")
        ):
            os.makedirs(
                os.path.join(system_config.repository_dir_base, "media", "tmp")
            )

        self.state_dict["acquire_trials"] = True
        self.online_data_acquisitioner.start()

        while self.state_dict["acquire_trials"] is True:
            try:
                new_trial_marker = self.online_data_acquisitioner.get_new_trial_marker()
                # logger.info(new_trial)
                if new_trial_marker is not None:
                    self.online_data_acquisitioner.clear_new_trial_marker()
                    self.state_dict["trial_completed"] = False
                    
                    trial_label = int(str(new_trial_marker + 1)[-1])
                    labels.append(trial_label)
                    logger.info("New Trial Started : %d" % trial_label)

                    clf_out = list()
                    for m in range(self.n_class):
                        clf_out.append(list())
                    clf_out_mean = list()
                    for m in range(self.n_class):
                        clf_out_mean.append(list())

                    distances = list()
                    stimulus_count = 0
                    dynamic_stopping_stim_num = self.dynamic_stopping_params[
                        "min_n_stims"
                    ]

                    barplot_colors = self._do_live_barplot_setup_for_new_trial(trial_label)

                if self.epochs.has_new_data():
                    # increment index to track LSL packages
                    self.incrementing_idx += 1

                    epoch, events = self.epochs.get_new_data()
                    if self.state_dict["trial_completed"]:
                        continue
                    
                    logger.info("New epochs was recorded.")
                    logger.debug("epoch.shape : %s" % str(epoch.shape))
                    logger.debug("events : %s" % str(events))

                    true_class_labels = np.empty(0)
                    for event in events:
                        if event in system_config.markers["target"]:
                            true_class_labels = np.append(
                                true_class_labels,
                                classifier_config.labels_binary_classification[
                                    "target"
                                ],
                            )
                        elif event in system_config.markers["nontarget"]:
                            true_class_labels = np.append(
                                true_class_labels,
                                classifier_config.labels_binary_classification[
                                    "nontarget"
                                ],
                            )
                        else:
                            raise ValueError("Unknown event")

                    vectorized_epoch = self.vectorizer.transform(epoch)
                    self.streaming_outlet_manager.push_features_to_lsl(vectorized_epoch, true_class_labels, self.incrementing_idx)

                    if classifier_config.adaptation:
                        # this function will calclate new set of w and b.
                        # And it's not overwritten yet. It will be overwritten after trial.
                        classifier_config.adaptation_clf.adaptation(
                            vectorized_epoch,
                            true_class_labels,
                            eta_cov=classifier_config.adaptation_eta_cov,
                            eta_mean=classifier_config.adaptation_eta_mean,
                        )
                        self.adaptation_available_new = True

                    classification_scores = self.clf.decision_function(vectorized_epoch)

                    stimulus_count += epoch.shape[0]
                    logger.info("stimulus count : %s" % str(stimulus_count))
                    logger.info("scores : %s" % str(classification_scores))

                    for index, event in enumerate(events):
                        event_number = int(str(event)[-1])
                        if classification_scores.ndim == 0:
                            distances.append([event_number, classification_scores])
                        else:
                            distances.append([event_number, classification_scores[index]])

                    logger.debug("distances : %s" % str(distances))
                    self.streaming_outlet_manager.push_distances_to_lsl(distances, self.incrementing_idx)

                    if (
                        system_config.show_live_classification_barplot
                        and stimulus_count >= self.n_class
                    ):
                        clf_out = self._get_distances_foreach_class(distances, self.n_class)
                        for index, clf_out_class in enumerate(clf_out):
                            # clf_out_mean[idx] = np.mean(clf_out_class)
                            self.live_barplot_state_dict["mean_classificaiton_values"][index] = np.mean(clf_out_class)

                    if (
                        self.dynamic_stopping is True
                        and self.state_dict["trial_completed"] is False
                    ):
                        if (stimulus_count >= self.dynamic_stopping_params["min_n_stims"]):
                            for stim_num in range(dynamic_stopping_stim_num, stimulus_count + 1):
                                clf_out = self._get_distances_foreach_class(
                                    distances, self.n_class, idx=stim_num - 1
                                )
                                logger.info("stim_num : %d" % stim_num)
                                logger.debug("clf_out : %s" % str(clf_out))

                                """
                                # for debugging
                                if stimulus_cnt >= 42:
                                    self.state_dict["trial_classification_status"] = TrialClassificationStatus.DECODED_EARLY # decoded by dynamic stopping
                                    self.state_dict["trial_label"] = 1
                                    self.state_dict["trial_stimulus_count"] = 42
                                    self.state_dict[""trial_completed"] = True
                                    self.state_dict["trial_completed"] = True
                                    break
                                """

                                for index, clf_out_class in enumerate(clf_out):
                                    clf_out_mean[index] = np.mean(clf_out_class)

                                logger.info(f"label trial (target) : {str(trial_label)}")
                                target_idx = trial_label - 1
                                target_distances = np.array(clf_out[target_idx])
                                logger.info(f"target_distances : {str(target_distances)}")

                                nontarget_clf_out_mean = clf_out_mean.copy()
                                nontarget_clf_out_mean.pop(target_idx)
                                nontarget_clf_out = clf_out.copy()
                                nontarget_clf_out.pop(target_idx)
                                logger.info(f"len(nontarget_clf_out) : {len(nontarget_clf_out)}")
                                logger.info(f"len(nontarget_clf_out_mean) : {len(nontarget_clf_out_mean)}")
                                logger.info(f"nontarget_distances : {str(nontarget_clf_out_mean)}")

                                best_nontarget_idx = np.argmax(nontarget_clf_out_mean)
                                best_nontarget_distances = np.array(nontarget_clf_out[best_nontarget_idx])
                                logger.info(f"best_nontarget_idx : {best_nontarget_idx}")
                                logger.info(f"best_nontarget_distances : {str(best_nontarget_distances)}")

                                # best_nontarget_idx =
                                # best_class_idx = np.argmax(clf_out_mean)

                                # rest_class_idx = list(range(len(clf_out_mean)))
                                # rest_class_idx.remove(best_class_idx)
                                # logger.debug("rest_class_idx : %s" %str(rest_class_idx))
                                # logger.debug("best_class_idx : %s" %str(best_class_idx))
                                # best_distances = np.array(clf_out[best_class_idx])
                                # rest_distances = np.empty(0)
                                # for idx in rest_class_idx:
                                #    rest_distances = np.append(rest_distances, np.array(clf_out[idx]))
                                logger.debug("clf_out : %s" % str(clf_out))
                                # logger.debug("rest_distances : %s" %str(rest_distances))
                                # logger.debug("best_distances : %s" %str(best_distances))

                                t_score, ttest_p_value = stats.ttest_ind(
                                    target_distances,
                                    best_nontarget_distances,
                                    equal_var=False,
                                    alternative="greater",
                                )
                                # equal_var : bool
                                # If True (default), perform a standard independent 2 sample test that assumes equal population variances. If False, perform Welch’s t-test, which does not assume equal population variance.
                                #
                                # alternative : {‘two-sided’, ‘less’, ‘greater’}
                                # - ‘two-sided’: the means of the distributions underlying the samples are unequal.
                                # - ‘less’: the mean of the distribution underlying the first sample is less than the mean of the distribution underlying the second sample.
                                # - ‘greater’: the mean of the distribution underlying the first sample is greater than the mean of the distribution underlying the second sample.
                                #
                                # Ref : https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html

                                # p = 0.01 # for debugging

                                logger.info("pvalue : %.4f" % ttest_p_value)

                                if ttest_p_value <= self.dynamic_stopping_params["pvalue"]:

                                    fig_feedback = plt.figure(num=2)
                                    plt.bar(
                                        config.words, clf_out_mean, color=barplot_colors
                                    )
                                    plt.tick_params(
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                    )
                                    fig_feedback.savefig(
                                        os.path.join(
                                            system_config.repository_dir_base,
                                            "media",
                                            "tmp",
                                            "fb_barplot.png",
                                        ),
                                        dpi=1000,
                                    )
                                    plt.close(fig_feedback)

                                    pred_trial = trial_label
                                    preds.append(pred_trial)
                                    logger.info("labels : %s" % str(labels))
                                    logger.info("preds : %s" % str(preds))
                                    logger.info(
                                        "n_stimulus : %d" % stimulus_count
                                    )
                                    acc = accuracy_score(labels, preds)
                                    logger.info("Acc : %.3f" % acc)
                                    self.state_dict["trial_classification_status"] = (
                                        TrialClassificationStatus.DECODED_EARLY  # decoded by dynamic stopping
                                    )
                                    self.state_dict["trial_label"] = trial_label
                                    self.state_dict["trial_stimulus_count"] = stimulus_count
                                    self.state_dict["trial_completed"] = True
                                    break
                            dynamic_stopping_stim_num = stimulus_count + 1

                    if (
                        stimulus_count == self.max_n_stims
                        and self.state_dict["trial_completed"] is False
                    ):
                        # without dynamic stopping
                        clf_out = self._get_distances_foreach_class(distances, self.n_class)
                        logger.debug("clf_out : %s" % str(clf_out))
                        for index, clf_out_class in enumerate(clf_out):
                            clf_out_mean[index] = np.mean(clf_out_class)
                        logger.debug("clf_out_mean : %s" % str(clf_out_mean))

                        self._plot_and_save_feedback_figure(clf_out_mean, barplot_colors)

                        pred_trial = np.argmax(clf_out_mean) + 1
                        preds.append(pred_trial)
                        acc = accuracy_score(labels, preds)
                        logger.info("labels : %s" % str(labels))
                        logger.info("preds : %s" % str(preds))
                        logger.info("Acc : %.3f" % acc)
                        if pred_trial == trial_label:
                            self.state_dict["trial_classification_status"] = TrialClassificationStatus.DECODED
                        else:
                            self.state_dict["trial_classification_status"] = TrialClassificationStatus.UNDECODED

                        self.state_dict["trial_label"] = trial_label
                        self.state_dict["trial_stimulus_count"] = stimulus_count
                        self.state_dict["trial_completed"] = True

                if self.state_dict["trial_completed"] and self.adaptation_available_new:
                    # overwrite w and b with new set.
                    classifier_config.adaptation_clf.apply_adaptation()
                    logger.info("classifier was updated.")
                    pandas_save_utility.add(
                        data=[
                            [
                                classifier_config.adaptation_clf.coef_,
                                classifier_config.adaptation_clf.intercept_,
                                classifier_config.adaptation_clf.cl_mean,
                                classifier_config.adaptation_clf.C_inv,
                                classifier_config.adaptation_clf.classes_,
                                datetime.datetime.now().strftime(
                                    "%y/%m/%d-%H:%M:%S"
                                ),
                            ]
                        ],
                        save_as_html=True,
                    )
                    self.adaptation_available_new = False

            # except Exception as e:
            #    self.acq.stop()
            #    logger.info("asc controller was stopped.")
            #    raise e.with_traceback(sys.exc_info()[2])
            # except KeyboardInterrupt as e:
            #    self.acq.stop()
            #    logger.info("asc controller was stopped.")
            #    raise e.with_traceback(sys.exc_info()[2])
            except:
                # tb = sys.exc_info()[2]
                # logger.info("Error : \n%s" %(tb.format_exc()))
                logger.error("Error : \n%s" % (traceback.format_exc()))
                # logger.info()
                # sys.exit()
                # logger.error(str(sys.exc_info()))
                # logger.info(sys.exc_info()[1])
                # logger.info("Error : " + sys.exc_info()[0])
        self.online_data_acquisitioner.stop()


    def _prepare_panda_save_util_for_adaptation() -> PandasSaveUtility:
        calibration_dir = os.path.join(
                system_config.data_dir,
                system_config.save_folder_name,
                "calibration",
            )
        
        if os.path.exists(calibration_dir) is False:
            os.mkdir(calibration_dir)

        columns = ["w", "b", "cl_mean", "Cov_inv", "classes", "time"]
        pandas_save_utility = PandasSaveUtility(
            file_path=os.path.join(calibration_dir, "calibration_log"), default_columns=columns
        )

        pandas_save_utility.add(
            data=[
                [
                    classifier_config.adaptation_clf.coef_,
                    classifier_config.adaptation_clf.intercept_,
                    classifier_config.adaptation_clf.cl_mean,
                    classifier_config.adaptation_clf.C_inv,
                    classifier_config.adaptation_clf.classes_,
                    datetime.datetime.now().strftime("%y/%m/%d-%H:%M:%S"),
                ]
            ],
            columns=columns,
            save_as_html=True,
        )

        return pandas_save_utility
    

    def _do_live_barplot_setup_for_new_trial(self, trial_label:int) -> list[str]:
        trial_label_index = trial_label - 1
        self.live_barplot_state_dict["index_best_class"] = trial_label_index
        barplot_colors = ["tab:blue" for m in range(self.n_class)]
        barplot_colors[trial_label_index] = "tab:green"
        for m in range(self.n_class):
            self.live_barplot_state_dict["mean_classificaiton_values"][m] = 0

        fb_barplot_path = os.path.join(
            system_config.repository_dir_base,
            "media",
            "tmp",
            "fb_barplot.png",
        )
        if os.path.exists(fb_barplot_path):
            os.remove(fb_barplot_path)

        return barplot_colors
    

    def _get_distances_foreach_class(distances:list[tuple[int,float]], n_class:int, idx:int=None) -> list[list[float]]:
        distances_foreach_class = [list() for m in range(n_class)]
        for idx_event, distance in enumerate(distances):
            event_num = distance[0]
            distances_foreach_class[event_num - 1].append(distance[1])
            if idx is not None and idx_event == idx:
                break
        return distances_foreach_class
    

    def _plot_and_save_feedback_figure(clf_out_mean:list[float], barplot_colors:list[str]):
        fig_feedback = plt.figure(num=2)
        plt.bar(
            config.words, clf_out_mean, color=barplot_colors
        )
        plt.tick_params(
            left=False,
            right=False,
            labelleft=False,
        )
        fig_feedback.savefig(
            os.path.join(
                system_config.repository_dir_base,
                "media",
                "tmp",
                "fb_barplot.png",
            ),
            dpi=1000,
        )
        plt.close(fig_feedback)


if __name__ == "__main__":
    print('Testing AcquisitionSystemController')
    classifier_factory = system_config.ClassificationPipelineClass(n_channels=classifier_config.n_channels)
    classifier = classifier_factory.get_model()

    testdict = dict(
        markers=system_config.markers,
        tmin=classifier_config.tmin,
        tmax=classifier_config.tmax,
        baseline=classifier_config.baseline,
        filter_freq=classifier_config.filter_freq,
        filter_order=classifier_config.filter_order,
        clf=classifier,
        ivals=classifier_config.ivals,
        n_class=classifier_config.n_class,
        adaptation=classifier_config.adaptation,
        dynamic_stopping=classifier_config.dynamic_stopping,
        dynamic_stopping_params=classifier_config.dynamic_stopping_params,
        max_n_stims=classifier_config.n_stimulus)
    
    for k,v in testdict.items():
        print(k, v)