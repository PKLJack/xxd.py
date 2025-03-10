# `xxd.py`

An exercise of writing `xxd` in Python.

## Usage

```sh
chmod u+x xxd.py

## From standard input
echo "Hello" | xxd.py

## From a file
./xxd.py infile.txt
./xxd.py infile.txt outfile.txt
```

Testing
```sh
./xxd.py
./xxd.py ./tests/files/en.txt
./xxd.py ./tests/files/cjk.txt

cat ./tests/files/cjk.txt | ./xxd.py
cat ./tests/files/en.txt |  ./xxd.py
```
