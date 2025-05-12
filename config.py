import os
import numpy as np
from dotenv import load_dotenv

WIDTH, HEIGHT = 1400, 800
FPS = 60

HEX_COLOR = (50, 50, 50)

ENTITY_COLOR = (46, 204, 113)

OFFSET = np.array([WIDTH/2, HEIGHT/2])

SIZE = 13

load_dotenv()
DEBUG = os.getenv("DEBUG")