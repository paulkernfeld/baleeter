#!/usr/bin/env python3
import stat
from datetime import datetime
from datetime import timedelta
from subprocess import call
from os import environ
from os import listdir
from os import remove
from os import stat as os_stat
from os import utime
from os import walk
from os.path import expanduser
from os.path import join
from shutil import rmtree
from textwrap import dedent

# Offset by 12 hours so that this triggers once when you start working, not
# frequently in the middle of work.
max_n_to_delete = 5
max_file_age = timedelta(days=14, hours=12)

dir_path = expanduser("~/Downloads")
file_paths = [join(dir_path, file_path) for file_path in listdir(dir_path)]
paths_and_stats = [(file_path, os_stat(file_path)) for file_path in file_paths]

# This gets the time of last access
files_by_age = sorted(paths_and_stats, key=lambda fpfs: fpfs[1][stat.ST_ATIME])


def file_time(f_stat):
    # Intentionally not using accessed time
    mtime = datetime.utcfromtimestamp(f_stat[stat.ST_MTIME])
    ctime = datetime.utcfromtimestamp(f_stat[stat.ST_CTIME])

    if mtime > datetime.utcnow():
        mtime = None
    if ctime > datetime.utcnow():
        ctime = None

    return max(mtime, ctime)


def get_dir_age(dir_path):
    newest = None

    def visitor(arg, dirname, fnames):
        for fname in fnames:
            ft = max(file_time(os_stat(f)) for f in fnames)
            newest = max(newest, ft)

    walk(dir_path, visitor, None)

n_considered = 0
for file_path, file_stat in files_by_age:
    if n_considered >= max_n_to_delete:
        break

    file_datetime = file_time(file_stat)
    file_age = datetime.now() - file_datetime
    is_dir = stat.S_ISDIR(file_stat.st_mode)
    file_dir_str = "dir" if is_dir else "file"

    if file_age > max_file_age:
        n_considered += 1
        while True:
            action = input(dedent("""
                Baleet {} {}, from {} ago?
                y: Delete
                n: Don't delete
                e: Open with $EDITOR
                o: Open
                q: Quit

                >>> """).format(file_dir_str, file_path, str(file_age)))
            if action in {"y", "Y"}:
                if is_dir:
                    rmtree(file_path)
                else:
                    remove(file_path)
                print("{} baleeted!\n\n".format(file_path))
                break
            elif action in {"o", "O"}:
                call(["open", file_path])
            elif action in {"e", "E"}:
                call([environ["EDITOR"], file_path])
            elif action in {"n", "N"}:
                utime(file_path, None)
                print("{} not baleeted!\n\n".format(file_path))
                break
            elif action in {"q", "Q"}:
                exit()
            else:
                print("Flagrant user error: input {}".format(action))
