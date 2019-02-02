#!/usr/bin/env python
"""GenericArgParser is an sub-class of ArgumentParser
that handles sub-parser, environments more easily.

This also handles logging with color format.
The color formattting part is borrowed from KurtJacobson's colored_log.py

https://gist.github.com/KurtJacobson/c87425ad8db411c73c6359933e5db9f9

Requires: python >=3.4  (Enum support)
"""

from __future__ import (absolute_import, division, print_function)
from enum import Enum, unique
import inspect
import logging
import os
import platform
import re
import sys

from argparse import ArgumentParser, ArgumentError, RawDescriptionHelpFormatter
# Following are for mypy
from argparse import Action  # noqa: F401 # pylint: disable=W0611
from argparse import Namespace  # noqa: F401 # pylint: disable=W0611
from argparse import _SubParsersAction  # noqa: F401 # pylint: disable=W0611

try:
    from typing import List, Any  # noqa: F401 # pylint: disable=W0611
    from typing import Dict  # noqa: F401 # pylint: disable=W0611
    from typing import Optional  # noqa: F401 # pylint: disable=W0611
    from typing import Tuple  # noqa: F401 # pylint: disable=W0611
except ImportError:
    sys.stderr.write("python typing module is not installed" + os.linesep)

try:
    # Windows support
    from ctypes import windll
except:
    pass

@unique
class ExitStatus(Enum):
    """Return value of
            Success:
                OK (0)

            Fatal that should stop immediately:
                FATAL_UNSPECIFIED (1)
                    Unspecified fatal error,
                    usually indicate a bug in our scripts.
                FATAL_FAIL (3)
                    Script detected that a fatal error occurred.
                FATAL_INVALID_OPTIONS (4)
                    Wrong options were given.
                FATAL_INVALID_ARGUMENTS (5)
                    Invalid arguments.
                FATAL_MISSING_DEPENDENCY (6)
                    Cannot find dependencY.

            Error that need to stop before next stage:
                ERROR_FAIL (40)
                    Script detected that an error occurred.
                ERROR_CANNOT_READ (41)
                    Cannot read from resources
                ERROR_INPUT_INVALID_FORMAT (42)
                    Format of input are invalid

            Return value, not errors:
                RETURN_FALSE (80)
                    Indicate the program did not have error, nor failed,
                    just not doing what you might hope it to do.
                    For example, zanata-release-notes-prepend returns RETURN_FALSE
                    when the version-name exists, but no issues.
    """
    OK = 0
    FATAL_UNSPECIFIED = 1
    FATAL_FAIL = 3
    FATAL_INVALID_OPTIONS = 4
    FATAL_INVALID_ARGUMENTS = 5
    FATAL_MISSING_DEPENDENCY = 6

    ERROR_FAIL = 40
    ERROR_CANNOT_READ = 41
    ERROR_INVALID_FORMAT = 42

    RETURN_FALSE = 80


class NoSuchMethodError(Exception):
    """Method does not exist

    Args:
        method_name (str): Name of the method
    """

    def __init__(self, method_name):
        super(NoSuchMethodError, self).__init__()
        self.method_name = method_name

    def __str__(self):
        return "No such method: %s" % self.method_name


class ColoredLogHandler(logging.StreamHandler):
    bg = os.getenv("LOGGING_BG_COLOR", 'black')  # Default black background

    COLOR_MAPPING = {
            'DEBUG': [os.getenv("LOGGING_DEBUG_COLOR", 'white'), bg],  # white
            'INFO': [os.getenv("LOGGING_INFO_COLOR", 'cyan'), bg],  # cyan
            'WARNING': [os.getenv("LOGGING_WARNING_COLOR", 'yellow'), bg],  # yellow
            'ERROR': [os.getenv("LOGGING_ERROR_COLOR", 'red'), bg],  # red
            'CRITICAL': ['white', 'red']}  # white on red bg

    def __init__(self, stream=None, level=logging.NOTSET):
        super(ColoredLogHandler, self).__init__(stream)

    def emit_windows(self, record):
        import ctypes
        FOREGROUND_COLOR = {
            'black'  : 0x0000,
            'blue'   : 0x0001,
            'green'  : 0x0002,
            'red'    : 0x0004,
            'cyan'   : 0x0003,
            'megenta': 0x0005,
            'yellow' : 0x0006,
            'white'  : 0x000f}

        BACKGROUND_COLOR = {
            'black'  : 0x0000,
            'blue'   : 0x0010,
            'green'  : 0x0020,
            'red'    : 0x0040,
            'cyan'   : 0x0030,
            'megenta': 0x0050,
            'yellow' : 0x0060,
            'white'  : 0x00f0}

        # winbase.h
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        # add methods we need to the class
        def _set_color(code):
            import ctypes
            # Constants from the Windows API
            # self.STD_OUTPUT_HANDLE = -11
            hdl = ctypes.windll.kernel32.GetStdHandle(STD_ERROR_HANDLE)
            ctypes.windll.kernel32.SetConsoleTextAttribute(hdl, code)

        def _set_level_color(level):
            fg_color, bg_color = ColoredLogHandler.COLOR_MAPPING[level]
            code = FOREGROUND_COLOR[fg_color] | BACKGROUND_COLOR[bg_color]
            _set_color(code)

        _set_level_color(record.levelname)
        super(ColoredLogHandler, self).emit(record)
        _set_level_color('DEBUG')

    def emit_ansi(self, record):
        # add methods we need to the class
        FOREGROUND_COLOR = {
            'black'  : 30,
            'blue'   : 34,
            'green'  : 32,
            'red'    : 31,
            'cyan'   : 36,
            'megenta': 35,
            'yellow' : 33,
            'white'  : 37}

        BACKGROUND_COLOR = {
            'black'  : 40,
            'blue'   : 44,
            'green'  : 42,
            'red'    : 41,
            'cyan'   : 46,
            'megenta': 45,
            'yellow' : 43,
            'white'  : 47}

        def _color(fg_code, bg_code, content):
            if os.getenv('LOGGING_NO_COLOR', '0') != '0':
                return content
            return "\033[%d;%dm%s\033[0m" % (fg_code, bg_code, content)

        fg_color, bg_color = ColoredLogHandler.COLOR_MAPPING[record.levelname]
        try:
            msg = _color(
                    FOREGROUND_COLOR[fg_color],
                    BACKGROUND_COLOR[bg_color],
                    self.format(record))
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


    def emit(self, record):
        if platform.system() == 'Windows':
            self.emit_windows(record)
        else:
            self.emit_ansi(record)


class GenericArgParser(ArgumentParser):
    """Zanata Argument Parser that support sub-commands and environment

    Examples:
    >>> import GenericArgParser
    >>> parser = GenericArgParser.GenericArgParser('my-prog')
    >>> parser.add_common_argument('-b', '--branch', default='master')
    >>> parser.add_sub_command('list', None, None)
    >>> args = parser.parse_all(['list', '-b', 'release'])
    >>> print(args.sub_command)
    list
    >>> print(args.branch)
    release
    >>> args2 = parser.parse_all(['list'])
    >>> print(args2.branch)
    master
    """

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None
        # Ignore mypy "ArgumentParser" gets multiple values for keyword
        # argument "formatter_class"
        # See https://github.com/python/mypy/issues/1028
        super(GenericArgParser, self).__init__(
                *args, formatter_class=RawDescriptionHelpFormatter, **kwargs)
        self.env_def = {}  # type: Dict[str, dict]
        self.parent_parser = ArgumentParser(add_help=False)
        self.add_argument(
                '-v', '--verbose', type=str, default='INFO',
                metavar='VERBOSE_LEVEL',
                help='Valid values: %s'
                % 'DEBUG, INFO, WARNING, ERROR, CRITICAL, NONE')

        self.sub_parsers = None  # type: _SubParsersAction
        self.sub_command_obj_dict = {}  # type: Dict[str, Any]
        self.logger = None

    def add_common_argument(self, *args, **kwargs):
        # type:  (Any, Any) -> None
        """Add a common argument that will be used in all sub commands
        In other words, common argument will be put in common parser.
        Note that add_common_argument must be put in then front of
        add_sub_command that uses common arguments."""
        self.parent_parser.add_argument(*args, **kwargs)

    def add_sub_command(self, name, arguments, obj=None, **kwargs):
        # type:  (str, List, Any, Any) -> None
        """Add a sub command

        Args:
            name (str): name of the sub-command
            arguments (dict): argments to be passed to argparse.add_argument()
            obj (Any, optional): Defaults to None. The sub_command is
                a method of the obj.
            kwargs (Any, optional): other arguments for add_parser
        """
        if not self.sub_parsers:
            self.sub_parsers = self.add_subparsers(
                    title='Command', description='Valid commands',
                    help='Command help')

        if obj:
            self.sub_command_obj_dict[name] = obj

        if 'parents' in kwargs:
            kwargs['parents'] += [self.parent_parser]
        else:
            kwargs['parents'] = [self.parent_parser]

        anonymous_parser = self.sub_parsers.add_parser(
                name, **kwargs)
        if arguments:
            for arg in arguments:
                k = arg[0]
                v = arg[1]
                if v:
                    anonymous_parser.add_argument(*k.split(), **v)
                else:
                    anonymous_parser.add_argument(*k.split())
        anonymous_parser.set_defaults(sub_command=name)

    def add_env(# pylint: disable=too-many-arguments
            self, env_name,
            default=None,
            required=False,
            value_type=str,
            dest=None,
            sub_commands=None):
        # type: (str, object, bool, type, str, List[str]) -> None
        """Add environment variable
            env_name: Environment variable name
            default: Default value
            value_type: type of value e.g. str
            dest: attribute name to be return by parse_*
            sub_commands: List of subcommands that use this environment"""
        if not dest:
            dest = env_name.lower()
        if env_name in self.env_def:
            raise ArgumentError(
                    None, "Duplicate environment name %s" % env_name)
        self.env_def[env_name] = {
                'default': default,
                'required': required,
                'value_type': value_type,
                'dest': dest,
                'sub_commands': sub_commands}

    def add_methods_as_sub_commands(self, obj, name_pattern='.*'):
        # type (Any, str) -> None
        """Add public methods as sub-commands

        Args:
            cls ([type]): Public methods of obj will be used
            name_pattern (str, optional): Defaults to '.*'.
                    Method name should match the pattern.
        """
        method_list = inspect.getmembers(obj)
        for m in method_list:
            if not re.match(name_pattern, m[0]):
                continue

            name = m[0]
            m_obj = m[1]

            if name[0] == '_':
                # No private functions (which start with _)
                continue

            if not inspect.ismethod(m_obj) and not inspect.isfunction(m_obj):
                continue

            if name == 'init_from_parsed_args':
                # init_from_parsed_args initialize from parsed args.
                # No need to be in sub-commands
                continue

            argspec = inspect.getargspec(m_obj)
            sub_args = None
            try:
                start_idx = len(argspec.args) - len(argspec.defaults)
            except TypeError:
                start_idx = len(argspec.args) + 1
            for idx, a in enumerate(argspec.args):
                if a == 'self' or a == 'cls':
                    continue
                if argspec.defaults and idx >= start_idx:
                    arg_def = {
                            'nargs': '?',
                            'default': argspec.defaults[idx - start_idx]}
                else:
                    arg_def = None
                if sub_args:
                    sub_args.append(tuple([a, arg_def]))
                else:
                    sub_args = [tuple([a, arg_def])]

            self.add_sub_command(
                    name,
                    sub_args,
                    obj,
                    help=re.sub(
                            "\n.*$", "", m_obj.__doc__, flags=re.MULTILINE),
                    description=m_obj.__doc__)

    def has_common_argument(self, option_string=None, dest=None):
        # type: (str, str) -> bool
        """Has the parser defined this argument as a common argument?
           Either specify option_string or dest
           option_string: option in command line. e.g. -i
           dest: attribute name to be return by parse_*"""
        for action in self.parent_parser._actions:  # pylint: disable=W0212
            if option_string:
                if option_string in action.option_strings:
                    return True
                else:
                    continue
            elif dest:
                if dest == action.dest:
                    return True
                else:
                    continue
            else:
                raise ArgumentError(None, "need either option_string or dest")
        return False

    def has_env(self, env_name):
        # type: (str) -> bool
        """Whether this parser parses this environment"""
        return env_name in self.env_def

    def set_logger(self, verbose='INFO', name=None):
        # type: (str) -> None
        """Handle logger
        Inspired from KurtJacobson's colored_log.py"""
        self.logger = logging.getLogger(name)
        # Add console handler

        c_handler = ColoredLogHandler()
        c_formatter = logging.Formatter(
                '%(asctime)-15s [%(levelname)s] %(message)s')
        c_handler.setFormatter(c_formatter)
        self.logger.addHandler(c_handler)
        if verbose == 'NONE':
            # Not showing any log
            self.logger.setLevel(logging.CRITICAL + 1)
        elif hasattr(logging, verbose):
            self.logger.setLevel(getattr(logging, verbose))
        else:
            ArgumentError(None, "Invalid verbose level: %s" % verbose)

    def parse_args(self, args=None, namespace=None):
        # type: (Any, Any) -> Namespace
        """Parse arguments"""
        result = super(GenericArgParser, self).parse_args(args, namespace)
        self.set_logger(result.verbose)

        # We do not need verbose for the caller
        delattr(result, 'verbose')
        return result

    @staticmethod
    def _is_env_valid(env_name, env_value, env_data, args):
        # type (str, str, dict, argparse.Namespace) -> bool
        """The invalid env should be skipped or raise error"""
        # Skip when the env is NOT in the list of supported sub-commands
        if env_data['sub_commands'] and args and hasattr(args, 'sub_command'):
            if args.sub_command not in env_data['sub_commands']:
                return False

        # Check whether the env_value is valid
        if not env_value:
            if env_data['required']:
                # missing required value
                raise AssertionError("Missing environment '%s'" % env_name)
            elif not env_data['default']:
                # no default value
                return False
        return True

    def parse_env(self, args=None):
        # type: (Namespace) -> dict
        """Parse environment"""
        result = {}
        for env_name in self.env_def:
            env_data = self.env_def[env_name]
            env_value = os.environ.get(env_name)
            try:
                if not GenericArgParser._is_env_valid(
                        env_name, env_value, env_data, args):
                    continue
            except AssertionError as e:
                raise e
            if not env_value:
                if env_data['required']:
                    raise AssertionError("Missing environment '%s'" % env_name)
                elif not env_data['default']:
                    continue
                else:
                    env_value = env_data['default']
            result[env_data['dest']] = env_value
        return result

    def parse_all(self, args=None, namespace=None):
        # type: (List, Namespace) -> Namespace
        """Parse arguments and environment"""
        result = self.parse_args(args, namespace)
        env_dict = self.parse_env(result)
        for k, v in env_dict.iteritems():  # pylint: disable=no-member
            setattr(result, k, v)
        return result

    def run_sub_command(self, args=None):
        """Run the sub ccommand with parsed arguments

        Args:
            instance ([type]): [description]
            args ([type], optional): Defaults to None. Arguments

        Raises:
            ArgumentError: When sub_command is missing
        """
        if not args.sub_command:
            raise ArgumentError(args, "Missing sub-command")

        if args.sub_command not in self.sub_command_obj_dict:
            raise ArgumentError(
                    args,
                    "sub-command %s is not associated with any object" %
                    args.sub_command)
        obj = self.sub_command_obj_dict[args.sub_command]
        if inspect.isclass(obj):
            cls = obj
            if not hasattr(cls, 'init_from_parsed_args'):
                raise NoSuchMethodError('init_from_parsed_args')
            # New an object accordingto args
            obj = getattr(cls, 'init_from_parsed_args')(args)

        sub_cmd_obj = getattr(obj, args.sub_command)
        argspec = inspect.getargspec(sub_cmd_obj)
        arg_values = []
        for a in argspec.args:
            if a == 'self' or a == 'cls':
                continue
            arg_values.append(getattr(args, a))
        return sub_cmd_obj(*arg_values)




if __name__ == '__main__':
    if os.getenv("PY_DOCTEST", "0") == "1":
        import doctest
        test_result = doctest.testmod()
        print(doctest.testmod(), file=sys.stderr)
        sys.exit(0 if test_result.failed == 0 else 1)
    print("Legend of log levels", file=sys.stderr)
    GenericArgParser('parser').parse_args(["-v", "DEBUG"])
    logging.debug("debug")
    logging.info("info")
    logging.warning("warning")
    logging.error("error")
    logging.critical("critical")
