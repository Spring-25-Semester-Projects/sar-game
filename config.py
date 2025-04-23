import os
from dotenv import load_dotenv

WIDTH, HEIGHT = 800, 600
FPS = 60

HEX_W = 10
HEX_H = 10

ENTITY_COLOR = (0,0,0)


load_dotenv()
DEBUG = os.getenv("DEBUG", "False") == "True"
