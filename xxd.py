#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO:
# Replace
#     `#!/usr/bin/env python3`
# with
#     `#!/usr/bin/env -S python3 -OO`
# to disable asserts (asserts are for development only)

import optparse
import os
import sys
import typing
from contextlib import contextmanager
from pathlib import Path
from pprint import pp

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


# Config
# ========================================
class Config(typing.TypedDict):
    revert: bool
    infile: typing.BinaryIO | Path
    outfile: typing.TextIO | Path
    is_infile_path: bool
    is_outfile_path: bool


# Stuff
# ========================================
class NoSuchFileException(Exception):
    def __init__(self, *args: object, message: str | None = None):
        super().__init__(*args)
        self.message = message


def convert(b: bytes):
    pass


def revert(s: str):
    pass


def route_dehex(config: Config):
    pass


def check_args(args: list):
    # length = len(args)
    pass


def get_config(opts: optparse.Values, args) -> Config:
    config: Config = {
        "revert": False,
        "infile": sys.stdin.buffer,
        "outfile": sys.stdout,
        "is_infile_path": False,
        "is_outfile_path": False,
    }

    if opts.revert:
        config["revert"] = True

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


def mid_buffer_width(c: int, g: int):
    """
    Numbers after `+` is whitespace column count
    """
    if g == 0 or c <= g:
        return 2 * c
    elif g == 1:
        return 2 * c + c - 1
    elif c % g == 0:
        return 2 * c + c // g - 1
    else:
        return 2 * c + c // g


def route_hex(config: Config):
    print("t1")

    CONFIG_COLS = 16
    CONFIG_GROUPSIZE = 2
    MID_SEC_WIDTH = mid_buffer_width(CONFIG_COLS, CONFIG_GROUPSIZE)
    RIGHT_SEC_WIDTH = CONFIG_COLS

    mid_buffer = [" "] * MID_SEC_WIDTH
    mid_index = 0

    right_buffer = [" "] * RIGHT_SEC_WIDTH
    right_index = 0

    groups = 0

    with (
        writer_opened(config) as writer,
        reader_opened(config) as reader,
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


@contextmanager
def reader_opened(config: Config):
    infile = config["infile"]

    if config["is_infile_path"]:
        assert isinstance(infile, Path)
        with open(infile, "rb") as reader:
            yield reader
    else:
        assert not isinstance(infile, Path)
        yield infile


@contextmanager
def writer_opened(config: Config):
    outfile = config["outfile"]

    if config["is_outfile_path"]:
        assert isinstance(outfile, Path)
        with open(outfile, "w") as reader:
            yield reader
    else:
        assert not isinstance(outfile, Path)
        yield outfile


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
        print("Config:")
        pp(config)
        print()
        if config["revert"]:
            # route_dehex(config)
            pass
        else:
            route_hex(config)

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
