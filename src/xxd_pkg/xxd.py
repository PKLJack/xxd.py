#!/usr/bin/env -S python3 -OO
# -*- coding: utf-8 -*-

# NOTE:
# To enable assertions:
# - Execute this file as `python3 ./xxd.py` instead of `./xxd.py`
# - Remove `-OO` from the shebang line

import optparse
import os
import re
import sys
import typing
from contextlib import contextmanager
from pathlib import Path

PROGRAM_NAME = "xxd.py"

# Parser
# ========================================
usage = "usage: %prog [options] [infile [outfile]]"
description = "xxd.py creates a hex dump of a given file or standard input."

parser = optparse.OptionParser(usage, description=description)
parser.add_option(
    "-r",
    "--revert",
    default=False,
    action="store_true",
    help="Reverse operation: convert hexdump into binary",
)


# Class
# ========================================
class Config(typing.TypedDict):
    revert: bool
    infile: typing.IO | Path
    outfile: typing.IO | Path
    is_infile_path: bool
    is_outfile_path: bool


class NoSuchFileException(Exception):
    def __init__(self, *args: object, message: str | None = None):
        super().__init__(*args)
        self.message = message


# Functions
# ========================================
def get_config(opts: optparse.Values, args) -> Config:
    config: Config = {
        "revert": opts.revert,
        "infile": sys.stdin if opts.revert else sys.stdin.buffer,
        "outfile": sys.stdout.buffer if opts.revert else sys.stdout,
        "is_infile_path": False,
        "is_outfile_path": False,
    }

    args_count = len(args)

    # TODO: maybe put this elsewhere
    if args_count > 2:
        parser.print_help()
        sys.exit(1)

    if args_count >= 1:
        fp = Path(args[0]).resolve()
        if not fp.exists():
            raise NoSuchFileException(
                message=f"{PROGRAM_NAME}: {args[0]}: No such file or directory"
            )
        config["infile"] = fp
        config["is_infile_path"] = True

    if args_count == 2:
        # out file will be created / overwitten
        config["outfile"] = Path(args[1]).resolve()
        config["is_outfile_path"] = True

    return config


@contextmanager
def opened_stream(obj: typing.IO | Path, is_path: bool, mode: str):
    assert mode in ("r", "wb", "rb", "w")

    if is_path:
        assert isinstance(obj, Path)
        with open(obj, mode) as handler:
            yield handler
    else:
        assert not isinstance(obj, Path)
        yield obj


def revert_route(config: Config):
    with (
        opened_stream(config["infile"], config["is_infile_path"], "r") as reader,
        opened_stream(config["outfile"], config["is_outfile_path"], "wb") as writer,
    ):
        for line in reader.readlines():
            _, s2, _ = revert_parse_line(line)

            assert isinstance(s2, str)

            writer.write(bytes.fromhex(s2))


def revert_parse_line(line: str):
    """
    Parse line for revert mode.
    """
    # NOTE:
    # Only handles "NNNNNNNN: XXXX XXXX ... XXXX  CCC...\n"
    #                       ^^                  ^^+

    s1, rest = line.split(": ")

    # TODO: compile pattern somewhere once only
    s2, s3, *_ = re.split(r"\s{2,}", rest)

    return s1, s2, s3


def hexdump_route(config: Config):
    CONFIG_COLS = 16
    CONFIG_GROUPSIZE = 2
    MID_SEC_WIDTH = hexdump_mid_buffer_width(CONFIG_COLS, CONFIG_GROUPSIZE)
    RIGHT_SEC_WIDTH = CONFIG_COLS

    mid_buffer = [" "] * MID_SEC_WIDTH
    mid_index = 0

    right_buffer = [" "] * RIGHT_SEC_WIDTH
    right_index = 0

    groups = 0

    with (
        opened_stream(config["infile"], config["is_infile_path"], "rb") as reader,
        opened_stream(config["outfile"], config["is_outfile_path"], "w") as writer,
    ):

        for i, v in enumerate(reader.read()):

            # Left Section
            if i % CONFIG_COLS == 0:
                writer.write(f"{i:08x}: ")

            # Mid Section
            mid_buffer[mid_index], mid_buffer[mid_index + 1] = f"{v:02x}"
            mid_index += 2
            groups += 1

            if groups == CONFIG_GROUPSIZE:
                groups = 0

                if mid_index < MID_SEC_WIDTH:
                    mid_buffer[mid_index] = " "
                    mid_index += 1

            # Right Section
            # See ASCII Table 33: `!` 126: `~`
            right_buffer[right_index] = chr(v) if 33 <= v <= 126 else "."
            right_index += 1

            # Buffers full
            if right_index == RIGHT_SEC_WIDTH:
                writer.write("".join(mid_buffer) + "  " + "".join(right_buffer) + "\n")

                # Reset
                mid_index = 0
                right_index = 0
                groups = 0

        # Remaining buffer content
        if right_index != 0:
            # Empty outdated elements

            for j in range(mid_index, MID_SEC_WIDTH):
                mid_buffer[j] = " "
            for j in range(right_index, RIGHT_SEC_WIDTH):
                right_buffer[j] = " "

            writer.write("".join(mid_buffer) + "  " + "".join(right_buffer) + "\n")


def hexdump_mid_buffer_width(c: int, g: int):
    """
    For hexdump mode.
    Calculates width for mid section.
    """
    # Numbers after `+` is whitespace column count
    if g == 0 or c <= g:
        return 2 * c
    elif g == 1:
        return 2 * c + c - 1
    elif c % g == 0:
        return 2 * c + c // g - 1
    else:
        return 2 * c + c // g


# Main
# ========================================
def main():
    opts, args = parser.parse_args()

    try:
        config = get_config(opts, args)
    except NoSuchFileException as e:
        print(e.message, file=sys.stderr)
        sys.exit(2)

    try:
        if config["revert"]:
            revert_route(config)
        else:
            hexdump_route(config)

        sys.stdout.flush()
    except BrokenPipeError:
        # See: https://docs.python.org/3/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)  # Not needed?
        sys.exit(0)

    pass


if __name__ == "__main__":
    main()
