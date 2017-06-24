from __future__ import print_function, unicode_literals

from argparse import ArgumentParser
import datetime
import os
import sys
import re

import logbook
from logbook.compat import redirect_logging
import pysrt

import babelfish
import subliminal
from subliminal.cache import region
from subliminal.cli import dirs, cache_file, MutexLock
from subliminal.subtitle import get_subtitle_path


UTORRENT_COMPLETED_DOWNLOADS_PATH = r'D:\Downloads'
# A map between each language and its favorite providers (None for all providers).
LANGUAGES_MAP = {
    babelfish.Language('heb'): ['wizdom', 'thewiz', 'subscenter'],
    babelfish.Language('eng'): None
}
NON_ENGLISH_PATTERN = re.compile(r'[^a-zA-Z0-9_\W]+')

# The global logger used by the script.
logger = logbook.Logger('py-subs')


def _get_log_handlers(log_file_directory_path):
    """
    Returns a list of the nested log handlers setup.

    :param log_file_directory_path: The path of the directory to save to log file in.
    :return: The handlers list.
    """
    # Create log directory path, if it doesn't exist.
    if not os.path.exists(log_file_directory_path):
        os.makedirs(log_file_directory_path)
    log_file_path = os.path.join(log_file_directory_path, 'py-subs.log')
    # Create the handlers chain.
    return [logbook.NullHandler(),
            logbook.FileHandler(log_file_path, level=logbook.DEBUG, bubble=True),
            logbook.StreamHandler(sys.stdout, level=logbook.INFO, bubble=True)]


def _get_arguments():
    """
    Gets the arguments from the user.
    utorrent_path - The full path of the video file or directory, in uTorrent format.
    full_path - The full path of the video file or directory.
    providers_menu - Prints the available subtitle providers menu (conflicts with path).
    quiet - If True, no log files will be saved, and nothing will be printed to the screen.
    log_path - If supplied, the log file path will be changed to it (instead of the video file's path).
    languages - If supplied, the script will find subtitles for these languages only. Default list is used otherwise.
    providers - If supplied, the script will use the providers from the list (in that given order) only.
    backwards - If True, non-english strings will be saved backwards, in order to support problematic TVs.
    """
    parser = ArgumentParser(description='Search for subtitles automatically')
    required_group = parser.add_mutually_exclusive_group(required=True)
    required_group.add_argument('-u', '--utorrent', dest='utorrent_path', nargs=2,
                                help='The video file\'s (or directory\'s) full path, in uTorrent format')
    required_group.add_argument('-p', '--path', dest='full_path',
                                help='The video file\'s (or directory\'s) full path')
    required_group.add_argument("-pm", "--providers-menu", action="store_true", dest="providers_menu",
                                default=False, help="The available subtitle providers menu")
    optional_log_group = parser.add_mutually_exclusive_group()
    optional_log_group.add_argument('-q', '--quiet', action='store_true', dest='quiet', default=False,
                                    help='Don\'t save any logs')
    optional_log_group.add_argument('-a', '--log', dest='log_path', help='An alternative log file path')
    parser.add_argument('-l', '--language', dest='languages', nargs='*',
                        help='A list of languages (separated by space)')
    parser.add_argument('-r', '--provider', dest='providers', nargs='*',
                        help='A priority list of subtitle providers (separated by space)')
    parser.add_argument('-b', '--backwards', action='store_true', dest='is_backwards', default=False,
                        help='Reverse all non-english strings and show them backwards')

    args = parser.parse_args()
    # Make sure the supplied providers are valid.
    if args.providers is not None:
        available_providers = [p.name for p in subliminal.provider_manager]
        for provider in args.providers:
            if provider not in available_providers:
                parser.error('Illegal provider! Please choose providers from the list (pysubs --providers-menu)')
    return args


def reverse_strings(subtitles_path, encoding):
    """
    Reverses all non-english strings in the subtitles file.

    :param subtitles_path: The subtitles file path.
    :param encoding: The guessed subtitles encoding.
    """
    logger.info('Reversing non-english strings...')
    subtitles = pysrt.open(subtitles_path, encoding=encoding)
    for line in subtitles:
        # Reverse only matching parts of each line.
        line.text = NON_ENGLISH_PATTERN.sub(lambda x: x.group(0)[::-1], line.text)
    subtitles.save(subtitles_path, encoding=encoding)


def find_file_subtitles(path, args):
    """
    Finds subtitles for the given video file path.

    :param path: The path of the video file to find subtitles to.
    :param args: The script arguments.
    :return: A list of the created subtitles files.
    """
    if not os.path.isfile(path):
        raise IOError('find_file_subtitles was called with an invalid path!')
    logger.info('py-subs started! Searching subtitles for file: {}'.format(path))
    # Call Subliminal and get the right subtitles.
    try:
        # Get required video information.
        video = subliminal.scan_video(path)
        languages_list = list(LANGUAGES_MAP.keys())
        other_languages = []
        subtitle_results = []
        # Get favorite provider subtitles first.
        if args.languages:
            languages_list = [babelfish.Language(l) for l in args.languages]
        for language in languages_list:
            providers_list = LANGUAGES_MAP.get(language, None)
            # Filter providers the user didn't ask for.
            if providers_list is not None and args.providers:
                providers_list = [p for p in providers_list if p in args.providers]
            if providers_list is None or len(providers_list) == 0:
                other_languages.append(language)
            else:
                current_result = list(subliminal.download_best_subtitles(
                    {video}, languages={language}, providers=providers_list).values())
                if len(current_result) > 0:
                    subtitle_results.extend(current_result[0])
        # Add global providers after.
        if len(other_languages) > 0:
            providers_list = None
            if args.providers:
                providers_list = args.providers
            current_result = list(subliminal.download_best_subtitles(
                {video}, languages=set(other_languages), providers=providers_list).values())
            if len(current_result) > 0:
                subtitle_results.extend(current_result[0])
        # Handle results.
        if len(subtitle_results) == 0:
            logger.info('No subtitles were found. Moving on...')
            return []
        logger.info('Found {} subtitles. Saving files...'.format(len(subtitle_results)))
        # Save subtitles alongside the video file.
        results_list = list()
        if __name__ == '__main__':
            if __name__ == '__main__':
                for subtitles in subtitle_results:
                    saved_languages = set()
                    if subtitles.content is None:
                        logger.debug('Skipping subtitle {}: no content'.format(subtitles))
                        continue
                    if subtitles.language in saved_languages:
                        logger.debug('Skipping subtitle {}: language already saved'.format(subtitles))
                        continue
                    subtitles_path = get_subtitle_path(video.name, subtitles.language)
                    logger.info('Saving {} to: {}'.format(subtitles, subtitles_path))
                    open(subtitles_path, 'wb').write(subtitles.content)
                    saved_languages.add(subtitles.language)
                    results_list.append(subtitles_path)
                    # Reverse non-english strings if needed.
                    if args.is_backwards:
                        reverse_strings(subtitles_path, subtitles.guess_encoding())
        return results_list
    except ValueError:
        # Subliminal raises a ValueError if the given file is not a video file.
        logger.info('Not a video file. Moving on...')
        return []
    except Exception:
        # Subliminal crashes randomly sometimes.
        logger.exception('Error while searching for subtitles. Moving on...')
        return []


def find_directory_subtitles(path, args):
    """
    Finds subtitles for all video files in the given directory and its sub-directories.

    :param path: The initial directory path.
    :param args: The script arguments.
    :return: A list of the created subtitle files.
    """
    if not os.path.isdir(path):
        raise IOError('find_directory_subtitles was called with an invalid path!')
    logger.info('py-subs started! Searching subtitles for directory: {}'.format(path))
    results_list = list()
    for directory_name, _, files in os.walk(path):
        for file_name in files:
            results_list.extend(find_file_subtitles(os.path.join(directory_name, file_name), args))
    return results_list


def main():
    """
    This main function is designed to be called from commandline.
    The expected argument is a full path of either a directory or a file (usage: -p <FULL_PATH>.
    Additional arguments are stated in _get_arguments' docstring.
    """
    # Get the arguments from the user.
    args = _get_arguments()
    # Print the providers menu (supplied by Subliminal), if asked to by the user.
    if args.providers_menu:
        print("Available providers are:")
        for provider in subliminal.provider_manager:
            print(provider.name)
        print("Please run the program again with your choice, or without one to use default order.")
        return
    if args.full_path is not None:
        path = os.path.abspath(args.full_path)
    else:
        # uTorrent gives us its completed downloads directory in case we download a single file.
        directory = args.utorrent_path[0]
        file_name = args.utorrent_path[1]
        if directory.lower() == UTORRENT_COMPLETED_DOWNLOADS_PATH.lower():
            path = os.path.join(directory, file_name)
        else:
            # When downloading a directory, uTorrent will just pick a random file from it
            # and will give it as the downloaded file.
            path = directory
    # Configure the subliminal cache.
    cache_dir = dirs.user_cache_dir
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cache_file_path = os.path.join(cache_dir, cache_file)
    region.configure('dogpile.cache.dbm', expiration_time=datetime.timedelta(days=30),
                     arguments={'filename': cache_file_path, 'lock_factory': MutexLock})
    # Determine if the given path is a directory, and continue accordingly.
    is_dir = os.path.isdir(path)
    log_path = path if is_dir else os.path.dirname(path)
    with logbook.NestedSetup(_get_log_handlers(log_path)).applicationbound():
        redirect_logging()
        if os.path.isdir(path):
            results_list = find_directory_subtitles(path, args)
        else:
            results_list = find_file_subtitles(path, args)
        logger.info('py-subs finished! Found {} subtitles'.format(len(results_list)))
        logger.info('Subtitles found: {}'.format(', '.join(results_list)))


if __name__ == '__main__':
    # Handle pythonw stdout and stderr block.
    if sys.executable.endswith("pythonw.exe"):
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
    main()
