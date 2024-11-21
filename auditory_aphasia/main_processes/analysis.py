import os

import matplotlib
import mne
import numpy as np
import pyclf
import pyerp  # TODO: WHAT DO WE NEED PYERP FOR? << Replace this by a more standard solution

from auditory_aphasia.config_builder import SystemConfig

matplotlib.use("tkagg")


def session_parser(data_dir, f_name_prefix, date, subject_code, extension):

    folders = os.listdir(data_dir)
    if date is None:
        import datetime

        date = datetime.datetime.now().strftime("%y_%m_%d")

    if subject_code is None:
        subject_code = list()
        for folder in folders:
            folder = folder.split("_")
            if len(folder) == 1:
                continue
            folder_subject_code = folder[0]
            del folder[0]

            folder_date = "_".join(folder)

            if folder_date == date:
                subject_code.append(folder_subject_code)
        if len(subject_code) > 1:
            raise ValueError("Two participants were found at date : %s" % date)
        elif len(subject_code) == 1:
            subject_code = subject_code[0]
        elif len(subject_code) == 0:
            raise ValueError("Couldn't find session at date : %s" % date)

    session = "_".join([subject_code, date])

    files = os.listdir(os.path.join(data_dir, session))

    condition = list()
    soa = list()

    for file in files:
        if f_name_prefix in file:
            if extension in file:
                condition.append(file.split("_")[-3])
                soa.append(file.split("_")[-2])

    conditions = np.unique(condition)
    soas = np.unique(soa)

    return session, conditions, soas


def plot_erp(
    data_dir,
    save_dir,
    system_config: SystemConfig,
    marker,
    date=None,
    subject_code=None,
    channels=["F3", "Cz"],
    eog_channel="vEOG",
    l_freq=1,
    h_freq=20,
    tmin=-0.35,
    tmax=1.2,
    baseline=None,
    resample=250,
):
    # print(data_dir)

    extension = "vhdr"

    session, conditions, soas = session_parser(
        data_dir, system_config.f_name_prefix, date, subject_code, extension=extension
    )

    pyerp.utils.mkdir(os.path.join(save_dir, session, "erp"))

    files = os.listdir(os.path.join(data_dir, session))

    for condition in conditions:
        for soa in soas:
            files_to_load = list()
            for file in files:
                if system_config.f_name_prefix in file and extension in file:
                    condition_file = file.split("_")[-3]
                    soa_file = file.split("_")[-2]
                    if condition == condition_file and soa == soa_file:
                        files_to_load.append(file)
            eeg_files = list()
            for file in files_to_load:
                eeg_files.append(
                    [
                        os.path.join(data_dir, session, file.split(".")[0]),
                        "%s_%s" % (condition, soa),
                    ]
                )

            epochs = pyerp.export_epoch(
                os.path.join(data_dir, session),
                eeg_files,
                marker,
                l_freq=l_freq,
                h_freq=h_freq,
                resample=resample,
                tmin=tmin,
                tmax=tmax,
                file_type=extension,
                split_trial=False,
            )

            if eog_channel is not None:
                epochs.set_channel_types({eog_channel: "eog"})
            epochs.set_montage("standard_1020")

            vlim = pyerp.get_min_max_tnt(epochs, picks=channels, units="uV")
            vlim = tuple([m * 1.1 for m in vlim])
            fig = pyerp.plot_2ch_tnt(
                epochs,
                vlim=vlim,
                picks=channels,
                legend_loc="upper right",
                figsize=[16, 8],
            )
            fig.savefig(
                os.path.join(
                    save_dir,
                    session,
                    "erp",
                    "%s_%s_2ch.jpg" % (condition, soa),
                ),
                dpi=100,
            )

            time_scalpmap = np.arange(0, tmax, 0.02)
            fig = epochs.average().plot_topomap(
                time_scalpmap, vlim=vlim, ch_type="eeg", nrows=8, show=False
            )
            fig.savefig(
                os.path.join(
                    save_dir,
                    session,
                    "erp",
                    "%s_%s_target_topo.jpg" % (condition, soa),
                ),
                dpi=100,
            )
            fig = mne.combine_evoked(
                [epochs["target"].average(), epochs["nontarget"].average()],
                weights=[1, -1],
            ).plot_topomap(time_scalpmap, vlim=vlim, ch_type="eeg", nrows=8, show=False)
            fig.savefig(
                os.path.join(
                    save_dir,
                    session,
                    "erp",
                    "%s_%s_diff_topo.jpg" % (condition, soa),
                ),
                dpi=100,
            )


def classify_erp(
    data_dir,
    save_dir,
    system_config: SystemConfig,
    marker,
    ivals,
    cv=4,
    date=None,
    subject_code=None,
    channels=["F3", "Cz"],
    eog_channel="vEOG",
    l_freq=1,
    h_freq=20,
    tmin=-0.35,
    tmax=1.2,
    baseline=None,
    resample=250,
):
    extension = "vhdr"

    session, conditions, soas = session_parser(
        data_dir, system_config.f_name_prefix, date, subject_code, extension=extension
    )

    pyerp.utils.mkdir(os.path.join(save_dir, session, "classification"))

    files = os.listdir(os.path.join(data_dir, session))

    pd = pyerp.utils.pd.quickSave(
        file_dir=os.path.join(save_dir, session, "classification", "classification"),
        delete_if_exists=True,
    )

    for condition in conditions:
        for soa in soas:
            files_to_load = list()
            for file in files:
                if system_config.f_name_prefix in file and extension in file:
                    condition_file = file.split("_")[-3]
                    soa_file = file.split("_")[-2]
                    if condition == condition_file and soa == soa_file:
                        files_to_load.append(file)
            eeg_files = list()
            for file in files_to_load:
                eeg_files.append(
                    [
                        os.path.join(data_dir, session, file.split(".")[0]),
                        "%s_%s" % (condition, soa),
                    ]
                )

            epochs = pyerp.export_epoch(
                os.path.join(data_dir, session),
                eeg_files,
                marker,
                l_freq=l_freq,
                h_freq=h_freq,
                resample=resample,
                tmin=tmin,
                tmax=tmax,
                file_type=extension,
                split_trial=False,
            )

            if eog_channel is not None:
                epochs.set_channel_types({eog_channel: "eog"})
            epochs.pick_types(eeg=True)

            clf = pyclf.lda.classification.ToeplitzLDA(n_channels=len(epochs.ch_names))

            print("analyzing....")
            score = pyerp.classify_binary(
                epochs,
                clf=clf,
                ivals=ivals,
                cv=cv,
                scoring="roc_auc",
                n_jobs=-1,
            )

            print(score)

            score.pop("scores")
            score["permutation_scores"] = np.mean(score["permutation_scores"])

            pd.add(
                data=[
                    [
                        condition,
                        soa,
                        score["score"],
                        score["permutation_scores"],
                        score["pvalue"],
                        # score['n_permutations'],
                        # score['cv'],
                        # score['scoring'],
                        # score['estimator']
                    ]
                ],
                columns=[
                    "condition",
                    "soa",
                    "accuracy",
                    "chance level",
                    "pvalue",
                    #    'n_permutations',
                    #    'cross validation',
                    #    'scoring',
                    #    'estimator'
                ],
            )
            pd.save_html()


def run_analysis(system_config: SystemConfig):

    data_dir = system_config.data_dir
    save_dir = os.path.join(data_dir, "plots", system_config.save_folder_name)

    subject_code = None  # TODO: Where would those acutally be set?
    date = None

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    marker = [
        [101, "nontarget", "word1"],
        [102, "nontarget", "word2"],
        [103, "nontarget", "word3"],
        [104, "nontarget", "word4"],
        [105, "nontarget", "word5"],
        [106, "nontarget", "word6"],
        [111, "target", "word1"],
        [112, "target", "word2"],
        [113, "target", "word3"],
        [114, "target", "word4"],
        [115, "target", "word5"],
        [116, "target", "word6"],
        [210, "new-trial/disable", ""],
    ]

    ivals = [
        [0.08, 0.15],
        [0.151, 0.21],
        [0.211, 0.28],
        [0.271, 0.35],
        [0.351, 0.44],
        [0.45, 0.56],
        [0.561, 0.7],
        [0.701, 0.85],
        [0.851, 1],
        [1.001, 1.2],
    ]

    plot_erp(
        data_dir=data_dir,
        save_dir=save_dir,
        system_config=system_config,
        marker=marker,
        eog_channel=None,
        subject_code=subject_code,
        date=date,
    )

    classify_erp(
        data_dir=data_dir,
        save_dir=save_dir,
        f_name_prefix=system_config.file_name_prefix,
        marker=marker,
        eog_channel=None,
        ivals=ivals,
        subject_code=subject_code,
        date=date,
    )

