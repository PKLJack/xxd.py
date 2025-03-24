"""
Usage:
python3 -m unittest
"""

import io
import sys
import unittest
from optparse import Values
from pathlib import Path

import xxd


class TestSanity(unittest.TestCase):
    def test_sanity(self):
        self.assertTrue(True)


class TestParserOptsArgs(unittest.TestCase):

    def test_empty(self):
        sys_argv = []

        result = xxd.parser.parse_args(sys_argv)
        expected = (Values({"revert": False}), [])

        self.assertEqual(result, expected)

    def test_revert_short(self):
        sys_argv = ["-r"]

        result = xxd.parser.parse_args(sys_argv)
        expected = (Values({"revert": True}), [])

        self.assertEqual(result, expected)

    def test_revert_long(self):
        sys_argv = ["--revert"]

        result = xxd.parser.parse_args(sys_argv)
        expected = (Values({"revert": True}), [])

        self.assertEqual(result, expected)

    def test_infile(self):
        sys_argv = ["infile.txt"]

        result = xxd.parser.parse_args(sys_argv)
        expected = (Values({"revert": False}), ["infile.txt"])

        self.assertEqual(result, expected)

    def test_infile_outfile(self):
        sys_argv = ["infile.txt", "outfile.txt"]

        result = xxd.parser.parse_args(sys_argv)
        expected = (Values({"revert": False}), ["infile.txt", "outfile.txt"])

        self.assertEqual(result, expected)


class TestGetConfig(unittest.TestCase):

    def test_empty(self):
        opts, args = xxd.parser.parse_args([])
        result = xxd.get_config(opts, args)
        expected: xxd.Config = {
            "revert": False,
            "infile": sys.stdin.buffer,
            "outfile": sys.stdout,
            "is_infile_path": False,
            "is_outfile_path": False,
        }

        self.assertEqual(result, expected)

    def test_1_file(self):
        opts, args = xxd.parser.parse_args(["tests/files/en.txt"])
        result = xxd.get_config(opts, args)
        expected: xxd.Config = {
            "revert": False,
            "infile": Path("tests/files/en.txt").resolve(),
            "outfile": sys.stdout,
            "is_infile_path": True,
            "is_outfile_path": False,
        }

        self.assertEqual(result, expected)

    def test_2_file(self):
        opts, args = xxd.parser.parse_args(
            [
                "tests/files/en.txt",
                "output.txt",
            ]
        )
        result = xxd.get_config(opts, args)
        expected: xxd.Config = {
            "revert": False,
            "infile": Path("tests/files/en.txt").resolve(),
            "outfile": Path("output.txt").resolve(),
            "is_infile_path": True,
            "is_outfile_path": True,
        }

        self.assertEqual(result, expected)

    def test_1_arg_1_bad(self):
        opts, args = xxd.parser.parse_args(["badfile"])

        with self.assertRaises(xxd.NoSuchFileException):
            xxd.get_config(opts, args)

    def test_2_args_1_bad(self):
        # outfile will be created
        opts, args = xxd.parser.parse_args(["badfile", "does not matter"])

        with self.assertRaises(xxd.NoSuchFileException):
            xxd.get_config(opts, args)


class TestHexStuff(unittest.TestCase):

    def test_bytes_to_str(self):
        bytes1 = "Hello\n".encode()
        s1 = "".join(f"{x:02x}" for x in bytes1)

        expected = "48656c6c6f0a"

        self.assertEqual(s1, expected)

    def test_str_to_bytes_1(self):
        s1 = "48656c6c6f0a"
        b1 = bytes.fromhex(s1)
        s2 = b1.decode()

        expected = "Hello\n"

        self.assertEqual(s2, expected)

    def test_str_to_bytes_2(self):
        s1 = "48 65 6c 6c 6f 0a"
        b1 = bytes.fromhex(s1)
        s2 = b1.decode()

        expected = "Hello\n"

        self.assertEqual(s2, expected)

    def test_str_to_bytes_3(self):
        s1 = "4865 6c6c 6f0a"
        b1 = bytes.fromhex(s1)
        s2 = b1.decode()

        expected = "Hello\n"

        self.assertEqual(s2, expected)

    def test_str_to_bytes_4(self):
        s1 = "e4b8 96e7 958c e4b8 96e7 958c 0a"
        b1 = bytes.fromhex(s1)
        s2 = b1.decode()

        expected = "世界世界\n"

        self.assertEqual(s2, expected)

    def test_str_to_bytes_5(self):
        s1 = "e3 8293 e382 93e3 8293 0a"
        b1 = bytes.fromhex(s1)
        s2 = b1.decode()

        expected = "んんん\n"

        self.assertEqual(s2, expected)


class TestRouteHex(unittest.TestCase):
    def test_en(self):
        out = io.StringIO()
        config: xxd.Config = {
            "revert": False,
            "infile": io.BytesIO("Hello World.\nHello World Again.\n".encode()),
            "outfile": out,
            "is_infile_path": False,
            "is_outfile_path": False,
        }
        xxd.hexdump_route(config)
        result = out.getvalue()

        expected = (
            ""
            + "00000000: 4865 6c6c 6f20 576f 726c 642e 0a48 656c  Hello.World..Hel"
            + "\n"
            + "00000010: 6c6f 2057 6f72 6c64 2041 6761 696e 2e0a  lo.World.Again.."
            + "\n"
        )

        self.assertEqual(result, expected)

    def test_cjk(self):
        out = io.StringIO()
        config: xxd.Config = {
            "revert": False,
            "infile": io.BytesIO("世界世界\nんんん\n".encode()),
            "outfile": out,
            "is_infile_path": False,
            "is_outfile_path": False,
        }
        xxd.hexdump_route(config)
        result = out.getvalue()

        expected = (
            ""
            + "00000000: e4b8 96e7 958c e4b8 96e7 958c 0ae3 8293  ................"
            + "\n"
            + "00000010: e382 93e3 8293 0a                        .......         "
            + "\n"
            # NOTE:
            # In this implementation, the end of the line will be
            # padded with spaces
        )

        self.assertEqual(result, expected)


class TestRouteRevert(unittest.TestCase):
    def test_in_file_1(self):
        fp = Path(__file__).parent / "files" / "en.txt.xxd"
        in_stream = fp
        out_stream = io.BytesIO()

        config: xxd.Config = {
            "revert": True,
            "infile": in_stream,
            "outfile": out_stream,
            "is_infile_path": isinstance(in_stream, Path),
            "is_outfile_path": isinstance(out_stream, Path),
        }

        xxd.revert_route(config)
        result = out_stream.getvalue()

        expected = (Path(__file__).parent / "files" / "en.txt").read_bytes()

        self.assertEqual(type(result), type(expected))
        self.assertEqual(result, expected)

    def test_in_file_2(self):
        fp = Path(__file__).parent / "files" / "cjk.txt.xxd"
        in_stream = fp
        out_stream = io.BytesIO()

        config: xxd.Config = {
            "revert": True,
            "infile": in_stream,
            "outfile": out_stream,
            "is_infile_path": isinstance(in_stream, Path),
            "is_outfile_path": isinstance(out_stream, Path),
        }

        xxd.revert_route(config)
        result = out_stream.getvalue()

        expected = (Path(__file__).parent / "files" / "cjk.txt").read_bytes()

        self.assertEqual(type(result), type(expected))
        self.assertEqual(result, expected)

    def test_in_stringio(self):
        fp = Path(__file__).parent / "files" / "en.txt.xxd"
        in_stream = io.StringIO(fp.read_text())
        out_stream = io.BytesIO()

        config: xxd.Config = {
            "revert": True,
            "infile": in_stream,
            "outfile": out_stream,
            "is_infile_path": isinstance(in_stream, Path),
            "is_outfile_path": isinstance(out_stream, Path),
        }

        xxd.revert_route(config)
        result = out_stream.getvalue()

        expected = (Path(__file__).parent / "files" / "en.txt").read_bytes()

        self.assertEqual(type(result), type(expected))
        self.assertEqual(result, expected)


class TestUtils(unittest.TestCase):
    def test1(self):
        s0 = "00000010: e382 93e3 8293 0a                        .......         "

        s1, s2, s3 = xxd.revert_parse_line(s0)

        self.assertEqual(s1, "00000010")
        self.assertEqual(s2, "e382 93e3 8293 0a")
        self.assertEqual(s3, ".......")


if __name__ == "__main__":
    unittest.main()
