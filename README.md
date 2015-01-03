py-subs
====================

A python script which runs after uTorrent finishes downloading and automatically finds subtitles.

The script simply tries to run subliminal on every video file (visits sub-directories recursively as well).
If the given file is not a video file, subliminal will recognize it and the script will move on to the next file.
The script uses babelfish to specify subtitle language to subliminal.

Downloaded subs are saved with the video file's name and the language 2-letter extension.
For example: 'Inception.mkv' english srt subs will be saved as 'Inception.en.srt'.

Usage
====================
Edit your preferred languages inside the script (under the LANGUAGE_LIST const).
Change the DOWNLOADS_PATH const in the script to your uTorrent completed downloads path.
You're (almost) good to go!

The script can be used from the command line:

	$ pysubs -p /Downloads/Movies/Inception/Inception.mkv
	$ pysubs -d /Downloads/Movies/Inception -f Inception.mkv -l heb eng -p addic7ed

But works best with uTorrent:

    Options -> Advanced -> Run Program
    When download is finished, run (Change paths accordingly): 
	'C:\Python27\pythonw.exe D:\Projects\py-subs\pysubs.py -u "%D" "%F"'
	
	Important: Be sure to use different folders for new downloads and completed downloads, or else py-subs won't work.
	
For full usage instructions:
    
    $ pysubs --help
	
Dependencies
====================
subliminal
babelfish
logbook