import datetime
import json
import os
import sys
import traceback
import matplotlib
import mne
import numpy as np
import pylsl
import logging

from multiprocessing import Array, Process
from pyclf.lda.classification import EpochsVectorizer
from scipy import stats
from sklearn.metrics import accuracy_score, get_scorer, roc_auc_score
from sklearn.model_selection import StratifiedKFold, permutation_test_score

matplotlib.use("tkagg")
import matplotlib.pyplot as plt
import pylsl

import config.conf as conf
import config.conf_system as conf_system
import config.temp_new_conf as temp_new_conf
import common.utils as utils
import fmt_converter
import src.LSL_streaming as streaming
import src.acquisition.container as container
import src.acquisition.OnlineDataAcquire as OnlineDataAcquire
import src.process_management.intermodule_communication as intermodule_comm

from src.classifier.ClassifierFactory import ClassifierFactory
from src.common.pandas_save_utility import PandasSaveUtility


#TODO: figure out alternative for starting live barplot process without ProcessManager circular import
# from src.process_management.process_manager import ProcessManager
from src.process_management.state_dictionaries import *
from src.process_management.process_communication_enums import *

logger = logging.getLogger(__name__)


def get_distances_class(distances, n_class, idx=None):
    distances_class = [list() for m in range(n_class)]
    for idx_event, distance in enumerate(distances):
        event_num = distance[0]
        distances_class[event_num - 1].append(distance[1])
        if idx is not None and idx_event == idx:
            break
    return distances_class


class AcquisitionSystemController:

    def __init__(
        self,
        markers,
        tmin,
        tmax,
        baseline,
        filter_freq,
        filter_order,
        clf,
        ivals,
        n_class,
        # ch_names=None,
        n_ch=None,
        fs=None,
        adaptation=False,
        dynamic_stopping=False,
        dynamic_stopping_params=None,
        max_n_stims=None,
        state_dict=None,
    ):

        self.markers = markers
        self.tmin = tmin
        self.tmax = tmax
        self.baseline = baseline
        self.filter_freq = filter_freq
        self.filter_order = filter_order
        self.clf = clf
        self.ivals = ivals
        self.n_ch = n_ch
        self.fs = fs
        self.adaptation = adaptation
        self.adaptation_available_new = False
        self.dynamic_stopping = dynamic_stopping
        self.dynamic_stopping_params = dynamic_stopping_params
        self.max_n_stims = max_n_stims
        self.n_class = n_class

        self.state_dict = state_dict

        self.ch_names = None
        self.channels_to_acquire = None
        self.epochs = None
        self.acq = None
        self.vectorizer = None

    def init(self):

        self.epochs = container.Epochs(
            self.n_ch,
            self.fs,
            self.markers["target"] + self.markers["nontarget"],
            self.tmin,
            self.tmax,
            self.baseline,
            ch_names=self.ch_names,
            ch_types="eeg",
        )

        self.acq = OnlineDataAcquire.OnlineDataAcquire(
            self.epochs,
            self.eeg_inlet,
            self.channels_to_acquire,
            self.n_ch,
            self.fs,
            self.marker_inlet,
            self.filter_freq,
            self.filter_order,
            fmt_converter.eeg_format_convert,
            fmt_converter.marker_format_convert,
            new_trial_markers=self.markers["new-trial"],
        )

        self.vectorizer = EpochsVectorizer(
            jumping_mean_ivals=self.ivals, sfreq=self.fs, t_ref=self.tmin
        )

        self.inc_idx = 0  # index to track LSL packages, belonging to a single decoding set
        # single decoding task
        self.feature_outlet: pylsl.StreamOutlet | None = None
        self.distance_outlet: pylsl.StreamOutlet | None = None

    def push_features_to_lsl(self, vec: np.ndarray, y: np.ndarray):
        if self.feature_outlet is None:
            self.init_feature_outlet(vec.shape[1])

        self.feature_outlet.push_chunk(
            # this should get to a matrix with inc_idx in the first column and y labels in the last column
            np.hstack([[self.inc_idx] * len(vec), vec.T, y]).T
        )

    def push_distances_to_lsl(self, scores):
        if self.distance_outlet is None:
            self.init_distance_outlet(len(scores))

        # TODO: add info about the target / non-target, needs to understand the
        # `conf_system` variable and where it is coming from
        self.distance_function_outlet.push_sample(
            np.hstack([self.inc_idx, scores])
        )

    def init_feature_outlet(self, n_features: int):
        # create feature outlet
        feature_info = pylsl.StreamInfo(
            name="AphasiaFeature",
            type="EEG",
            channel_count=n_features + 2,  # +2 for inc_idx and y
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

    def fit_classifier(self, epochs):
        X = self.vectorizer.transform(epochs)

        events = epochs.events
        events = mne.merge_events(
            events,
            self.markers["target"],
            conf_system.labels_binary_classification["target"],
        )
        events = mne.merge_events(
            events,
            self.markers["nontarget"],
            conf_system.labels_binary_classification["nontarget"],
        )

        Y = events[:, -1]

        self.clf.fit(X, Y)

    def calibration(self, params):
        """
        Prameters
        =========
        """
        logger.info("start calibration")
        epochs = conf_system.get_calibration_data(params)
        epochs.load_data()
        self.fit_classifier(epochs)

        logger.info("classifier was calibrated.")

    def connect_LSL(self, ENABLE_STREAM_INLET_RECOVER=True):
        # ------------------------------------------------------------------------------------------------
        # find/connect eeg outlet

        logger.info("looking for an EEG stream...")
        
        self.eeg_stream, self.eeg_inlet = streaming.resolve_stream(
            temp_new_conf.eeg_acquisition_stream_name,
            temp_new_conf.eeg_acquisition_stream_type
        )

        # self.n_ch = self.eeg_stream[0].channel_count()
        # self.n_ch = fmt_converter.n_ch_convert(self.n_ch)
        self.fs = self.eeg_stream[0].nominal_srate()
        self.ch_names = utils.get_channel_names_LSL(self.eeg_inlet)

        channels_to_acquire = list()
        for idx, ch in enumerate(self.ch_names):
            if ch in conf.channel_labels_online:
                channels_to_acquire.append(idx)
        self.channels_to_acquire = np.array(channels_to_acquire)
        logger.debug("ch_names_LSL : %s" % str(self.ch_names))
        logger.debug(
            "channels_to_acquire (idx) : %s" % str(channels_to_acquire)
        )
        logger.debug(
            "channels_to_acquire : %s"
            % str(np.array(self.ch_names)[self.channels_to_acquire])
        )

        self.n_ch = len(channels_to_acquire)
        logger.debug("n_ch for online session : %d" % self.n_ch)

        # ------------------------------------------------------------------------------------------------
        # find/connect marker outlet

        logger.info("looking for a marker stream...")
        is_searching_marker_stream = True

        self.marker_stream, self.marker_inlet = streaming.init_LSL_inlet(
            temp_new_conf.marker_acquisition_stream_name,
            temp_new_conf.marker_acquisition_stream_type,
            await_stream = True,
            timeout = temp_new_conf.marker_stream_await_timeout_ms
        )
        logger.info("Configuration Done.")

    def main(self):

        logger.info("Acquisition System Controller was started.")

        if self.adaptation:
            calibration_dir = os.path.join(
                conf_system.data_dir,
                conf_system.save_folder_name,
                "calibration",
            )
            if os.path.exists(calibration_dir) is False:
                os.mkdir(calibration_dir)
            pandas_save_utility = PandasSaveUtility(
                file_path=os.path.join(calibration_dir, "calibration_log")
            )
            columns = ["w", "b", "cl_mean", "Cov_inv", "classes", "time"]
            pandas_save_utility.add(
                data=[
                    [
                        conf_system.adaptation_clf.coef_,
                        conf_system.adaptation_clf.intercept_,
                        conf_system.adaptation_clf.cl_mean,
                        conf_system.adaptation_clf.C_inv,
                        conf_system.adaptation_clf.classes_,
                        datetime.datetime.now().strftime("%y/%m/%d-%H:%M:%S"),
                    ]
                ],
                columns=columns,
                save_as_html=True,
            )

        labels = list()
        preds = list()

        trial_was_done = False

        # if conf_system.show_barplot:
        #     logger.info("show_barplot is True")
    
        #     process_manager = ProcessManager()
        #     live_barplot_process, live_barplot_state_dict = process_manager.create_live_barplot_process(self.n_class)
        #     live_barplot_process.start()

        if not os.path.exists(
            os.path.join(conf_system.repository_dir_base, "media", "tmp")
        ):
            os.makedirs(
                os.path.join(conf_system.repository_dir_base, "media", "tmp")
            )

        self.state_dict["acquire_trials"] = True
        self.acq.start()

        while self.state_dict["acquire_trials"] is True:
            try:
                new_trial = self.acq.is_got_new_trial_marker()
                # logger.info(new_trial)
                if new_trial is not False:
                    trial_was_done = False
                    self.state_dict["trial_completed"] = False
                    label_trial = int(str(new_trial + 1)[-1])
                    logger.info("New Trial Started : %d" % label_trial)
                    labels.append(label_trial)
                    clf_out = list()
                    for m in range(self.n_class):
                        clf_out.append(list())
                    clf_out_mean = list()
                    for m in range(self.n_class):
                        clf_out_mean.append(list())
                    distances = list()
                    stimulus_cnt = 0
                    dynamic_stopping_stim_num = self.dynamic_stopping_params[
                        "min_n_stims"
                    ]

                    # for barplot
                    label_trial_index = label_trial - 1
                    live_barplot_state_dict["index_best_class"] = label_trial_index
                    colors = ["tab:blue" for m in range(self.n_class)]
                    colors[label_trial_index] = "tab:green"
                    for m in range(self.n_class):
                        live_barplot_state_dict["mean_classificaiton_values"][m] = 0

                    fb_barplot_dir = os.path.join(
                        conf_system.repository_dir_base,
                        "media",
                        "tmp",
                        "fb_barplot.png",
                    )
                    if os.path.exists(fb_barplot_dir):
                        os.remove(fb_barplot_dir)

                if self.epochs.has_new_data():
                    # increment index to track LSL packages
                    self.inc_idx += 1

                    epoch, events = self.epochs.get_new_data()
                    if trial_was_done:
                        continue
                    
                    logger.info("New epochs was recorded.")
                    logger.debug("epoch.shape : %s" % str(epoch.shape))
                    logger.debug("events : %s" % str(events))

                    y = np.empty(0)
                    for event in events:
                        if event in conf_system.markers["target"]:
                            y = np.append(
                                y,
                                conf_system.labels_binary_classification[
                                    "target"
                                ],
                            )
                        elif event in conf_system.markers["nontarget"]:
                            y = np.append(
                                y,
                                conf_system.labels_binary_classification[
                                    "nontarget"
                                ],
                            )
                        else:
                            raise ValueError("Unknown event")

                    vec = self.vectorizer.transform(epoch)
                    self.push_features_to_lsl(vec, y)

                    if conf_system.adaptation:
                        # this function will calclate new set of w and b.
                        # And it's not overwritten yet. It will be overwritten after trial.
                        conf_system.adaptation_clf.adaptation(
                            vec,
                            y,
                            eta_cov=conf_system.adaptation_eta_cov,
                            eta_mean=conf_system.adaptation_eta_mean,
                        )
                        self.adaptation_available_new = True

                    scores = self.clf.decision_function(vec)

                    stimulus_cnt += epoch.shape[0]
                    logger.info("stimulus_cnt : %s" % str(stimulus_cnt))
                    logger.info("scores : %s" % str(scores))

                    for index, event in enumerate(events):
                        event_num = int(str(event)[-1])
                        if scores.ndim == 0:
                            distances.append([event_num, scores])
                        else:
                            distances.append([event_num, scores[index]])

                    logger.debug("distances : %s" % str(distances))

                    self.push_distances_to_lsl(distances)

                    if (
                        conf_system.show_barplot
                        and stimulus_cnt >= self.n_class
                    ):
                        clf_out = get_distances_class(distances, self.n_class)
                        for index, clf_out_class in enumerate(clf_out):
                            # clf_out_mean[idx] = np.mean(clf_out_class)
                            live_barplot_state_dict["mean_classificaiton_values"][index] = np.mean(clf_out_class)

                    if (
                        self.dynamic_stopping is True
                        and trial_was_done is False
                    ):
                        if (
                            stimulus_cnt
                            >= self.dynamic_stopping_params["min_n_stims"]
                        ):
                            for stim_num in range(
                                dynamic_stopping_stim_num, stimulus_cnt + 1
                            ):
                                clf_out = get_distances_class(
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
                                    trial_was_done = True
                                    break
                                """

                                for index, clf_out_class in enumerate(clf_out):
                                    clf_out_mean[index] = np.mean(clf_out_class)

                                logger.info(
                                    "label trial (target) : %s"
                                    % str(label_trial)
                                )
                                target_idx = label_trial - 1
                                target_distances = np.array(
                                    clf_out[target_idx]
                                )

                                nontarget_clf_out_mean = clf_out_mean.copy()
                                nontarget_clf_out_mean.pop(target_idx)
                                nontarget_clf_out = clf_out.copy()
                                nontarget_clf_out.pop(target_idx)

                                logger.info(
                                    "len(nontarget_clf_out) : %d"
                                    % len(nontarget_clf_out)
                                )
                                logger.info(
                                    "len(nontarget_clf_out_mean) : %d"
                                    % len(nontarget_clf_out_mean)
                                )

                                logger.info(
                                    "nontarget_distances : %s"
                                    % str(nontarget_clf_out_mean)
                                )

                                best_nontarget_idx = np.argmax(
                                    nontarget_clf_out_mean
                                )
                                logger.info(
                                    "best_nontarget_idx : %d"
                                    % best_nontarget_idx
                                )

                                best_nontarget_distances = np.array(
                                    nontarget_clf_out[best_nontarget_idx]
                                )

                                logger.info(
                                    "target_distances : %s"
                                    % str(target_distances)
                                )
                                logger.info(
                                    "best_nontarget_distances : %s"
                                    % str(best_nontarget_distances)
                                )

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

                                t_score, p = stats.ttest_ind(
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

                                logger.info("pvalue : %.4f" % p)

                                if p <= self.dynamic_stopping_params["pvalue"]:

                                    fig_fb = plt.figure(num=2)
                                    plt.bar(
                                        conf.words, clf_out_mean, color=colors
                                    )
                                    plt.tick_params(
                                        left=False,
                                        right=False,
                                        labelleft=False,
                                    )
                                    fig_fb.savefig(
                                        os.path.join(
                                            conf_system.repository_dir_base,
                                            "media",
                                            "tmp",
                                            "fb_barplot.png",
                                        ),
                                        dpi=1000,
                                    )
                                    plt.close(fig_fb)

                                    pred_trial = label_trial
                                    preds.append(pred_trial)
                                    logger.info("labels : %s" % str(labels))
                                    logger.info("preds : %s" % str(preds))
                                    logger.info(
                                        "n_stimulus : %d" % stimulus_cnt
                                    )
                                    acc = accuracy_score(labels, preds)
                                    logger.info("Acc : %.3f" % acc)
                                    self.state_dict["trial_classification_status"] = (
                                        TrialClassificationStatus.DECODED_EARLY  # decoded by dynamic stopping
                                    )
                                    self.state_dict["trial_label"] = label_trial
                                    self.state_dict["trial_stimulus_count"] = stimulus_cnt
                                    self.state_dict["trial_completed"] = True
                                    trial_was_done = True
                                    break
                            dynamic_stopping_stim_num = stimulus_cnt + 1

                    if (
                        stimulus_cnt == self.max_n_stims
                        and trial_was_done is False
                    ):
                        # without dynamic stopping
                        clf_out = get_distances_class(distances, self.n_class)
                        logger.debug("clf_out : %s" % str(clf_out))
                        for index, clf_out_class in enumerate(clf_out):
                            clf_out_mean[index] = np.mean(clf_out_class)
                        logger.debug("clf_out_mean : %s" % str(clf_out_mean))

                        fig_fb = plt.figure(2)
                        plt.bar(conf.words, clf_out_mean, color=colors)
                        plt.tick_params(
                            left=False, right=False, labelleft=False
                        )
                        fig_fb.savefig(
                            os.path.join(
                                conf_system.repository_dir_base,
                                "media",
                                "tmp",
                                "fb_barplot.png",
                            ),
                            dpi=300,
                        )
                        plt.close(fig_fb)

                        pred_trial = np.argmax(clf_out_mean) + 1
                        preds.append(pred_trial)
                        acc = accuracy_score(labels, preds)
                        logger.info("labels : %s" % str(labels))
                        logger.info("preds : %s" % str(preds))
                        logger.info("Acc : %.3f" % acc)
                        if pred_trial == label_trial:
                            self.state_dict["trial_classification_status"] = TrialClassificationStatus.DECODED
                        else:
                            self.state_dict["trial_classification_status"] = TrialClassificationStatus.UNDECODED

                        self.state_dict["trial_label"] = label_trial
                        self.state_dict["trial_stimulus_count"] = stimulus_cnt
                        self.state_dict["trial_completed"] = True
                        trial_was_done = True

                if trial_was_done and self.adaptation_available_new:
                    # overwrite w and b with new set.
                    conf_system.adaptation_clf.apply_adaptation()
                    logger.info("classifier was updated.")
                    pandas_save_utility.add(
                        data=[
                            [
                                conf_system.adaptation_clf.coef_,
                                conf_system.adaptation_clf.intercept_,
                                conf_system.adaptation_clf.cl_mean,
                                conf_system.adaptation_clf.C_inv,
                                conf_system.adaptation_clf.classes_,
                                datetime.datetime.now().strftime(
                                    "%y/%m/%d-%H:%M:%S"
                                ),
                            ]
                        ],
                        columns=columns,
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
        self.acq.stop()


def init_asc(state_dict=None):
    # TO DO
    # logging

    clfh = ClassifierFactory(n_channels=conf_system.n_ch)
    clf = clfh.getmodel()

    asc = AcquisitionSystemController(
        markers=conf_system.markers,
        tmin=conf_system.tmin,
        tmax=conf_system.tmax,
        baseline=conf_system.baseline,
        filter_freq=conf_system.filter_freq,
        filter_order=conf_system.filter_order,
        clf=clf,
        ivals=conf_system.ivals,
        n_class=conf_system.n_class,
        adaptation=conf_system.adaptation,
        dynamic_stopping=conf_system.dynamic_stopping,
        dynamic_stopping_params=conf_system.dynamic_stopping_params,
        max_n_stims=conf_system.n_stimulus,
        state_dict=state_dict,
    )

    return asc


def interface(
    name, name_main_outlet="main", log_file=True, log_stdout=True, state_dict=None
):
    # ==============================================
    # This function is called from main module.
    # It opens LSL and communicate with main module.
    # ==============================================
    #
    # name : name of this module. main module will call this module with this name.
    #        This name will be given by main module.
    # name_main_outlet : name of main module's outlet. This module will find the main module with this name.
    #

    if state_dict == None:
        state_dict = init_acquisition_state_dict()

    # set_logger(file=log_file, stdout=log_stdout)
    params = dict()  # variable for receive parameters

    inlet = intermodule_comm.getIntermoduleCommunicationInlet(name_main_outlet)
    # print('LSL connected, Acquisition Controller Module')
    state_dict["LSL_inlet_connected"] = True

    asc = None

    while True:
        data, _ = inlet.pull_sample(timeout=0.01)
        if data is not None:
            if data[0].lower() == name:
                if data[1].lower() == "cmd":
                    logger.info(
                        "cmd '%s' was recieved with param : %s"
                        % (data[2], str(json.loads(data[3])))
                    )
                    # ------------------------------------
                    # command
                    if data[2].lower() == "start_recording":
                        f_dir = json.loads(data[3])
                        conf_system.start_recording(f_dir)
                    elif data[2].lower() == "init_recorder":
                        params["init_recorder"] = json.loads(data[3])
                        conf_system.initialize_recorder(
                            params["init_recorder"]
                        )
                    elif data[2].lower() == "stop_recording":
                        conf_system.stop_recording()
                    elif data[2].lower() == "start_calibration":
                        asc.calibration(params)
                        state_dict["trial_completed"] = True
                    elif data[2].lower() == "init":
                        asc = init_asc(state_dict=state_dict)
                    elif data[2].lower() == "set":
                        asc.init()
                    elif data[2].lower() == "connect_lsl":
                        # asc = init_asc()
                        asc.connect_LSL()
                    elif data[2].lower() == "start":
                        asc.main()
                    else:
                        raise ValueError("Unknown command was received.")
                    # modify here to add new commands
                    # ------------------------------------

                elif data[1].lower() == "params":
                    # ------------------------------------
                    # parameters
                    params[data[2]] = json.loads(data[3])
                    logger.info(
                        "Param Received : %s, %s"
                        % (str(data[2]), str(params[data[2]]))
                    )
                    # ------------------------------------
                else:
                    raise ValueError("Unknown LSL data type received.")


if __name__ == "__main__":
    print('Testing AcquisitionSystemController')
    clfh = ClassifierFactory(n_channels=conf_system.n_ch)
    clf = clfh.get_model()

    testdict = dict(markers=conf_system.markers,
        tmin=conf_system.tmin,
        tmax=conf_system.tmax,
        baseline=conf_system.baseline,
        filter_freq=conf_system.filter_freq,
        filter_order=conf_system.filter_order,
        clf=clf,
        ivals=conf_system.ivals,
        n_class=conf_system.n_class,
        adaptation=conf_system.adaptation,
        dynamic_stopping=conf_system.dynamic_stopping,
        dynamic_stopping_params=conf_system.dynamic_stopping_params,
        max_n_stims=conf_system.n_stimulus)
    
    for k,v in testdict.items():
        print(k, v)