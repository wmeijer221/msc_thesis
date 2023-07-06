


import tempfile
import shutil

with tempfile.NamedTemporaryFile('w+', delete=False) as tmp:
    tmp.write("hello world\n")
    tmp.writelines([str(i) for i in range(10)])


shutil.move(tmp.name, "./real_temp.dat")

