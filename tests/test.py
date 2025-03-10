import sys
import types
from pathlib import Path
from pprint import pp

sys.path.insert(0, str(Path().resolve()))

pp(sys.path)
# pp(sys.meta_path)

import xxd

print(xxd)
print(xxd.__spec__)
print(type(xxd))
print(dir(xxd))

# xxd.main()

print("This is test.py")
