import os

stream = os.popen("jupyter notebook list")
print(stream.read())