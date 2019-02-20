#!/usr/bin/env python
"""Extract the downloaded tar.gz"""

from typing import List
import logging
import os
import sys

from GenericArgParser import GenericArgParser
from GenericFunctions import TgzHelper, next_file


def untgz(tgz_filename, out_dir):
    """Un tar gz file

    Args:
        tgz_filename ([type]): [description]
        out_dir ([type]): [description]
    """
    logging.info("Source: %s" % tgz_filename)
    tgz = TgzHelper(tgz_filename, out_dir)
    tgz.extract()


def run_doctest_and_quit_if_enabled():
    """Run doctest and quit the program if doctest is enabled
    The doctest can be enabled by defining environment PY_DOCTEST=1.
    If doctest is enabled, the this function run doctest, print test results,
    then quit;
    otherwise it skips the doctest and continue.
    """
    if os.getenv("PY_DOCTEST", "0") == "0":
        return
    import doctest
    test_result = doctest.testmod()
    print(doctest.testmod(), file=sys.stderr)
    sys.exit(0 if test_result.failed == 0 else 1)


def main():
    """Run as command line program"""
    parser = GenericArgParser(__file__)
    parser.add_argument('src_dir', help='Source directory')
    parser.add_argument(
            'out_dir',
            default='.',
            help="""The directory the files to be extracted.
            (Default: Current directoty""")
    args = parser.parse_all()
    for f in next_file(args.src_dir):
        untgz(f, args.out_dir)


if __name__ == '__main__':
    run_doctest_and_quit_if_enabled()
    main()
