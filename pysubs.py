from __future__ import print_function, unicode_literals
from argparse import ArgumentParser
import os
import sys
import datetime
import logbook
from logbook.compat import redirect_logging

import babelfish
import subliminal
from subliminal.cli import app_dir, cache_file, MutexLock
from subliminal.subtitle import get_subtitle_path
from subliminal.cache import region


UTORRENT_COMPLETED_DOWNLOADS_PATH = r'd:\downloads'
LANGUAGES_LIST = ['heb', 'eng']

# The global logger used by the script.
logger = None


def _initialize_logger(log_file_directory_path):
    """
    Initializes a single logger lazily and returns it..

    :param log_file_directory_path: The path of the directory to save to log file in.
    :return: A logbook Logger.
    """
    global logger
    # Create log directory path, if it doesn't exist.
    if not os.path.exists(log_file_directory_path):
        os.makedirs(log_file_directory_path)
    log_file_path = os.path.join(log_file_directory_path, 'py-subs.log')
    # If for some reason we initialize the logger a second time, we want to report it in the previous log.
    if logger is not None:
        logger.error('Logger was initialized again unexpectedly.. new path is: %s' % log_file_path)
    # Create the handlers chain.
    logbook.NullHandler().push_application()
    logbook.FileHandler(log_file_path, level=logbook.INFO, bubble=True).push_application()
    logbook.StreamHandler(sys.stdout, level=logbook.INFO, bubble=True).push_application()
    logger = logbook.Logger('py-subs')
    # Redirect all logs to logbook.
    redirect_logging()
    return logger


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

    args = parser.parse_args()
    # Make sure the supplied providers are valid.
    if args.providers is not None:
        available_providers = [p.name for p in subliminal.provider_manager]
        for provider in args.providers:
            if provider not in available_providers:
                parser.error('Illegal provider! Please choose providers from the list (pysubs --providers-menu)')
    return args


def find_file_subtitles(path, args):
    """
    Finds subtitles for the given video file path.

    :param path: The path of the video file to find subtitles to.
    :param args: The script arguments.
    :return: A list of the created subtitles files.
    """
    if not os.path.isfile(path):
        raise IOError('find_file_subtitles was called with an invalid path!')
    logger.info('py-subs started! Searching subtitles for file: %s' % path)
    # Call subliminal and get the right subtitles.
    try:
        # Get required video information.
        video = subliminal.scan_video(path, subtitles=True, embedded_subtitles=True)
        # Get subtitles.
        languages_list = LANGUAGES_LIST
        if args.languages:
            languages_list = args.languages
        providers_list = None
        if args.providers:
            providers_list = args.providers
        subtitles_result = list(subliminal.download_best_subtitles(
            {video}, languages=set([babelfish.Language(l) for l in languages_list]),
            providers=providers_list).values())
        if len(subtitles_result) == 0:
            logger.info('No subtitles were found. Moving on...')
            return []
        subtitles_result = subtitles_result[0]
        logger.info('Found %d subtitles. Saving files...' % len(subtitles_result))
        # Save subtitles alongside the video file.
        results_list = list()
        for subtitles in subtitles_result:
            saved_languages = set()
            if subtitles.content is None:
                logger.debug('Skipping subtitle %s: no content' % str(subtitles))
                continue
            if subtitles.language in saved_languages:
                logger.debug('Skipping subtitle %s: language already saved' % str(subtitles))
                continue
            subtitles_path = get_subtitle_path(video.name, subtitles.language)
            logger.info('Saving %s to: %s' % (str(subtitles), subtitles_path))
            open(subtitles_path, 'wb').write(subtitles.content)
            saved_languages.add(subtitles.language)
            results_list.append(subtitles_path)
        return results_list
    except ValueError:
        # subliminal raises a ValueError if the given file is not a video file.
        logger.info('Not a video file. Moving on...')
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
    logger.info('py-subs started! Searching subtitles for directory: %s' % path)
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
    # Print the providers menu (supplied by subliminal), if asked to by the user.
    if args.providers_menu:
        print("Available providers are:")
        for provider in subliminal.provider_manager:
            print(provider.name)
        print("Please run the program again with your choice, or without one to use default order.")
        return

    if args.full_path is not None:
        path = args.full_path
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
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    cache_file_path = os.path.join(app_dir, cache_file)
    region.configure('dogpile.cache.dbm', expiration_time=datetime.timedelta(days=30),
                     arguments={'filename': cache_file_path, 'lock_factory': MutexLock})
    # Determine if the given path is a directory, and continue accordingly.
    if os.path.isdir(path):
        _initialize_logger(path)
        results_list = find_directory_subtitles(path, args)
    else:
        _initialize_logger(os.path.dirname(path))
        results_list = find_file_subtitles(path, args)
    logger.info('py-subs finished! Found %d subtitles' % len(results_list))
    logger.info('Subtitles found: %s' % ', '.join(results_list))


if __name__ == '__main__':
    main()
