import os
import pygame
import random
import warnings
from PIL import Image

# Suppress the libpng warning
warnings.filterwarnings("ignore", "(?s).*iCCP: known incorrect sRGB profile.*", UserWarning)

# Initialize Pygame
pygame.init()
TILE_SIZE   = 15
DIM         = 25
IMG_FOLDER  = '.\\tiles'

# Set up display
WIDTH, HEIGHT = TILE_SIZE * DIM, TILE_SIZE * DIM

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("WFunc Tester")

def reset_grid():
    return [Cell(list(range(len(tiles)))) for _ in range(DIM * DIM)]

def load_tile_images(folder_path):
    images = []
    for i in range(13): #max 13 images total
        image_path = os.path.join(folder_path, f"{i}.png")
        if os.path.exists(image_path):
            img = pygame.image.load(image_path)
            images.append(img)
        else:
            print(f"Image #{i} not found, skipping...")
    return images

class Tile:
    def __init__(self, img, edges, index):
        self.img = img
        self.edges = edges
        self.index = index
        self.up = []
        self.right = []
        self.down = []
        self.left = []

    def analyze(self, tiles):
        for i, tile in enumerate(tiles):
            # UP
            if tile.edges[2] == self.edges[0]:
                self.up.append(i)
            # RIGHT
            if tile.edges[3] == self.edges[1]:
                self.right.append(i)
            # DOWN
            if tile.edges[0] == self.edges[2]:
                self.down.append(i)
            # LEFT
            if tile.edges[1] == self.edges[3]:
                self.left.append(i)

    def rotate(self, num):
        rotated_img = pygame.transform.rotate(self.img, 90 * num)
        rotated_edges = self.edges[-num:] + self.edges[:-num]
        return Tile(rotated_img, rotated_edges, self.index)
        
    def resize(self, size):
        self.img = pygame.transform.scale(self.img, size)

def create_tiles(resource):
    tile_images = load_tile_images(resource)
    # Top, Right, Bottom, and Left
    tiles = [
        Tile(tile_images[0],  ['AAA', 'AAA', 'AAA', 'AAA'], 1),  # Fully dark tile
        Tile(tile_images[1],  ['BBB', 'BBB', 'BBB', 'BBB'], 2),  # Fully green tile
        Tile(tile_images[2],  ['AAA', 'BCB', 'AAA', 'AAA'], 3),  # Gray right terminal
        Tile(tile_images[3],  ['BBB', 'BDB', 'BBB', 'BDB'], 4),  # Gray horizontal wire
        Tile(tile_images[4],  ['ABB', 'BCB', 'BBA', 'AAA'], 5),  # Gray horizontal converter, left dark to green
        Tile(tile_images[5],  ['BBB', 'BBB', 'BBB', 'BBB'], 6),  # Top-left dark corner
        Tile(tile_images[6],  ['BBB', 'BCB', 'BBB', 'BCB'], 7),  # Green horizontal wire
        Tile(tile_images[7],  ['BDB', 'BCB', 'BDB', 'BCB'], 8),  # Horizontal green, gray vertical intersection
        Tile(tile_images[8],  ['BDB', 'BBB', 'BCB', 'BBB'], 9),  # Vertical converter, top gray to bottom green
        Tile(tile_images[9],  ['BCB', 'BCB', 'BBB', 'BCB'], 10), # Green 3-way intersection, top
        
        Tile(tile_images[10], ['CCC', 'CCC', 'CCC', 'CCC'], 11), # Diagonal double green, top left to bottom right
        Tile(tile_images[11], ['CCC', 'AAA', 'CCC', 'AAA'], 12), # Diagonal single, right top corner
        
        Tile(tile_images[12], ['AAA', 'BCB', 'AAA', 'BCB'], 13), # Horizontal green wire
    ]
    # Create rotated versions of the tiles
    rotated_tiles = []
    for tile in tiles:
        for i in range(1, 4):
            rotated_tiles.append(tile.rotate(i))
    
    tiles.extend(rotated_tiles)
    
    return tiles

class Cell:
    def __init__(self, options):
        self.options = options
        self.collapsed = False

def check_valid(arr, valid):
    return [option for option in arr if option in valid]

def get_entropy(cell):
    return len(cell.options) if not cell.collapsed else float('inf')

def collapse(grid):
    uncollapsed = [cell for cell in grid if not cell.collapsed]
    if not uncollapsed:
        return True

    uncollapsed.sort(key=get_entropy)
    min_entropy = get_entropy(uncollapsed[0])
    min_entropy_cells = [cell for cell in uncollapsed if get_entropy(cell) == min_entropy]
    
    if not min_entropy_cells:
        return False

    cell_to_collapse = random.choice(min_entropy_cells)
    if not cell_to_collapse.options:
        return False

    cell_to_collapse.collapsed = True
    cell_to_collapse.options = [random.choice(cell_to_collapse.options)]

    return False

def propagate(grid):
    stack = list(range(len(grid)))
    while stack:
        index = stack.pop()
        current_cell = grid[index]
        x, y = index % DIM, index // DIM

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < DIM and 0 <= ny < DIM:
                neighbor_index = ny * DIM + nx
                neighbor = grid[neighbor_index]

                if not neighbor.collapsed:
                    direction = "left" if dx == 1 else "right" if dx == -1 else "up" if dy == 1 else "down"
                    valid_options = set()
                    for option in current_cell.options:
                        valid_options.update(getattr(tiles[option], direction))
                    
                    new_options = check_valid(neighbor.options, valid_options)
                    if len(new_options) < len(neighbor.options):
                        neighbor.options = new_options
                        if neighbor_index not in stack:
                            stack.append(neighbor_index)
def draw_grid(screen, grid):
    for i, cell in enumerate(grid):
        x, y = i % DIM, i // DIM
        if cell.collapsed:
            tile = tiles[cell.options[0]]
            tile.resize((TILE_SIZE, TILE_SIZE))
            screen.blit(tile.img, (x * TILE_SIZE, y * TILE_SIZE))

# Create tiles
tiles = create_tiles(IMG_FOLDER)

# Analyze tiles
for tile in tiles:
    tile.analyze(tiles)

# Initialize grid
grid = [Cell(list(range(len(tiles)))) for _ in range(DIM * DIM)]

def main():
    clock = pygame.time.Clock()
    running = True
    completed = False
    grid = reset_grid()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Reset the grid and start over
                    grid = reset_grid()
                    completed = False

        if not completed:
            completed = collapse(grid)
            propagate(grid)

        screen.fill((255, 255, 255))
        draw_grid(screen, grid)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()