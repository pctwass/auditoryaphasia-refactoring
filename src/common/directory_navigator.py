import os
import config.conf as conf

def get_word_audio_file_path(
    base_dir : str,
    condition : str,
    word : str,
    file_name : str,
) -> str:
    return os.path.join(
        base_dir,
        'media',
        'audio',
        conf.language,
        'words',
        condition,
        word,
        file_name
    )


def get_sentence_audio_file_path(
    base_dir : str,
    condition : str,
    word : str,
    file_name : str,
) -> str:
    return os.path.join(
        base_dir,
        'media',
        'audio',
        conf.language,
        'sentences',
        condition,
        word,
        file_name
    )


def get_restart_audio_file_path(
    base_dir : str,
) -> str:
    return os.path.join(
        base_dir,
        'media',
        'audio',
        conf.language,
        'misc',
        'restart.wav'
    )


def get_relax_audio_file_path(
    base_dir : str,
) -> str:
    return os.path.join(
        base_dir,
        'media',
        'audio',
        conf.language,
        'misc',
        'relax.wav'
    )