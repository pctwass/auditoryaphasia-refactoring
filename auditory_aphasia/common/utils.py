import json
import os
import re


def increment_file_name_if_exists(file_path: Path) -> Path:
    if not file_path.exists():
        return file_path
    else:
        # existing files with same prefix
        existing_files = list(file_path.parent.glob(f"{file_path.stem}.*"))

        # find suffices
        ixs = [
            re.search(rf"(.*)_(\d+)\.{file_path.suffix[1:]}", f.name)
            for f in existing_files
        ]

        # first increment
        if ixs == [None]:
            new_file_path = file_path.with_name(
                file_path.stem + "_1" + file_path.suffix
            )

        else:
            matches = [r for r in ixs if r]
            ix_max = max([int(r.group(2)) for r in matches])

            # increment file suffix just before
            new_file_path = file_path.with_name(
                file_path.stem.replace(f"_{ix_max}", f"_{ix_max+1}") + file_path.suffix
            )

    return new_file_path


# def check_file_exists_on_extenstion(file_path: str, extension: str) -> str:
#     """
#     Parameters
#     ----------
#
#     f_dir : path-like
#         don't include extension
#     extension : str
#         don't include .(dot)
#     """
#     f_name = file_path + "." + extension
#     if os.path.exists(f_name):
#         idx = 1
#         while True:
#             idx += 1
#             f_name = file_path + "_%d.%s" % (idx, extension)
#             if not os.path.exists(f_name):
#                 break
#
#     return f_name


# used only for calibration
def get_n_sessions(
    data_dir: str, subject_code: str, datestr: str
) -> dict[str, int | list[str]]:
    sessions_info_dict = dict()
    sessions_info_dict["n_offline"] = 0
    sessions_info_dict["n_online"] = 0
    sessions_info_dict["offline_sessions"] = list()
    sessions_info_dict["online_sessions"] = list()

    sessions = list()
    folders = _sort_list(os.listdir(data_dir))
    for folder in folders:
        if (
            "_".join(folder.split("_")[1:]) != datestr
            and folder.split("_")[0].lower() == subject_code.lower()
        ):
            sessions.append(folder)

    sessions = _sort_list(sessions)

    for session in sessions:
        meta = json.load(open(os.path.join(data_dir, session, "meta.json"), "r"))
        if meta["session_type"] == "offline":
            sessions_info_dict["n_offline"] += 1
            sessions_info_dict["offline_sessions"].append(session)
        elif meta["session_type"] == "online":
            sessions_info_dict["n_online"] += 1
            sessions_info_dict["online_sessions"].append(session)
        else:
            raise ValueError("unkown session_type : %s" % (str(meta["session_type"])))

    return sessions_info_dict


# used only for calibration
def get_files_for_calibration(
    n_sessions: int,
    data_dir: str,
    extension: str,
    soa_ms: float,
    condition: str,
    file_name_prefix: str,
    th_soa_ms: float = 350,
) -> enumerate[str]:
    files_for_calibration = list()

    if n_sessions["n_offline"] >= 2 and n_sessions["n_online"] == 0:
        # first online session
        # load data which has same (speaker) condition and soa from former 2 sessions
        for session in _sort_list(n_sessions["offline_sessions"]):
            files = os.listdir(os.path.join(data_dir, session))
            tmp = list()
            for file in files:
                if file.split(".")[-1] == extension:
                    tmp.append(file)
            files = tmp
            for file in files:
                if file_name_prefix in file:
                    condition_file = file.split("_")[-3]
                    soa_file = int(file.split("_")[-2])
                    if (
                        soa_ms >= th_soa_ms
                        and soa_file >= th_soa_ms
                        and condition_file == condition
                    ):
                        files_for_calibration.append(
                            os.path.join(data_dir, session, file)
                        )
                    elif (
                        soa_ms < th_soa_ms
                        and soa_file < th_soa_ms
                        and condition_file == condition
                    ):
                        files_for_calibration.append(
                            os.path.join(data_dir, session, file)
                        )

    elif n_sessions["n_offline"] >= 2 and n_sessions["n_online"] > 0:
        # load previous online session (even if speaker condition or soa was different)
        online_sessions = _sort_list(n_sessions["online_sessions"])
        session = online_sessions[-1]
        files = os.listdir(os.path.join(data_dir, session))
        for file in files:
            if file.split(".")[-1] == extension:
                files_for_calibration.append(os.path.join(data_dir, session, file))
    elif n_sessions["n_offline"] < 2:
        # no offline session or one offline session
        pass

    return _sort_list(files_for_calibration)


def _sort_list(data: enumerate) -> enumerate | dict:
    return sorted(data, key=_natural_keys)


def _natural_keys(text: str) -> str:
    return [_text_to_digit_if_digit(c) for c in re.split(r"(\d+)", text)]


def _text_to_digit_if_digit(text: str) -> int | str:
    return int(text) if text.isdigit() else text
