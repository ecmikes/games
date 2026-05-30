# Snake Sprint is a desktop Snake game built with Python and Tkinter,
# where players guide a growing snake to eat food and increase their score.
# The game supports both WASD and arrow-key controls, includes clear game-over
# and win states, and lets players instantly restart with the R key.
#
# Requirements:
# - Python 3.8+ recommended
# - random (built into Python, no install needed)
# - tkinter (usually included with Python on Windows/macOS)
#   If tkinter is missing on Linux, install: sudo apt-get install python3-tk

import random
import tkinter as tk
import tkinter.font as tkfont

WINDOW_SIZE = 400
CELL = 20
GRID_SIZE = WINDOW_SIZE // CELL
HUD_HEIGHT = 64
CANVAS_HEIGHT = WINDOW_SIZE + HUD_HEIGHT

SPEED_OPTIONS = {
    "1": ("Easy", 170),
    "2": ("Medium", 120),
    "3": ("Hard", 85),
}
RENDER_INTERVAL = 33  # ~30 FPS render rate, independent of game speed
DEFAULT_SPEED_KEY = "2"
FOOD_COUNT = 3

SNAKE_COLOR = "#2e8b57"
SNAKE_OUTLINE_COLOR = "#1f5f3c"
SNAKE_HEAD_COLOR = "#256f47"
FOOD_COLOR = "#d9534f"
FOOD_OUTLINE_COLOR = "#b13a37"
FOOD_HIGHLIGHT_COLOR = "#ffd7d7"
FOOD_STYLES = [
    ("#d9534f", "#b13a37", "#ffd7d7"),  # red
    ("#f0ad4e", "#c98a30", "#ffe7c2"),  # orange
    ("#5bc0de", "#3a97b1", "#d7f2fb"),  # blue
    ("#5cb85c", "#3f8f3f", "#d8f3d8"),  # green
    ("#c97be8", "#9a58b7", "#efd9fa"),  # violet
]
TEXT_COLOR = "#222"
SUBTLE_TEXT_COLOR = "#555"
OVERLAY_COLOR = "black"
HUD_BG_COLOR = "#f5f1e6"
HUD_BORDER_COLOR = "#d8d1c3"
HUD_TOP_STRIP_COLOR = "#efe7d8"
HUD_PATTERN_COLOR = "#e7dece"
PLAYFIELD_BG_COLOR = "#fbfaf7"
PLAYFIELD_FLASH_COLOR = "#eef9ef"
GRID_LINE_COLOR = "#ece7de"

START_DIRECTION = "RIGHT"
START_SNAKE = [(5, 5), (4, 5), (3, 5)]
CONTROL_HINT = "Move: WASD/Arrows | R:Restart | 1:E 2:M 3:H"
CONTROL_HINT_PREFIX = "Move: WASD/Arrows | R:Restart | "

class SnakeGame:
    """Simple Snake game built with Tkinter."""

    def __init__(self):
        """Create the window, initialize state, and start the timed game loop."""
        self.root = tk.Tk()
        self.root.title("Snake")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=WINDOW_SIZE, height=CANVAS_HEIGHT, bg=PLAYFIELD_BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        self.root.bind_all("<KeyPress>", self.key_pressed)

        self.hud_hint_font = tkfont.Font(family="Arial", size=8)
        self.hud_hint_bold_font = tkfont.Font(family="Arial", size=8, weight="bold")

        self.reset_state()

        self.canvas.focus_set()
        self.root.focus_force()
        self.root.after(100, self.canvas.focus_set)
        self._init_static_bg()
        self.spawn_foods()
        self._render_loop()
        self.root.after(self.speed_delay, self.game_loop)

    def reset_state(self):
        """Reset game variables to their initial values for a new run."""
        self.direction = START_DIRECTION
        self.snake = START_SNAKE.copy()
        self.foods = {}
        self.game_over_flag = False
        self.score = 0
        self.status_text = "Playing"
        self.speed_key = DEFAULT_SPEED_KEY
        self.speed_name, self.speed_delay = SPEED_OPTIONS[self.speed_key]
        self.playfield_color = PLAYFIELD_BG_COLOR
        self.overlay_message = None
        self._flash_progress = 0.0

    def _render_loop(self):
        """Continuously redraw at ~30 FPS, independent of game logic speed."""
        self._update_flash()
        self.draw_scene()
        self.root.after(RENDER_INTERVAL, self._render_loop)

    def _update_flash(self):
        """Advance the playfield flash fade one step per render frame."""
        if self._flash_progress > 0:
            self._flash_progress = max(0.0, self._flash_progress - 0.1)
            self.playfield_color = self._lerp_color(
                PLAYFIELD_FLASH_COLOR, PLAYFIELD_BG_COLOR, self._flash_progress
            )

    def _lerp_color(self, c_from, c_to, t):
        """Interpolate between two hex colors. t=1 returns c_from, t=0 returns c_to."""
        r1, g1, b1 = int(c_from[1:3], 16), int(c_from[3:5], 16), int(c_from[5:7], 16)
        r2, g2, b2 = int(c_to[1:3], 16), int(c_to[3:5], 16), int(c_to[5:7], 16)
        r = int(r1 * t + r2 * (1 - t))
        g = int(g1 * t + g2 * (1 - t))
        b = int(b1 * t + b2 * (1 - t))
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_speed(self, speed_key):
        """Update the game speed based on key 1/2/3."""
        self.speed_key = speed_key
        self.speed_name, self.speed_delay = SPEED_OPTIONS[speed_key]

    def _init_static_bg(self):
        """Draw all static background elements once; called on startup only."""
        # HUD chrome
        self.canvas.create_rectangle(0, 0, WINDOW_SIZE, HUD_HEIGHT, fill=HUD_BG_COLOR, outline=HUD_BORDER_COLOR, tags="hud_static")
        self.canvas.create_rectangle(0, 0, WINDOW_SIZE, 20, fill=HUD_TOP_STRIP_COLOR, outline="", tags="hud_static")
        for x in range(0, WINDOW_SIZE, 14):
            self.canvas.create_line(x, 0, x, HUD_HEIGHT, fill=HUD_PATTERN_COLOR, width=1, tags="hud_static")
        self.canvas.create_line(0, HUD_HEIGHT, WINDOW_SIZE, HUD_HEIGHT, fill=HUD_BORDER_COLOR, width=2, tags="hud_static")
        # Playfield background — stored so its fill can be updated without recreation
        self._playfield_rect = self.canvas.create_rectangle(0, HUD_HEIGHT, WINDOW_SIZE, CANVAS_HEIGHT, fill=self.playfield_color, outline="", tags="playfield_bg")
        # Grid lines
        for i in range(GRID_SIZE + 1):
            x = i * CELL
            y = HUD_HEIGHT + i * CELL
            self.canvas.create_line(x, HUD_HEIGHT, x, CANVAS_HEIGHT, fill=GRID_LINE_COLOR, width=1, tags="grid_static")
            self.canvas.create_line(0, y, WINDOW_SIZE, y, fill=GRID_LINE_COLOR, width=1, tags="grid_static")
        # Static title text
        self.canvas.create_text(10, 8, anchor="nw", text="Snake Sprint", fill=SUBTLE_TEXT_COLOR, font=("Arial", 11, "italic"), tags="hud_static")

    def draw_controls_hint(self):
        """Draw controls text and bold the active speed selection."""
        right_x = WINDOW_SIZE - 10
        y = 8

        segments = [
            ("3:H", "3"),
            (" ", None),
            ("2:M", "2"),
            (" ", None),
            ("1:E", "1"),
            (" | ", None),
            (CONTROL_HINT_PREFIX, None),
        ]

        for text, speed_token in segments:
            font = self.hud_hint_font
            if speed_token == self.speed_key:
                font = self.hud_hint_bold_font

            self.canvas.create_text(
                right_x,
                y,
                anchor="ne",
                text=text,
                fill=SUBTLE_TEXT_COLOR,
                font=font,
                tags="hud_text",
            )
            right_x -= font.measure(text)

    def flash_playfield(self):
        """Trigger a smooth playfield flash when food is eaten."""
        self._flash_progress = 1.0
        self.playfield_color = PLAYFIELD_FLASH_COLOR

    def draw_cell(self, x, y, color, outline=None, oval=False, tags="game"):
        """Draw one grid cell as a rectangle or oval."""
        left = x * CELL
        top = HUD_HEIGHT + y * CELL
        right = left + CELL
        bottom = top + CELL
        if oval:
            self.canvas.create_oval(left, top, right, bottom, fill=color, outline=outline or color, tags=tags)
        else:
            self.canvas.create_rectangle(left, top, right, bottom, fill=color, outline=outline or color, tags=tags)

    def draw_scene(self):
        """Redraw only dynamic elements: snake, food, HUD text, and overlays."""
        # Update playfield flash color without recreating the rectangle
        self.canvas.itemconfig(self._playfield_rect, fill=self.playfield_color)

        # Remove only the items that change each tick
        self.canvas.delete("game")
        self.canvas.delete("hud_text")

        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                self.draw_snake_head(x, y)
            else:
                self.draw_cell(x, y, SNAKE_COLOR, outline=SNAKE_OUTLINE_COLOR)

        for (fx, fy), (food_color, outline_color, highlight_color) in self.foods.items():
            self.draw_food(fx, fy, food_color, outline_color, highlight_color)

        self.draw_controls_hint()
        self.canvas.create_text(
            10,
            34,
            anchor="nw",
            text=f"Status: {self.status_text}",
            fill=TEXT_COLOR,
            font=("Arial", 12, "bold"),
            tags="hud_text",
        )
        self.canvas.create_text(
            150,
            34,
            anchor="nw",
            text=f"Score: {self.score}",
            fill=TEXT_COLOR,
            font=("Arial", 12, "bold"),
            tags="hud_text",
        )
        self.canvas.create_text(
            250,
            34,
            anchor="nw",
            text=f"Speed: {self.speed_name}",
            fill=TEXT_COLOR,
            font=("Arial", 12, "bold"),
            tags="hud_text",
        )
        if self.overlay_message:
            self.show_center_message(self.overlay_message)

    def draw_snake_head(self, x, y):
        """Draw the snake head with directional eyes."""
        left = x * CELL
        top = HUD_HEIGHT + y * CELL
        right = left + CELL
        bottom = top + CELL

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=SNAKE_HEAD_COLOR,
            outline=SNAKE_OUTLINE_COLOR,
            tags="game",
        )

        eye_size = max(2, CELL // 6)
        pupil_size = max(1, eye_size // 2)
        margin = max(2, CELL // 5)

        if self.direction == "UP":
            eye_positions = [
                (left + margin, top + margin),
                (right - margin - eye_size, top + margin),
            ]
        elif self.direction == "DOWN":
            eye_positions = [
                (left + margin, bottom - margin - eye_size),
                (right - margin - eye_size, bottom - margin - eye_size),
            ]
        elif self.direction == "LEFT":
            eye_positions = [
                (left + margin, top + margin),
                (left + margin, bottom - margin - eye_size),
            ]
        else:  # RIGHT
            eye_positions = [
                (right - margin - eye_size, top + margin),
                (right - margin - eye_size, bottom - margin - eye_size),
            ]

        for ex, ey in eye_positions:
            self.canvas.create_oval(
                ex,
                ey,
                ex + eye_size,
                ey + eye_size,
                fill="white",
                outline="white",
                tags="game",
            )
            px = ex + (eye_size - pupil_size) / 2
            py = ey + (eye_size - pupil_size) / 2
            self.canvas.create_oval(
                px,
                py,
                px + pupil_size,
                py + pupil_size,
                fill="black",
                outline="black",
                tags="game",
            )

    def draw_food(self, x, y, food_color, outline_color, highlight_color):
        """Draw food as a polished, smaller circle with a highlight."""
        left = x * CELL
        top = HUD_HEIGHT + y * CELL
        inset = max(2, CELL // 8)

        self.canvas.create_oval(
            left + inset,
            top + inset,
            left + CELL - inset,
            top + CELL - inset,
            fill=food_color,
            outline=outline_color,
            tags="game",
        )

        highlight_size = max(2, CELL // 5)
        self.canvas.create_oval(
            left + inset + 2,
            top + inset + 2,
            left + inset + 2 + highlight_size,
            top + inset + 2 + highlight_size,
            fill=highlight_color,
            outline=highlight_color,
            tags="game",
        )

    def show_center_message(self, message):
        """Display a centered overlay message (for win/game over)."""
        center_x = WINDOW_SIZE // 2
        center_y = HUD_HEIGHT + (WINDOW_SIZE // 2)

        # Soft panel to increase readability for screenshots and demos.
        panel_w = 280
        panel_h = 110
        self.canvas.create_rectangle(
            center_x - panel_w // 2,
            center_y - panel_h // 2,
            center_x + panel_w // 2,
            center_y + panel_h // 2,
            fill="#f7f2e7",
            outline=HUD_BORDER_COLOR,
            width=2,
            tags="game",
        )

        # Shadow + foreground text for improved contrast.
        self.canvas.create_text(
            center_x + 2,
            center_y + 2,
            text=message,
            fill="#8a8175",
            font=("Arial", 22, "bold"),
            justify="center",
            tags="game",
        )
        self.canvas.create_text(
            center_x,
            center_y,
            text=message,
            fill=OVERLAY_COLOR,
            font=("Arial", 22, "bold"),
            justify="center",
            tags="game",
        )

    def spawn_foods(self):
        """Keep up to FOOD_COUNT food items on free cells."""
        free_cells = [
            (x, y)
            for x in range(GRID_SIZE)
            for y in range(GRID_SIZE)
            if (x, y) not in self.snake and (x, y) not in self.foods
        ]

        while len(self.foods) < FOOD_COUNT and free_cells:
            picked = random.choice(free_cells)
            self.foods[picked] = random.choice(FOOD_STYLES)
            free_cells.remove(picked)

        # If the snake fills the board and no food can exist, trigger win state.
        if not free_cells and not self.foods:
            self.game_over_flag = True

    def key_pressed(self, event):
        """Handle keyboard input for movement and restart."""
        key = event.keysym.lower()

        if key in SPEED_OPTIONS:
            self.set_speed(key)
            return

        if key == "r" and self.game_over_flag:
            self.restart()
            return

        # Support both arrow keys and WASD for laptops/keyboards where arrows are awkward.
        if key in ("up", "w") and self.direction != "DOWN":
            self.direction = "UP"
        elif key in ("down", "s") and self.direction != "UP":
            self.direction = "DOWN"
        elif key in ("left", "a") and self.direction != "RIGHT":
            self.direction = "LEFT"
        elif key in ("right", "d") and self.direction != "LEFT":
            self.direction = "RIGHT"

    def game_loop(self):
        """Advance one game tick: move, detect collisions, and update display."""
        if self.game_over_flag:
            return

        head_x, head_y = self.snake[0]

        if self.direction == "UP":
            head_y -= 1
        elif self.direction == "DOWN":
            head_y += 1
        elif self.direction == "LEFT":
            head_x -= 1
        elif self.direction == "RIGHT":
            head_x += 1

        # Wall collision
        if head_x < 0 or head_x >= GRID_SIZE or head_y < 0 or head_y >= GRID_SIZE:
            self.game_over()
            return

        next_head = (head_x, head_y)
        growing = next_head in self.foods
        occupied_body = self.snake if growing else self.snake[:-1]

        # Self collision
        if next_head in occupied_body:
            self.game_over()
            return

        # Move snake
        self.snake.insert(0, next_head)

        # Eating food
        if growing:
            self.foods.pop(next_head, None)
            self.score += 1
            self.flash_playfield()
            self.spawn_foods()
            if self.game_over_flag:
                self.status_text = "You Win"
                self.overlay_message = "YOU WIN!\nPress R to restart"
                print("YOU WIN")
                return
        else:
            self.snake.pop()

        self.root.after(self.speed_delay, self.game_loop)

    def game_over(self):
        """End the current round and show the game-over message."""
        self.game_over_flag = True
        self.status_text = "Game Over"
        self.overlay_message = "GAME OVER\nPress R to restart"
        print("GAME OVER")

    def restart(self):
        """Start a new round from the initial state."""
        current_speed_name = self.speed_name
        current_speed_delay = self.speed_delay
        self.reset_state()
        self.speed_name = current_speed_name
        self.speed_delay = current_speed_delay
        self.spawn_foods()
        self.draw_scene()
        self.root.after(self.speed_delay, self.game_loop)

    def run(self):
        """Run the Tkinter event loop."""
        self.root.mainloop()

if __name__ == "__main__":
    SnakeGame().run()

    
