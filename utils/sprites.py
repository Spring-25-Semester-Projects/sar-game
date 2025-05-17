import pygame

class SpriteSheet:
    """Utility class for handling sprite sheets"""
    def __init__(self, image):
        self.sheet = image
        
    def get_img(self, frame, width, height, scale, color):
        """Extract a single image from a sprite sheet"""
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), (0, (frame * height), width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(color)
        return image

def load_sprite_sheet(path, frame_count, frame_size, scale=1, colorkey=(0, 0, 0)):
    """Helper function to load and prepare a sprite sheet"""
    sheet_img = pygame.image.load(path).convert_alpha()
    sheet = SpriteSheet(sheet_img)
    return [sheet.get_img(i, *frame_size, scale, colorkey) for i in range(frame_count)]