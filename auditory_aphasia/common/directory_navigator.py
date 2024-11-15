import os
import auditory_aphasia.config.config as config

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
        config.language,
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
        config.language,
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
        config.language,
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
        config.language,
        'misc',
        'relax.wav'
    )