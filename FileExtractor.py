#!/usr/bin/env python
"""Extract the downloaded tar.gz"""

import logging
import CommonFunctions

from CommonArgParser import CommonArgParser
from CommonFunctions import TgzHelper, next_file


def untgz(tgz_filename, out_dir):
    """Un tar gz file

    Args:
        tgz_filename ([type]): [description]
        out_dir ([type]): [description]
    """
    logging.info("Source: %s" % tgz_filename)
    tgz = TgzHelper(tgz_filename, out_dir)
    tgz.extract()


def main():
    """Run as command line program"""
    parser = CommonArgParser(__file__)
    parser.add_argument('src_dir', help='Source directory')
    parser.add_argument(
            'out_dir',
            default='.',
            help="""The directory the files to be extracted.
            (Default: Current directoty""")
    args = parser.parse_all()
    for f in next_file(args.src_dir, ['*.tgz', '*.tar.gz']):
        untgz(f, args.out_dir)


if __name__ == '__main__':
    CommonFunctions.run_doctest_and_quit_if_enabled()
    main()
