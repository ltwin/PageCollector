import os
import sys

sys.path.append('spiders')


spiders = []
for item in os.listdir('spiders'):
    if os.path.isfile(item):
        package = __import__(os.path.splitext(item)[0])
        for attr in dir(package):
            obj = getattr(package, attr)
            try:
                obj_name = obj.__base__.__name__
            except AttributeError:
                continue
            if obj_name == '_Spider':
                spiders.append(obj)
print(spiders)
