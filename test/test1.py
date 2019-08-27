
from configparser import ConfigParser


cfg = ConfigParser()
cfg.read('../config/config.ini')





print(cfg.sections())

print(cfg.get('kafka','library'))