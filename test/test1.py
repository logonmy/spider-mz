import os
from configparser import ConfigParser


cfg = ConfigParser()
cfg.read('../config/config.ini')





# print(cfg.sections())

print(type(list(cfg.get('kafka','bootstrap_servers'))))

print(cfg.get('file_path','write_file_path1'))


print(os.path.exists('../config/config.ini'))

