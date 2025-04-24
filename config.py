import os
from dotenv import load_dotenv

WIDTH, HEIGHT = 800, 600
FPS = 60

HEX_W = 10
HEX_H = 10

ENTITY_COLOR = (0,255,0)
OFFSET = (WIDTH // 2, HEIGHT // 2)
HEX_COLOR = (50, 50, 50)


load_dotenv()
DEBUG = os.getenv("DEBUG", "False") == "True"