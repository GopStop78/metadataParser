# This is a video file metadata parsing script
# Created by Vladimir on 01.09.2021
# Script uses ffmpeg for reading file duration
# Script

import sys
import os
import time
import platform
import datetime as dt
from stat import *  # ST_SIZE etc
import subprocess
import re
import csv


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() != 'Windows':
        stat = os.stat(path_to_file)
        try:
            return dt.datetime.fromtimestamp(stat.st_birthtime).strftime('%d %m %Y, %H:%M')
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return time.ctime(stat.st_mtime)
    else:
        return dt.datetime.fromtimestamp(os.path.getctime(path_to_file)).strftime('%d-%m-%Y, %H:%M')


class FileList:
    def __init__(self, directory_path):
        self.directoryPath = directory_path     # FileList object will hold directory path that is being searched
        self.filelist = []                      # list of all found files
        self.skippedFiles = []                  # list of files that were skipped while searching
        self.metadata = []                      # files metadata
        self.duration = []                      # files duration
        self.absolutePath = ''                  # files absolute path
        self.st = ''                            # files parameters
        self.fileFormat = ''                    # files formats
        self.metadata_skipped = ''              # skipped files metadata
        self.writer = None                      # csv writer

    def scan_directory(self, allowed_formats):
        # convert allowed_formats to lower case (self.fileFormat will also be converted)
        # we need to do so because "mp4" != "MP4"
        [x.lower() for x in allowed_formats]

        index = 1
        for path, dirs, files in os.walk(self.directoryPath):
            for file in files:
                # Try reading stats of the file (Absoulte path) if it doesn't fail then we can continue parsing
                try:
                    self.absolutePath = path + '\\' + file
                    self.st = os.stat(self.absolutePath)
                    self.fileFormat = file.split('.')[-1]

                except IOError:
                    print('Failed to get information', file)
                else:
                    if self.fileFormat.lower() not in allowed_formats:
                        self.metadata_skipped = [self.absolutePath, self.fileFormat]
                        self.skippedFiles.append(self.metadata_skipped)
                    # There was no error reading filename, so we can continue parsing files
                    else:
                        try:
                            self.duration = filelength(self.absolutePath)
                        except Exception as inst:
                            print(type(inst))  # the exception instance
                            print(inst)  # __str__ allows args to be printed directly
                            print("Probably trying to get filelength of a file that isn't a video file")
                        else:
                            # There was no error reading movie file so we can update metadata
                            duration_string = "%s:%s:%s" % (
                                self.duration['hours'], self.duration['minutes'], self.duration['seconds'])

                            creation_string = creation_date(self.absolutePath)

                            file_size = "{:.2f}".format(self.st[ST_SIZE] / (1024*1024))
                            # metadata format : file_num - fullpath - filename - date - filelength - filesize
                            self.metadata = [index, self.absolutePath, file,
                                             creation_string, duration_string, file_size]
                            index += 1
                            self.filelist.append(self.metadata)
                            print(self.metadata)

    def data_output(self, filelist, out_name):
        self.writer = csv.writer(open(out_name, 'w', encoding='utf-8', newline=''))
        self.writer.writerow(['N', 'Path', 'Name', 'Date', 'Duration, hh:mm:ss', 'Size, Mb'])

        for line in filelist:  # filelist contains dictionaries with metadata about movie file
            self.writer.writerow(line)  # write each entry a single line, separate them with comma


def filelength(file_path):
    process = subprocess.Popen(['ffmpeg', '-i', file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    matches = re.search(r'Duration:\s(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),',
                        stdout.decode('utf-8'), re.DOTALL).groupdict()

    # print process.pid
    process.kill()
    duration = {'hours': matches['hours'], 'minutes': matches['minutes'], 'seconds': matches['seconds'],
                'total_in_sec': float(matches['seconds']) + 60 * float(matches['minutes']) + 3600 * float(
                    matches['hours'])}
    return duration


if __name__ == '__main__':
    path_to_files = 'd:\\TEST_VIDS'
    path_to_output_files = 'metadata.csv'

    print('This is a video file metadata parsing script\n')

    if len(sys.argv) > 1:
        path_to_files = str(sys.argv[1])

        if len(sys.argv) == 3:
            path_to_output_files = str(sys.argv[2])
    else:
        print('Usage: *script_name* *absolute_path_to_input_directory* *output_file_name*')

    print('Parsing path :', path_to_files, '\n')

    file_list = FileList(path_to_files)
    file_list.scan_directory(['mp4', 'mkv', 'flv', 'wmv', 'avi', 'mpg', 'mpeg', 'mpeg4'])

    print('\nFile list ready. Writing metadata to', os.path.dirname(os.path.realpath(__file__)) + '\\' + path_to_output_files)
    file_list.data_output(file_list.filelist, path_to_output_files)
    print('\nDone. Goodbye!')
