import os
import numpy as np
from dotenv import load_dotenv

WIDTH, HEIGHT = 1400, 800
FPS = 60

HEX_COLOR = (50, 50, 50)

ENTITY_COLOR = (46, 204, 113)

COST_COLORS = [(220, 20, 60), (178, 34, 34), (205, 92, 92), (255, 99, 71), (139, 0, 0), (240, 128, 128), (93, 58, 102)]

OFFSET = np.array([WIDTH/2, HEIGHT/2])

SIZE = 13


CONST_RESCUER_SPRITE_PATH = "sar-game-8-field-of-view/assets/Females/F_03.png"


load_dotenv()
DEBUG = os.getenv("DEBUG")
