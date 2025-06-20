# `xxd.py`

An exercise of writing `xxd` in Python.

## Install

<!-- TODO: Add pipx link -->
With [`pipx`](https://pipx.pypa.io/stable/)
```sh
pipx install https://github.com/PKLJack/xxd.py
```

Direct download (more complicated)
```sh
wget https://github.com/PKLJack/xxd.py/raw/refs/heads/main/src/xxd_pkg/xxd.py
```

## Usage

```sh
xxd.py

## Script mode (Not supported in Windows)
## Optionally, put the xxd.py file in your $PATH
chmod u+x ./xxd.py
./xxd.py --help

## or
python3 ./xxd.py --help
```

Hexdump (default) mode
```sh
## From standard input
echo "Hello" | xxd.py

## From a file
xxd.py infile
xxd.py infile outfile

## Hexdump into a file
xxd.py stuff.txt stuff.txt.xxd
```

Revert mode
```sh
## Reconstruct stuff.txt
xxd.py -r stuff.txt.xxd stuff.txt

## With pipes
xxd.py stuff.txt | xxd.py -r | further-commands
```

## Development

Install
```sh
pip install -e .
```

Testing
```sh
## Run tests
python3 -m unittest

## Manual tests
xxd.py
xxd.py ./tests/files/en.txt
xxd.py ./tests/files/cjk.txt

cat ./tests/files/cjk.txt | xxd.py
cat ./tests/files/en.txt |  xxd.py
```

## To do

- Pass `-O` and `-OO` flags into `pyprject.toml` scripts
