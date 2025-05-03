import pygame
import random
import time
import math
import json # For saving high scores
import os   # For checking file existence

# --- Settings ---
# Difficulty level definitions
DIFFICULTIES = {
    'easy':   {'size': (9, 9),   'mines': 10},
    'medium': {'size': (16, 16), 'mines': 40},
    'hard':   {'size': (30, 16), 'mines': 99} # Standard sizes
}
DEFAULT_DIFFICULTY = 'easy'

# --- Layout & Sizing Constants ---
CELL_SIZE = 28
BORDER = 15 # Slightly larger border for spacing
TOP_BORDER_HEIGHT = 30
INFO_PANEL_HEIGHT = 60
PANEL_INTERNAL_PADDING = 8
DIFFICULTY_BUTTON_AREA_HEIGHT = 40 # Space for difficulty buttons
STATUS_AREA_HEIGHT = 30 # Space for Hint button and status text
PANEL_GRID_SPACING = 10 # Gap between elements
GRID_OUTLINE_WIDTH = 3
# Ensure these constants are defined correctly:
HINT_BUTTON_H = 26 # <--- DEFINITION
HINT_BUTTON_W = 55 # <--- DEFINITION

# Determine maximum grid dimensions for window sizing
MAX_GRID_W = DIFFICULTIES['hard']['size'][0]
MAX_GRID_H = DIFFICULTIES['hard']['size'][1]

# Calculate Fixed Window Size based on largest grid + UI elements
window_width = 2 * BORDER + MAX_GRID_W * CELL_SIZE + 2 * GRID_OUTLINE_WIDTH
window_height = TOP_BORDER_HEIGHT + INFO_PANEL_HEIGHT + DIFFICULTY_BUTTON_AREA_HEIGHT + \
                STATUS_AREA_HEIGHT + PANEL_GRID_SPACING * 2 + \
                MAX_GRID_H * CELL_SIZE + BORDER + GRID_OUTLINE_WIDTH

# --- File Constants ---
SCORE_FILENAME = "minesweeper_scores.json" # Specific filename
SOUNDS_DIRECTORY = "sounds"

# Global variables that will change based on difficulty
grid_width, grid_height = DIFFICULTIES[DEFAULT_DIFFICULTY]['size']
mine_count_setting = DIFFICULTIES[DEFAULT_DIFFICULTY]['mines']
current_difficulty_level = DEFAULT_DIFFICULTY

# --- Retro Colors ---
COLOR_BACKGROUND      = (192, 192, 192)
COLOR_WINDOW_BAR  = (0, 0, 128)
COLOR_WINDOW_BAR_TEXT = (255, 255, 255)
COLOR_BORDER_HIGHLIGHT = (255, 255, 255)
COLOR_BORDER_SHADOW  = (128, 128, 128)
COLOR_BORDER_BLACK = (0, 0, 0)
COLOR_FACE_BG    = (255, 255, 0)
COLOR_FACE_FEATURES = (0,0,0)
COLOR_ALERT_RED     = (255, 0, 0)
COLOR_FLAGPOLE = (0, 0, 0)
COLOR_FLAG_HEAD = (255, 0, 0)
COLOR_BUTTON_TEXT    = (0, 0, 0)
COLOR_HINT_BULB = (255, 255, 0)
COLOR_MINE_BODY     = (50, 50, 50) # Dark grey for mine body
COLOR_MINE_HIGHLIGHT = (150, 150, 150) # Lighter grey highlight
COLOR_DIGITAL_DISPLAY_BG = (0, 0, 0)
COLOR_DIGITAL_DISPLAY_FG = (255, 0, 0)
COLOR_STATUS_BAR_TEXT = (0, 0, 0)
COLOR_QUESTION_MARK = (0, 0, 255)
COLOR_CLOCK_FACE_BG = (220, 220, 220)
COLOR_CLOCK_HANDS = (0, 0, 0)
COLOR_CLOCK_OUTLINE = (100, 100, 100)
COLOR_BUTTON_PRESSED_BG = (210, 210, 210) # Slightly darker for pressed button

# Number colors
NUMBER_COLORS = [(0,0,0), (0,0,255), (0,128,0), (255,0,0), (0,0,128), (128,0,0), (0,128,128), (0,0,0), (128,128,128)]

pygame.init()
# --- Sound Initialization ---
pygame.mixer.init()
game_sounds = {}
def load_sound_asset(sound_name, file_name):
    global game_sounds
    file_path = os.path.join(SOUNDS_DIRECTORY, file_name)
    if os.path.exists(file_path):
        try:
            game_sounds[sound_name] = pygame.mixer.Sound(file_path)
            game_sounds[sound_name].set_volume(0.6)
            print(f"Loaded sound: {sound_name} ({file_name})")
        except pygame.error as e:
            print(f"Cannot load sound: {sound_name} from {file_path} - {e}")
            game_sounds[sound_name] = None
    else:
        print(f"Sound file not found: {file_path}")
        game_sounds[sound_name] = None

load_sound_asset('click', 'click.wav')
load_sound_asset('explosion', 'lose_minesweeper.wav')
load_sound_asset('win', 'win.wav')
load_sound_asset('start', 'start.wav')

def play_game_sound(sound_name):
    if sound_name in game_sounds and game_sounds[sound_name] is not None:
        try: game_sounds[sound_name].play()
        except pygame.error as e: print(f"Error playing sound {sound_name}: {e}")

# --- Font Loading ---
try:
    font_window_title = pygame.font.SysFont("MS Sans Serif", 16, bold=True)
    try: font_digital_display = pygame.font.SysFont("Digital-7 Mono", 40, bold=False)
    except: font_digital_display = pygame.font.SysFont("Consolas", 36, bold=True)
    font_grid_numbers = pygame.font.SysFont("Arial", 20, bold=True)
    font_small_ui = pygame.font.SysFont("MS Sans Serif", 14)
    font_question_mark = pygame.font.SysFont("Arial", 20, bold=True)
    font_difficulty_button = pygame.font.SysFont("MS Sans Serif", 14, bold=True)
except:
    print("Warning: Retro fonts not found, using Arial/Courier New.")
    font_window_title = pygame.font.SysFont("Arial", 16, bold=True)
    font_digital_display = pygame.font.SysFont("Courier New", 36, bold=True)
    font_grid_numbers = pygame.font.SysFont("Arial", 20, bold=True)
    font_small_ui = pygame.font.SysFont("Arial", 14)
    font_question_mark = pygame.font.SysFont("Arial", 20, bold=True)
    font_difficulty_button = pygame.font.SysFont("Arial", 14, bold=True)


main_screen = pygame.display.set_mode((window_width, window_height)) # Use calculated fixed size
pygame.display.set_caption(f"Minesweeper - {current_difficulty_level.capitalize()}") # Renamed

class Cell:
    """Represents a single cell in the Minesweeper grid."""
    def __init__(self):
        self.is_mine = False # Renamed
        self.is_revealed = False
        self.is_flagged = False
        self.is_question = False
        self.is_losing_mine = False # Renamed
        self.adjacent_mines = 0 # Renamed

# --- High Score Functions ---
high_scores_data = {}
def load_high_scores():
    """Loads high scores from the JSON file."""
    global high_scores_data
    if os.path.exists(SCORE_FILENAME): # Use correct filename
        try:
            with open(SCORE_FILENAME, 'r') as f:
                high_scores_data = json.load(f)
                for diff_level in DIFFICULTIES:
                    if diff_level not in high_scores_data:
                        high_scores_data[diff_level] = []
                print("High scores loaded.")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading scores from {SCORE_FILENAME}: {e}. Using default scores.")
            high_scores_data = {diff_level: [] for diff_level in DIFFICULTIES}
    else:
        print(f"Score file '{SCORE_FILENAME}' not found. Starting fresh.")
        high_scores_data = {diff_level: [] for diff_level in DIFFICULTIES}

def save_high_scores():
    """Saves the current high scores to the JSON file."""
    try:
        with open(SCORE_FILENAME, 'w') as f: # Use correct filename
            json.dump(high_scores_data, f, indent=4)
        print("High scores saved.")
    except IOError as e:
        print(f"Error saving scores to {SCORE_FILENAME}: {e}")

def add_new_score(difficulty, time_taken):
    """Adds a new score for the given difficulty and saves."""
    if time_taken <= 0: return
    if difficulty not in high_scores_data: high_scores_data[difficulty] = []
    current_scores = high_scores_data[difficulty]
    current_scores.append(time_taken)
    current_scores.sort()
    high_scores_data[difficulty] = current_scores[:5] # Keep top 5
    save_high_scores()

def display_high_scores():
    """Prints the high scores to the console."""
    print("\n--- HIGH SCORES ---")
    for diff_level, scores in high_scores_data.items():
        print(f"{diff_level.capitalize()}:")
        if scores:
            for i, score_time in enumerate(scores): print(f"  {i+1}. {score_time} seconds")
        else: print("  No scores yet.")
    print("-------------------\n")

# --- Game Logic ---
def generate_game_grid():
    """Generates a new grid based on current difficulty settings."""
    global grid_width, grid_height, mine_count_setting
    new_grid = [[Cell() for _ in range(grid_width)] for _ in range(grid_height)]
    mines_placed_count = 0
    while mines_placed_count < mine_count_setting:
        x_pos, y_pos = random.randrange(grid_width), random.randrange(grid_height)
        if not new_grid[y_pos][x_pos].is_mine:
            new_grid[y_pos][x_pos].is_mine = True
            mines_placed_count += 1
    # Calculate adjacent mine counts
    for y_pos in range(grid_height):
        for x_pos in range(grid_width):
            if new_grid[y_pos][x_pos].is_mine: continue
            count = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    neighbor_x, neighbor_y = x_pos + dx, y_pos + dy
                    if 0 <= neighbor_x < grid_width and 0 <= neighbor_y < grid_height and new_grid[neighbor_y][neighbor_x].is_mine:
                        count += 1
            new_grid[y_pos][x_pos].adjacent_mines = count
    return new_grid

def reveal_cell(game_grid, x, y, is_first_click=False, is_chord_action=False):
    """Reveals a cell and performs flood fill if necessary. Returns True if a mine was hit."""
    global grid_width, grid_height
    if not (0 <= x < grid_width and 0 <= y < grid_height): return False
    target_cell = game_grid[y][x]

    # Move mine on first click if hit
    if is_first_click and target_cell.is_mine:
        mine_moved = False
        safe_spots_list = []
        for ny in range(grid_height):
            for nx in range(grid_width):
                if not game_grid[ny][nx].is_mine and (nx != x or ny != y) :
                    safe_spots_list.append((nx, ny))
        if not safe_spots_list: return False
        new_mine_x, new_mine_y = random.choice(safe_spots_list)
        game_grid[new_mine_y][new_mine_x].is_mine = True
        target_cell.is_mine = False
        mine_moved = True
        if mine_moved: # Recalculate neighbors
            affected_coordinates = set()
            for dy_offset in range(-1, 2):
                for dx_offset in range(-1, 2):
                    affected_coordinates.add((x + dx_offset, y + dy_offset))
                    affected_coordinates.add((new_mine_x + dx_offset, new_mine_y + dy_offset))
            for cx_coord, cy_coord in affected_coordinates:
                 if 0 <= cx_coord < grid_width and 0 <= cy_coord < grid_height and not game_grid[cy_coord][cx_coord].is_mine:
                    neighbor_count = 0
                    for dy2_offset in range(-1, 2):
                        for dx2_offset in range(-1, 2):
                            nnx_coord, nny_coord = cx_coord + dx2_offset, cy_coord + dy2_offset
                            if 0 <= nnx_coord < grid_width and 0 <= nny_coord < grid_height and game_grid[nny_coord][nnx_coord].is_mine:
                                neighbor_count += 1
                    game_grid[cy_coord][cx_coord].adjacent_mines = neighbor_count
        target_cell = game_grid[y][x]

    if target_cell.is_revealed or (target_cell.is_flagged and not is_chord_action): return False

    # Check for mine AFTER potential move
    if target_cell.is_mine:
        target_cell.is_revealed = True
        if not is_chord_action: target_cell.is_losing_mine = True
        return True # Mine hit!

    # Revealing a safe cell
    reveal_stack = [(x, y)]; visited_cells = set(); revealed_any_cell = False
    while reveal_stack:
        current_x, current_y = reveal_stack.pop()
        if not (0 <= current_x < grid_width and 0 <= current_y < grid_height) or (current_x, current_y) in visited_cells: continue
        cell_to_process = game_grid[current_y][current_x]
        if cell_to_process.is_revealed or cell_to_process.is_flagged: continue
        visited_cells.add((current_x, current_y))
        cell_to_process.is_revealed = True; cell_to_process.is_question = False
        revealed_any_cell = True
        if cell_to_process.adjacent_mines == 0 and not cell_to_process.is_mine:
            for dy_offset in range(-1, 2):
                for dx_offset in range(-1, 2):
                     if not (dx_offset == 0 and dy_offset == 0):
                        neighbor_x, neighbor_y = current_x + dx_offset, current_y + dy_offset
                        if 0 <= neighbor_x < grid_width and 0 <= neighbor_y < grid_height:
                            if not game_grid[neighbor_y][neighbor_x].is_revealed and not game_grid[neighbor_y][neighbor_x].is_flagged:
                                reveal_stack.append((neighbor_x, neighbor_y))
    if revealed_any_cell: play_game_sound('click')
    return False # No mine hit

def count_placed_flags(game_grid):
    return sum(cell_item.is_flagged for grid_row in game_grid for cell_item in grid_row)

def reveal_all_cells(game_grid, mark_losing_state=False, losing_pos=None):
    global grid_width, grid_height
    for y_pos in range(grid_height):
        for x_pos in range(grid_width):
            cell_item = game_grid[y_pos][x_pos]
            if mark_losing_state:
                if cell_item.is_mine and not cell_item.is_flagged: cell_item.is_revealed = True
                elif cell_item.is_flagged and not cell_item.is_mine: cell_item.is_revealed = True
                if (x_pos, y_pos) == losing_pos:
                    cell_item.is_losing_mine = True; cell_item.is_revealed = True
            elif not cell_item.is_mine: cell_item.is_revealed = True
            cell_item.is_question = False

def check_win_condition(game_grid):
    global grid_width, grid_height, mine_count_setting
    revealed_safe_count = sum(1 for grid_row in game_grid for cell_item in grid_row if cell_item.is_revealed and not cell_item.is_mine)
    total_safe_cells = (grid_width * grid_height) - mine_count_setting
    return revealed_safe_count == total_safe_cells

def perform_chord_reveal(game_grid, x, y):
    global grid_width, grid_height
    center_cell = game_grid[y][x]
    if not center_cell.is_revealed or center_cell.is_mine or center_cell.adjacent_mines == 0: return False, False
    neighbor_flag_count = 0; neighbors_to_potentially_reveal = []
    for dy_offset in range(-1, 2):
        for dx_offset in range(-1, 2):
            if dx_offset == 0 and dy_offset == 0: continue
            neighbor_x, neighbor_y = x + dx_offset, y + dy_offset
            if 0 <= neighbor_x < grid_width and 0 <= neighbor_y < grid_height:
                neighbor_cell = game_grid[neighbor_y][neighbor_x]
                if neighbor_cell.is_flagged: neighbor_flag_count += 1
                elif not neighbor_cell.is_revealed and not neighbor_cell.is_flagged: neighbors_to_potentially_reveal.append((neighbor_x, neighbor_y))
    if neighbor_flag_count == center_cell.adjacent_mines:
        hit_a_mine = False
        if neighbors_to_potentially_reveal:
            play_game_sound('click')
            for reveal_x, reveal_y in neighbors_to_potentially_reveal:
                if reveal_cell(game_grid, reveal_x, reveal_y, is_first_click=False, is_chord_action=True):
                    hit_a_mine = True
                    game_grid[reveal_y][reveal_x].is_losing_mine = True
                    break
            return True, hit_a_mine
        else: return False, False
    else: return False, False

def find_and_reveal_hint_cell(game_grid):
    global grid_width, grid_height
    safe_candidate_cells = [(x_pos, y_pos) for y_pos in range(grid_height) for x_pos in range(grid_width)
                            if not game_grid[y_pos][x_pos].is_revealed and
                               not game_grid[y_pos][x_pos].is_flagged and
                               not game_grid[y_pos][x_pos].is_question and
                               not game_grid[y_pos][x_pos].is_mine]
    if not safe_candidate_cells: print("No safe hints available!"); return False
    hint_x_coord, hint_y_coord = random.choice(safe_candidate_cells)
    print(f"Hint: Revealing ({hint_x_coord}, {hint_y_coord})")
    reveal_cell(game_grid, hint_x_coord, hint_y_coord)
    return True

# --- Drawing Functions ---
def draw_beveled_rectangle(surface, color, rect, border_thickness=2, is_raised=True):
    highlight_color = COLOR_BORDER_HIGHLIGHT; shadow_color = COLOR_BORDER_SHADOW
    pygame.draw.rect(surface, color, rect)
    if is_raised:
        pygame.draw.line(surface, highlight_color, rect.topleft, (rect.right - 1, rect.top), border_thickness)
        pygame.draw.line(surface, highlight_color, rect.topleft, (rect.left, rect.bottom - 1), border_thickness)
        pygame.draw.line(surface, shadow_color, (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), border_thickness)
        pygame.draw.line(surface, shadow_color, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), border_thickness)
    else:
        pygame.draw.line(surface, shadow_color, rect.topleft, (rect.right - 1, rect.top), border_thickness)
        pygame.draw.line(surface, shadow_color, rect.topleft, (rect.left, rect.bottom - 1), border_thickness)
        if border_thickness > 1:
            pygame.draw.line(surface, highlight_color, (rect.left + border_thickness -1, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 1)
            pygame.draw.line(surface, highlight_color, (rect.right - 1 , rect.top + border_thickness-1), (rect.right - 1, rect.bottom - 1), 1)

def draw_window_frame():
    draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, pygame.Rect(0, 0, window_width, window_height), border_thickness=3, is_raised=True)
    title_bar_rect = pygame.Rect(3, 3, window_width - 6, TOP_BORDER_HEIGHT - 4)
    pygame.draw.rect(main_screen, COLOR_WINDOW_BAR, title_bar_rect)
    window_title_text = f"Minesweeper - {current_difficulty_level.capitalize()}" # Renamed
    title_surface = font_window_title.render(window_title_text, True, COLOR_WINDOW_BAR_TEXT)
    title_y_pos = title_bar_rect.y + (title_bar_rect.height - title_surface.get_height()) // 2
    main_screen.blit(title_surface, (title_bar_rect.x + 6, title_y_pos))
    close_button_size = TOP_BORDER_HEIGHT - 10
    close_button_margin = (TOP_BORDER_HEIGHT - close_button_size) // 2
    close_button_rect = pygame.Rect(window_width - 3 - close_button_size - close_button_margin, 3 + close_button_margin, close_button_size, close_button_size)
    draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, close_button_rect, border_thickness=2, is_raised=True)
    x_inset_amount = close_button_size // 4
    pygame.draw.line(main_screen, COLOR_BUTTON_TEXT, (close_button_rect.left + x_inset_amount, close_button_rect.top + x_inset_amount), (close_button_rect.right - x_inset_amount -1, close_button_rect.bottom - x_inset_amount -1), 2)
    pygame.draw.line(main_screen, COLOR_BUTTON_TEXT, (close_button_rect.right - x_inset_amount -1, close_button_rect.top + x_inset_amount), (close_button_rect.left + x_inset_amount, close_button_rect.bottom - x_inset_amount -1), 2)

def draw_info_panel(flags_remaining, time_elapsed, current_game_state):
    panel_y_pos = TOP_BORDER_HEIGHT + 4
    panel_rect = pygame.Rect(BORDER, panel_y_pos, window_width - 2 * BORDER, INFO_PANEL_HEIGHT)
    draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, panel_rect, border_thickness=2, is_raised=False)
    internal_pad_y = PANEL_INTERNAL_PADDING; internal_pad_x = 10
    content_area_y = panel_y_pos + internal_pad_y
    content_area_height = INFO_PANEL_HEIGHT - 2 * internal_pad_y
    counter_display_width = 85; counter_display_height = content_area_height
    flags_counter_rect = pygame.Rect(panel_rect.left + internal_pad_x, content_area_y, counter_display_width, counter_display_height)
    pygame.draw.rect(main_screen, COLOR_DIGITAL_DISPLAY_BG, flags_counter_rect); pygame.draw.rect(main_screen, COLOR_BORDER_SHADOW, flags_counter_rect, 1)
    flag_icon_size = int(counter_display_height * 0.6); flag_icon_x = flags_counter_rect.left + 5; flag_icon_y = flags_counter_rect.centery - flag_icon_size // 2
    pygame.draw.line(main_screen, COLOR_FLAGPOLE, (flag_icon_x, flag_icon_y), (flag_icon_x, flag_icon_y + flag_icon_size), 2)
    pygame.draw.polygon(main_screen, COLOR_FLAG_HEAD, [(flag_icon_x + 1, flag_icon_y), (flag_icon_x + 1 + int(flag_icon_size * 0.7), flag_icon_y + flag_icon_size // 3), (flag_icon_x + 1, flag_icon_y + flag_icon_size // 3 * 2)])
    flags_text_content = f"{max(0, flags_remaining):03}"; flags_text_surface = font_digital_display.render(flags_text_content, True, COLOR_DIGITAL_DISPLAY_FG)
    flags_text_x_pos = flag_icon_x + int(flag_icon_size * 0.7) + 10; flags_text_rect = flags_text_surface.get_rect(midleft=(flags_text_x_pos, flags_counter_rect.centery)); flags_text_rect.centery += 2
    main_screen.blit(flags_text_surface, flags_text_rect)
    face_button_diameter = counter_display_height
    face_button_rect = pygame.Rect(panel_rect.centerx - face_button_diameter // 2, content_area_y, face_button_diameter, face_button_diameter)
    draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, face_button_rect, border_thickness=2, is_raised=True)
    face_center_coords = face_button_rect.center; face_inner_radius = face_button_diameter // 2 - 3
    pygame.draw.circle(main_screen, COLOR_FACE_BG, face_center_coords, face_inner_radius); pygame.draw.circle(main_screen, COLOR_FACE_FEATURES, face_center_coords, face_inner_radius, 1)
    eye_circle_radius = max(2, face_inner_radius // 4); eye_horizontal_offset = face_inner_radius // 2; eye_vertical_pos = face_center_coords[1] - face_inner_radius // 4
    left_eye_center = (int(face_center_coords[0] - eye_horizontal_offset), int(eye_vertical_pos)); right_eye_center = (int(face_center_coords[0] + eye_horizontal_offset), int(eye_vertical_pos))
    mouth_vertical_pos = face_center_coords[1] + face_inner_radius // 2.5; mouth_curve_width = eye_horizontal_offset * 1.5; mouth_curve_height = face_inner_radius // 2
    mouth_bounding_rect = pygame.Rect(face_center_coords[0] - mouth_curve_width // 2, mouth_vertical_pos - mouth_curve_height//2, mouth_curve_width, mouth_curve_height)
    if current_game_state == 'lost':
        eye_cross_offset = eye_circle_radius
        pygame.draw.line(main_screen, COLOR_FACE_FEATURES, (left_eye_center[0]-eye_cross_offset, left_eye_center[1]-eye_cross_offset), (left_eye_center[0]+eye_cross_offset, left_eye_center[1]+eye_cross_offset), 2)
        pygame.draw.line(main_screen, COLOR_FACE_FEATURES, (left_eye_center[0]+eye_cross_offset, left_eye_center[1]-eye_cross_offset), (left_eye_center[0]-eye_cross_offset, left_eye_center[1]+eye_cross_offset), 2)
        pygame.draw.line(main_screen, COLOR_FACE_FEATURES, (right_eye_center[0]-eye_cross_offset, right_eye_center[1]-eye_cross_offset), (right_eye_center[0]+eye_cross_offset, right_eye_center[1]+eye_cross_offset), 2)
        pygame.draw.line(main_screen, COLOR_FACE_FEATURES, (right_eye_center[0]+eye_cross_offset, right_eye_center[1]-eye_cross_offset), (right_eye_center[0]-eye_cross_offset, right_eye_center[1]+eye_cross_offset), 2)
        pygame.draw.arc(main_screen, COLOR_FACE_FEATURES, mouth_bounding_rect, math.pi * 1.1, math.pi * 1.9, 2)
    elif current_game_state == 'win':
        sunglass_height = eye_circle_radius * 2; sunglass_width = eye_circle_radius * 3; sunglass_y_pos = eye_vertical_pos - sunglass_height / 2
        left_sunglass_rect = pygame.Rect(left_eye_center[0] - sunglass_width/2, sunglass_y_pos, sunglass_width, sunglass_height); right_sunglass_rect = pygame.Rect(right_eye_center[0] - sunglass_width/2, sunglass_y_pos, sunglass_width, sunglass_height)
        pygame.draw.rect(main_screen, COLOR_FACE_FEATURES, left_sunglass_rect); pygame.draw.rect(main_screen, COLOR_FACE_FEATURES, right_sunglass_rect)
        pygame.draw.arc(main_screen, COLOR_FACE_FEATURES, mouth_bounding_rect, math.pi * 0.1, math.pi * 0.9, 2)
    else:
        pygame.draw.circle(main_screen, COLOR_FACE_FEATURES, left_eye_center, eye_circle_radius); pygame.draw.circle(main_screen, COLOR_FACE_FEATURES, right_eye_center, eye_circle_radius)
        pygame.draw.arc(main_screen, COLOR_FACE_FEATURES, mouth_bounding_rect, math.pi * 0.1, math.pi * 0.9, 2)
    timer_display_rect = pygame.Rect(panel_rect.right - internal_pad_x - counter_display_width, content_area_y, counter_display_width, counter_display_height)
    pygame.draw.rect(main_screen, COLOR_DIGITAL_DISPLAY_BG, timer_display_rect); pygame.draw.rect(main_screen, COLOR_BORDER_SHADOW, timer_display_rect, 1)
    clock_icon_total_size = int(counter_display_height * 0.65); clock_face_radius = clock_icon_total_size // 2
    clock_center_x = timer_display_rect.left + 5 + clock_face_radius; clock_center_y = timer_display_rect.centery
    pygame.draw.circle(main_screen, COLOR_CLOCK_FACE_BG, (clock_center_x, clock_center_y), clock_face_radius); pygame.draw.circle(main_screen, COLOR_CLOCK_OUTLINE, (clock_center_x, clock_center_y), clock_face_radius, 1)
    pygame.draw.line(main_screen, COLOR_CLOCK_HANDS, (clock_center_x, clock_center_y), (clock_center_x, clock_center_y - clock_face_radius + 3), 2)
    pygame.draw.line(main_screen, COLOR_CLOCK_HANDS, (clock_center_x, clock_center_y), (clock_center_x + clock_face_radius - 4, clock_center_y + 2), 1)
    timer_text_content = f"{min(time_elapsed, 999):03}"; timer_text_surface = font_digital_display.render(timer_text_content, True, COLOR_DIGITAL_DISPLAY_FG)
    timer_text_x_pos = clock_center_x + clock_face_radius + 8; timer_text_rect = timer_text_surface.get_rect(midleft=(timer_text_x_pos, timer_display_rect.centery)); timer_text_rect.centery += 2
    main_screen.blit(timer_text_surface, timer_text_rect)

def draw_difficulty_buttons(current_difficulty):
    """Draws the Easy, Medium, Hard buttons."""
    button_y = TOP_BORDER_HEIGHT + INFO_PANEL_HEIGHT + PANEL_GRID_SPACING
    button_h = DIFFICULTY_BUTTON_AREA_HEIGHT - PANEL_GRID_SPACING # Height for buttons
    button_w = 80 # Fixed width for difficulty buttons
    total_button_width = len(DIFFICULTIES) * button_w + (len(DIFFICULTIES) - 1) * 10 # Width + spacing
    start_x = (window_width - total_button_width) // 2 # Center the block of buttons

    difficulty_button_rects.clear() # Clear previous rects

    current_x = start_x
    for i, (level, _) in enumerate(DIFFICULTIES.items()):
        is_selected = (level == current_difficulty)
        button_rect = pygame.Rect(current_x, button_y, button_w, button_h)
        difficulty_button_rects[level] = button_rect # Store rect for click detection

        # Draw button slightly sunken if selected
        button_color = COLOR_BUTTON_PRESSED_BG if is_selected else COLOR_BACKGROUND
        draw_beveled_rectangle(main_screen, button_color, button_rect, border_thickness=2, is_raised=not is_selected)

        # Draw text
        text_surf = font_difficulty_button.render(level.capitalize(), True, COLOR_BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=button_rect.center)
        main_screen.blit(text_surf, text_rect)

        current_x += button_w + 10 # Move to next button position

def draw_status_area(current_game_state, time_elapsed):
    """Draws the Hint button and status text."""
    area_y = TOP_BORDER_HEIGHT + INFO_PANEL_HEIGHT + DIFFICULTY_BUTTON_AREA_HEIGHT + PANEL_GRID_SPACING
    area_h = STATUS_AREA_HEIGHT - PANEL_GRID_SPACING # Available height

    # Hint Button (position relative to left border)
    internal_pad_x = 10
    hint_button_y_pos = area_y + (area_h - HINT_BUTTON_H) // 2 # Center vertically in its area
    # Use the globally defined constants HINT_BUTTON_W and HINT_BUTTON_H
    hint_button_rect_local = pygame.Rect(BORDER + internal_pad_x, hint_button_y_pos, HINT_BUTTON_W, HINT_BUTTON_H)
    hint_button_static_rect.update(hint_button_rect_local) # Update the global rect

    draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, hint_button_rect_local, border_thickness=2, is_raised=True)
    hint_bulb_radius = 7; hint_bulb_center_x = hint_button_rect_local.left + hint_bulb_radius + 5; hint_bulb_center_y = hint_button_rect_local.centery
    pygame.draw.circle(main_screen, COLOR_HINT_BULB, (hint_bulb_center_x, hint_bulb_center_y), hint_bulb_radius)
    pygame.draw.circle(main_screen, COLOR_BORDER_SHADOW, (hint_bulb_center_x, hint_bulb_center_y), hint_bulb_radius, 1)
    hint_text_label = font_small_ui.render("Hint", True, COLOR_BUTTON_TEXT)
    hint_text_x_pos = hint_bulb_center_x + hint_bulb_radius + 4
    hint_text_y_pos = hint_button_rect_local.centery - hint_text_label.get_height() // 2 + 1
    main_screen.blit(hint_text_label, (hint_text_x_pos, hint_text_y_pos))

    # Status Text (position relative to hint button)
    status_text_x_pos = hint_button_rect_local.right + 15
    status_text_y_pos = hint_button_rect_local.centery - font_small_ui.get_height() // 2 + 1

    status_message = ""; status_color = COLOR_STATUS_BAR_TEXT
    if current_game_state == 'start': status_message = "Click Grid / Difficulty / F5 Scores"
    elif current_game_state == 'lost': status_message = "Game Over! Click face or press R."; status_color = COLOR_ALERT_RED
    elif current_game_state == 'win': status_message = f"You win! Time: {time_elapsed}s. Face/R."; status_color = (0, 128, 0)

    if status_message:
        status_label_surface = font_small_ui.render(status_message, True, status_color)
        main_screen.blit(status_label_surface, (status_text_x_pos, status_text_y_pos))


def draw_game_grid(game_grid, current_game_state):
    global grid_width, grid_height # Use current grid dimensions
    # Calculate the top-left corner to center the *current* grid within the max grid area
    max_grid_pixel_width = MAX_GRID_W * CELL_SIZE
    current_grid_pixel_width = grid_width * CELL_SIZE
    grid_area_start_x = BORDER + GRID_OUTLINE_WIDTH + (max_grid_pixel_width - current_grid_pixel_width) // 2

    max_grid_pixel_height = MAX_GRID_H * CELL_SIZE
    current_grid_pixel_height = grid_height * CELL_SIZE
    grid_area_start_y = TOP_BORDER_HEIGHT + INFO_PANEL_HEIGHT + DIFFICULTY_BUTTON_AREA_HEIGHT + STATUS_AREA_HEIGHT + \
                       PANEL_GRID_SPACING * 2 + (max_grid_pixel_height - current_grid_pixel_height) // 2


    # Draw sunken border around the max grid area (visual only)
    grid_max_area_y = TOP_BORDER_HEIGHT + INFO_PANEL_HEIGHT + DIFFICULTY_BUTTON_AREA_HEIGHT + STATUS_AREA_HEIGHT + PANEL_GRID_SPACING*2
    grid_outer_rect = pygame.Rect(BORDER, grid_max_area_y - GRID_OUTLINE_WIDTH, MAX_GRID_W*CELL_SIZE + 2*GRID_OUTLINE_WIDTH, MAX_GRID_H*CELL_SIZE + 2*GRID_OUTLINE_WIDTH)
    draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, grid_outer_rect, border_thickness=GRID_OUTLINE_WIDTH, is_raised=False)

    # Store the calculated top-left for click detection
    global grid_render_offset_x, grid_render_offset_y
    grid_render_offset_x = grid_area_start_x
    grid_render_offset_y = grid_area_start_y

    # Iterate through the *current* grid dimensions to draw cells
    for y_pos in range(grid_height):
        for x_pos in range(grid_width):
            cell_object = game_grid[y_pos][x_pos]
            # Calculate render position based on centered offset
            cell_render_x = grid_area_start_x + x_pos * CELL_SIZE
            cell_render_y = grid_area_start_y + y_pos * CELL_SIZE
            cell_bounding_rect = pygame.Rect(cell_render_x, cell_render_y, CELL_SIZE, CELL_SIZE)

            # --- Revealed Cells ---
            if cell_object.is_revealed:
                cell_background_color = COLOR_BACKGROUND
                if cell_object.is_losing_mine: cell_background_color = COLOR_ALERT_RED
                elif cell_object.is_mine: cell_background_color = COLOR_BACKGROUND
                pygame.draw.rect(main_screen, cell_background_color, cell_bounding_rect)
                pygame.draw.rect(main_screen, COLOR_BORDER_SHADOW, cell_bounding_rect, 1)
                if cell_object.is_mine: # Draw Mine
                    center_x, center_y = cell_bounding_rect.center; mine_body_radius = CELL_SIZE // 2 - 6
                    pygame.draw.circle(main_screen, COLOR_MINE_BODY, (center_x, center_y), mine_body_radius)
                    mine_highlight_radius = max(1, mine_body_radius // 3); mine_highlight_offset = mine_body_radius // 2
                    pygame.draw.circle(main_screen, COLOR_MINE_HIGHLIGHT, (center_x - mine_highlight_offset + 2, center_y - mine_highlight_offset + 2), mine_highlight_radius)
                    pygame.draw.line(main_screen, COLOR_MINE_BODY, (center_x - mine_body_radius - 2, center_y), (center_x + mine_body_radius + 2, center_y), 2)
                    pygame.draw.line(main_screen, COLOR_MINE_BODY, (center_x, center_y - mine_body_radius - 2), (center_x, center_y + mine_body_radius + 2), 2)
                elif cell_object.adjacent_mines > 0: # Draw Number
                    number_surface = font_grid_numbers.render(str(cell_object.adjacent_mines), True, NUMBER_COLORS[cell_object.adjacent_mines])
                    number_rect = number_surface.get_rect(center=cell_bounding_rect.center); number_rect.y += 1
                    main_screen.blit(number_surface, number_rect)
                elif current_game_state == 'lost' and cell_object.is_flagged and not cell_object.is_mine: # Wrong Flag X
                     pygame.draw.line(main_screen, COLOR_ALERT_RED, (cell_bounding_rect.left+4, cell_bounding_rect.top+4), (cell_bounding_rect.right-5, cell_bounding_rect.bottom-5), 3)
                     pygame.draw.line(main_screen, COLOR_ALERT_RED, (cell_bounding_rect.right-5, cell_bounding_rect.top+4), (cell_bounding_rect.left+4, cell_bounding_rect.bottom-5), 3)
            # --- Unrevealed Cells ---
            else:
                draw_beveled_rectangle(main_screen, COLOR_BACKGROUND, cell_bounding_rect, border_thickness=3, is_raised=True)
                if cell_object.is_flagged: # Draw Flag
                    flagpole_x = cell_bounding_rect.centerx - 4; flag_top_y = cell_bounding_rect.top + 6; flag_bottom_y = cell_bounding_rect.bottom - 6
                    flagpole_base_y = flag_bottom_y - 3; flag_head_height = 10; flag_head_width = 12
                    pygame.draw.line(main_screen, COLOR_FLAGPOLE, (flagpole_x, flag_top_y), (flagpole_x, flagpole_base_y), 2)
                    pygame.draw.polygon(main_screen, COLOR_FLAG_HEAD, [(flagpole_x + 1, flag_top_y), (flagpole_x + 1 + flag_head_width, flag_top_y + flag_head_height // 2), (flagpole_x + 1, flag_top_y + flag_head_height)])
                    pygame.draw.rect(main_screen, COLOR_FLAGPOLE, (flagpole_x-4, flagpole_base_y, 8, 3))
                elif cell_object.is_question: # Draw Question Mark
                    question_mark_surface = font_question_mark.render("?", True, COLOR_QUESTION_MARK)
                    question_mark_rect = question_mark_surface.get_rect(center=cell_bounding_rect.center)
                    main_screen.blit(question_mark_surface, question_mark_rect)

# --- Function to reset the game (with selected difficulty) ---
def reset_game_instance(difficulty_level):
    """Resets the game state and grid for the specified difficulty."""
    global game_grid, game_state, timer_start_time, time_elapsed_seconds, flags_placed_count
    global clicked_mine_position, current_difficulty_level, grid_width, grid_height, mine_count_setting, main_screen

    print(f"Setting difficulty to: {difficulty_level}")
    current_difficulty_level = difficulty_level
    grid_width, grid_height = DIFFICULTIES[difficulty_level]['size']
    mine_count_setting = DIFFICULTIES[difficulty_level]['mines']

    pygame.display.set_caption(f"Minesweeper - {current_difficulty_level.capitalize()}")

    game_grid = generate_game_grid()
    game_state = 'start'
    timer_start_time = 0
    time_elapsed_seconds = 0
    flags_placed_count = 0
    clicked_mine_position = None
    play_game_sound('start')

# --- Main Game Loop ---
def main():
    global game_grid, game_state, timer_start_time, time_elapsed_seconds, flags_placed_count
    global clicked_mine_position, current_difficulty_level, main_screen
    global face_button_static_rect, hint_button_static_rect, difficulty_button_rects
    global grid_render_offset_x, grid_render_offset_y

    pygame.init()
    pygame.mixer.init()
    load_high_scores()

    reset_game_instance(DEFAULT_DIFFICULTY)

    game_clock = pygame.time.Clock()
    is_running = True

    face_button_static_rect = pygame.Rect(0,0,0,0)
    hint_button_static_rect = pygame.Rect(0,0,0,0) # Initialize as empty rect
    difficulty_button_rects = {}
    grid_render_offset_x = 0
    grid_render_offset_y = 0

    panel_y_pos_init = TOP_BORDER_HEIGHT + 4
    content_area_y_init = panel_y_pos_init + PANEL_INTERNAL_PADDING
    counter_display_height_init = INFO_PANEL_HEIGHT - 2 * PANEL_INTERNAL_PADDING
    face_button_diameter_init = counter_display_height_init
    face_button_static_rect = pygame.Rect(window_width // 2 - face_button_diameter_init // 2, content_area_y_init, face_button_diameter_init, face_button_diameter_init)

    while is_running:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: reset_game_instance(current_difficulty_level)
                elif event.key == pygame.K_F2: reset_game_instance('easy')
                elif event.key == pygame.K_F3: reset_game_instance('medium')
                elif event.key == pygame.K_F4: reset_game_instance('hard')
                elif event.key == pygame.K_F5: display_high_scores()

            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_on_ui_element = False
                if face_button_static_rect.collidepoint(mouse_x, mouse_y):
                    clicked_on_ui_element = True
                    reset_game_instance(current_difficulty_level)
                elif not clicked_on_ui_element:
                    difficulty_button_was_clicked = False
                    for level, rect in difficulty_button_rects.items():
                        if rect.collidepoint(mouse_x, mouse_y):
                            clicked_on_ui_element = True
                            difficulty_button_was_clicked = True
                            if level != current_difficulty_level: reset_game_instance(level)
                            break
                    if not difficulty_button_was_clicked:
                        # Check hint button only if difficulty buttons weren't clicked
                        if hint_button_static_rect.collidepoint(mouse_x, mouse_y): # Check hint click
                            clicked_on_ui_element = True
                            if game_state == 'start' or game_state == 'playing':
                                is_first_action_in_game = (game_state == 'start' and time_elapsed_seconds == 0)
                                hint_was_revealed = find_and_reveal_hint_cell(game_grid)
                                if hint_was_revealed:
                                     if is_first_action_in_game: timer_start_time = time.time(); game_state = 'playing'
                                     if check_win_condition(game_grid):
                                          game_state = 'win'; flags_placed_count = mine_count_setting
                                          play_game_sound('win')
                                          if timer_start_time != 0:
                                              final_game_time = int(time.time() - timer_start_time)
                                              time_elapsed_seconds = min(final_game_time, 999)
                                              add_new_score(current_difficulty_level, time_elapsed_seconds)
                                          timer_start_time = 0

                if not clicked_on_ui_element and game_state != 'win' and game_state != 'lost':
                    grid_pixel_width = grid_width * CELL_SIZE; grid_pixel_height = grid_height * CELL_SIZE
                    if grid_render_offset_x <= mouse_x < grid_render_offset_x + grid_pixel_width and \
                       grid_render_offset_y <= mouse_y < grid_render_offset_y + grid_pixel_height:
                        clicked_grid_x = (mouse_x - grid_render_offset_x) // CELL_SIZE
                        clicked_grid_y = (mouse_y - grid_render_offset_y) // CELL_SIZE
                        if 0 <= clicked_grid_x < grid_width and 0 <= clicked_grid_y < grid_height:
                            is_this_the_first_click = (game_state == 'start')
                            target_cell_object = game_grid[clicked_grid_y][clicked_grid_x]
                            if event.button == 1:
                                if not target_cell_object.is_revealed and not target_cell_object.is_flagged:
                                    if is_this_the_first_click:
                                        if time_elapsed_seconds == 0: timer_start_time = time.time()
                                        game_state = 'playing'
                                    mine_was_hit = reveal_cell(game_grid, clicked_grid_x, clicked_grid_y, is_first_click=is_this_the_first_click)
                                    if mine_was_hit:
                                        game_state = 'lost'; clicked_mine_position = (clicked_grid_x, clicked_grid_y)
                                        reveal_all_cells(game_grid, mark_losing_state=True, losing_pos=clicked_mine_position)
                                        play_game_sound('explosion'); timer_start_time = 0
                                    elif check_win_condition(game_grid):
                                        game_state = 'win'; flags_placed_count = mine_count_setting
                                        play_game_sound('win')
                                        if timer_start_time != 0:
                                           final_game_time = int(time.time() - timer_start_time)
                                           time_elapsed_seconds = min(final_game_time, 999)
                                           add_new_score(current_difficulty_level, time_elapsed_seconds)
                                        timer_start_time = 0
                            elif event.button == 3:
                                if not target_cell_object.is_revealed:
                                    if not target_cell_object.is_flagged and not target_cell_object.is_question:
                                        if flags_placed_count < mine_count_setting: target_cell_object.is_flagged = True; play_game_sound('click')
                                    elif target_cell_object.is_flagged: target_cell_object.is_flagged = False; target_cell_object.is_question = True; play_game_sound('click')
                                    elif target_cell_object.is_question: target_cell_object.is_question = False; play_game_sound('click')
                                    flags_placed_count = count_placed_flags(game_grid)
                            elif event.button == 2:
                                chord_success, mine_hit_by_chord = perform_chord_reveal(game_grid, clicked_grid_x, clicked_grid_y)
                                if chord_success:
                                    if mine_hit_by_chord:
                                        game_state = 'lost'
                                        reveal_all_cells(game_grid, mark_losing_state=True, losing_pos=None)
                                        play_game_sound('explosion'); timer_start_time = 0
                                    elif check_win_condition(game_grid):
                                         game_state = 'win'; flags_placed_count = mine_count_setting
                                         play_game_sound('win')
                                         if timer_start_time != 0:
                                             final_game_time = int(time.time() - timer_start_time)
                                             time_elapsed_seconds = min(final_game_time, 999)
                                             add_new_score(current_difficulty_level, time_elapsed_seconds)
                                         timer_start_time = 0

        if game_state == 'playing' and timer_start_time != 0: time_elapsed_seconds = int(time.time() - timer_start_time)

        main_screen.fill(COLOR_BACKGROUND)
        draw_window_frame()
        flags_to_show = mine_count_setting - flags_placed_count
        current_timer_display = min(time_elapsed_seconds, 999) if timer_start_time != 0 or game_state == 'win' or game_state == 'lost' else 0
        draw_info_panel(flags_to_show, current_timer_display, game_state)
        draw_difficulty_buttons(current_difficulty_level)
        draw_status_area(game_state, current_timer_display)
        draw_game_grid(game_grid, game_state) # This updates grid_render_offset_x/y

        pygame.display.flip()
        game_clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()