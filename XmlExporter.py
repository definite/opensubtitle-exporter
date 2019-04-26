#!/usr/bin/env python
"""XmlExporter extract xml or gziped xml to other file format
"""

import gzip
import logging
import sys
import xml.etree.ElementTree as ETree
import CommonFunctions

from argparse import Namespace
from xml.etree.ElementTree import Element as XmlNode
from CommonArgParser import CommonArgParser
from CommonArgParser import ExitStatus
from CommonFunctions import next_file
from DbHandler import DbHandler


class UnsupportedDbError(Exception):
    def __init__(self, db_product):
        super(UnsupportedDbError, self).__init__()
        self.db_product = db_product

    def __str__(self):
        return "Unsupported Db: %s" % self.db_product


class NoTextInWElementError(Exception):
    def __init__(self, filename, document_id, w_id):
        super(NoTextInWElementError, self).__init__()
        self.filename = filename
        self.document_id = document_id
        self.w_id = w_id

    def __str__(self):
        return "No text in element w %s at document: %s (%s)" % (
            self.w_id, self.document_id, self.filename)


def xml_file_opener(in_file: str):
    if in_file.endswith('.gz'):
        return gzip.open(in_file, mode='r')
    return open(in_file, mode='r')


def pre_order_traversal(node: XmlNode, parent_path: str, args: Namespace):
    """traverse XML using pre-order

    Args:
        node (XmlNode): Current node
        parent_path (str): XML path to this node without the document node.
                Note that tag document will be omitted
        args (Namespace): [description]
    """
    level = parent_path.count('.')
    logging.debug(
            "%s%s %s %s" % (
                    " " * level, node.tag, node.attrib,
                    "" if not node.text else "| " + node.text))
    if hasattr(args, 'db_handler'):
        args.db_handler.write_node(node, parent_path, args)
    if node.tag == 'document':
        # Omit the tag <document>
        this_path = ''
    else:
        this_path = node.tag
    for child in node:
        pre_order_traversal(child, f"{parent_path}.{this_path}", args)


def export_xml_file(in_file: str, args: Namespace):
    logging.info(f"Reading {in_file}")
    with xml_file_opener(in_file) as f:
        tree = ETree.parse(f)
        root = tree.getroot()
        pre_order_traversal(root, '', args)


def main():
    """Run as command line program"""
    parser = CommonArgParser(__file__)
    parser.add_common_argument('lang', help='The language to be inserted')
    parser.add_common_argument('src_dir', help='Source directory')
    parser.add_sub_command(
            'db',
            [
                    ('-A --db-admin-password', {
                            'type': str,
                            'help': 'The DB admin password'}),
                    ('-b --db-product', {
                            'type': str, 'default': 'postgresql',
                            'help': 'The DB to store'}),
                    ('-N --db-name', {
                            'type': str, 'default': 'opensubtitle',
                            'help': 'The DB name'}),
                    ('-p --db-password', {
                            'type': str,
                            'help': 'The DB password'}),
                    ('-u --db-user', {
                            'type': str,
                            'help': 'The DB username'}),
                    ],
            help='Export to DB')

    args = parser.parse_all()
    if hasattr(args, 'sub_command'):
        if args.sub_command == 'db':
            db_handler = DbHandler.get_handler(args)
            db_handler.prepare()
            setattr(args, 'db_handler', db_handler)
        else:
            logging.critical('Not implement yet')
            sys.exit(ExitStatus.FATAL_INVALID_OPTIONS)
    else:
        parser.parse_args(['-h'])
        sys.exit(ExitStatus.FATAL_INVALID_ARGUMENTS)
    for f in next_file(args.src_dir, ['*.xml.gz', '*.xml']):
        export_xml_file(f, args)


if __name__ == '__main__':
    CommonFunctions.run_doctest_and_quit_if_enabled()
    main()
