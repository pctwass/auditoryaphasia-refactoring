import pytest

from auditory_aphasia.common.utils import increment_file_name_if_exists


def test_increment_file_name_if_exists(
    tmp_path,
):  # tmp_path is a default fixture from pytest
    fexists = tmp_path / "file.eeg"
    fexists.touch()

    fnew = tmp_path / "file123.eeg"

    fexists2 = tmp_path / "file2_1.eeg"
    fexists2.touch()

    nfex = increment_file_name_if_exists(fexists)
    nfnew = increment_file_name_if_exists(fnew)
    nfex2 = increment_file_name_if_exists(fexists2)

    assert nfex == tmp_path / "file_1.eeg", "First increment failed"
    assert nfnew == fnew, "New file changed but shoud not"
    assert nfex2 == tmp_path / "file2_2.eeg", "Second increment failed"
