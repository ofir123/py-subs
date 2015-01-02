py-subs
===========

A python script which runs after uTorrent finishes downloading and automatically finds subtitles.

The script simply tries to run subliminal on every video file (visits sub-directories recursively as well).
The script relies on the 'guessit' package to detect movies/tv downloads.

Downloaded subs are saved with the video file's name and the language 2-letter extension.
For example: 'Inception.mkv' english srt subs will be saved as 'Inception.en.srt'.

Usage
===========
Edit your preffered languages inside the script (under the LANGUAGE_LIST const).

The script can be used from the command line:

	$ pysubs /Downloads/Movies/Inception/Inception.mkv

But works best with uTorrent:

    Options -> Advanced -> Run Program
    When download is finished, run (Change paths accordingly): 
	'C:\Python27\pythonw.exe D:\Projects\py-subs\pysubs.py "%D" "%F"'
	
	Important: Be sure to use different folders for new downloads and completed downloads, or else py-subs won't work.