import os
from dotenv import load_dotenv

WIDTH, HEIGHT = 800, 600
FPS = 60

HEX_W = 30
HEX_H = 30

HEX_COLOR = (30, 30, 30)

ENTITY_COLOR = (46, 204, 113)

OFFSET = (WIDTH/2, HEIGHT/2)

load_dotenv()
DEBUG = os.getenv("DEBUG", "False") == "True"