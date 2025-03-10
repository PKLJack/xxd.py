#!/usr/bin/env python3

import os
import sys
import typing
from pathlib import Path

PROGRAM_NAME = "xxd.py"


# Classes
# ========================================
# NOTE: Might not need a class
class Config:
    def __init__(self) -> None:
        self.infile = sys.stdin.buffer
        self.outfile = sys.stdout
        self._cols = 16  # Min: 1  Max: 256

        # Separate  the  output  of  every <bytes> bytes by a whitespace.
        self._groupsize = 2

        # NOTE: Not implemented
        self.uppercase = False
        self.help = False
        self.len = False  # Stop after writing <len> octets.

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            "("
            f"infile={self.infile!r}, "
            f"outfile={self.outfile!r}, "
            f"cols={self.cols!r}, "
            f"groupsize={self.groupsize!r}"
            ")"
        )

    @property
    def cols(self):
        return self._cols

    @cols.setter
    def cols(self, v: int):
        if not (1 <= v <= 256):
            print("Cols must be between 1 and 256")
            sys.exit(1)
        self._cols = v

    @property
    def groupsize(self):
        return self._groupsize

    @groupsize.setter
    def groupsize(self, v: int):
        if not (0 <= v <= 256):
            print("Groupsize must be between 0 and 256")
            sys.exit(1)
        self._groupsize = v


config = Config()


# Functions
# ========================================
def parse_sys_argv():
    """
    Parse cli, update config.
    """

    i = 1
    N = len(sys.argv)

    while i < N:
        v = sys.argv[i]

        # Help
        if v == "-h" or v == "--help":
            print("Print Help")
            sys.exit()

        # Optional Arguments
        if v == "-c" or v == "--cols":
            i += 1
            config.cols = int(sys.argv[i])

        if v == "-g" or v == "--groupsize":
            i += 1
            config.groupsize = int(sys.argv[i])

        # Positional Arguments
        if not v.startswith("-"):
            fp = Path(v)
            if not fp.exists():
                print(f"{PROGRAM_NAME}: {v}: No such file or directory")
                sys.exit(1)

            if config.infile is sys.stdin.buffer:
                config.infile = fp
            else:
                config.outfile = fp

        # Process next word
        i += 1


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


def read_and_write(reader: typing.BinaryIO, writer: typing.TextIO):
    """
    Process byte by byte
    """

    CONFIG_GROUPSIZE = config.groupsize
    CONFIG_COLS = config.cols

    MID_SEC_WIDTH = mid_buffer_width(CONFIG_COLS, CONFIG_GROUPSIZE)
    RIGHT_SEC_WIDTH = CONFIG_COLS

    # FUTURE: use array
    mid_buffer = [" "] * MID_SEC_WIDTH
    mid_index = 0

    right_buffer = [" "] * RIGHT_SEC_WIDTH
    right_index = 0

    groups = 0

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
        right_buffer[right_index] = c if (c := chr(v)).isprintable() else "."
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
        for j in range(mid_index, MID_SEC_WIDTH):
            mid_buffer[j] = " "  # Empty dirty elements

        for j in range(right_index, RIGHT_SEC_WIDTH):
            right_buffer[j] = " "  # Empty dirty elements

        writer.write("".join(mid_buffer) + "  " + "".join(right_buffer) + "\n")


def execute():
    reader = None
    writer = None

    try:
        if isinstance(config.infile, Path):
            reader = open(config.infile, "rb")
        else:
            reader = config.infile

        if isinstance(config.outfile, Path):
            writer = open(config.outfile, "w")
        else:
            writer = config.outfile

        read_and_write(reader, writer)

    finally:
        if reader and isinstance(config.infile, Path):
            reader.close()

        if writer and isinstance(config.outfile, Path):
            writer.close()


# Main
# ========================================
def main():
    parse_sys_argv()

    try:
        execute()
        sys.stdout.flush()
    except BrokenPipeError:
        # See: https://docs.python.org/3/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)  # Not needed?
        sys.exit(0)


if __name__ == "__main__":
    main()
