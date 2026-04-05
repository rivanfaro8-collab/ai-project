import random
import threading
from pathlib import Path
from collections import deque
import tkinter as tk
from tkinter import ttk

# =========================================================
# CONFIG
# =========================================================
ROWS = 6
COLS = 6
CELL_SIZE = 85

EMPTY = 0
OBSTACLE = 1
DIRT = 2
VACUUM = 3

MOVE_ORDER = [
    ("UP",    (-1, 0)),
    ("LEFT",  (0, -1)),
    ("RIGHT", (0, 1)),
    ("DOWN",  (1, 0)),
]

MOVE_COST = {
    "UP": 2,
    "LEFT": 1,
    "RIGHT": 1,
    "DOWN": 0
}

COLORS = {
    "bg": "#0f172a",
    "panel": "#111827",
    "panel2": "#1f2937",
    "grid": "#334155",
    "text": "#e5e7eb",
    "muted": "#94a3b8",
    "empty": "#e5e7eb",
    "obstacle": "#0b0f19",
    "dirt": "#facc15",
    "vacuum": "#3b82f6",
    "path": "#cbd5e1",
    "wrong_try": "#ef4444",
    "success": "#22c55e",
    "danger": "#ef4444",
    "button": "#2563eb",
    "button_hover": "#1d4ed8",
}

# =========================================================
# BOARD GENERATION
# =========================================================


def generate_board(rows=ROWS, cols=COLS):
    board = [[EMPTY for _ in range(cols)] for _ in range(rows)]

    cells = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(cells)

    vacuum_pos = cells.pop()
    dirt_pos = cells.pop()

    board[vacuum_pos[0]][vacuum_pos[1]] = VACUUM
    board[dirt_pos[0]][dirt_pos[1]] = DIRT

    obstacle_count = random.randint(6, 11)
    for _ in range(obstacle_count):
        if not cells:
            break
        r, c = cells.pop()
        board[r][c] = OBSTACLE

    return board, vacuum_pos, dirt_pos


# =========================================================
# SOLUTION METHOD (BFS + exploration order)
# =========================================================
def solve_bfs(board, start, goal):
    """
    Breadth-First Search using a queue.

    Returns:
        path: final solution path [(move_name, position), ...] or None
        explored_order: all popped/expanded nodes in BFS order
    """
    q = deque([start])
    visited = {start: (None, None)}
    explored_order = []

    while q:
        current = q.popleft()
        explored_order.append(current)

        if current == goal:
            path = []
            node = current
            while visited[node][0] is not None:
                parent, move_name = visited[node]
                path.append((move_name, node))
                node = parent
            path.reverse()
            return path, explored_order

        r, c = current

        for move_name, (dr, dc) in MOVE_ORDER:
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)

            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if board[nr][nc] != OBSTACLE and nxt not in visited:
                    visited[nxt] = (current, move_name)
                    q.append(nxt)

    return None, explored_order


# =========================================================
# COST METHOD
# =========================================================
def calculate_cost(path):
    if path is None:
        return None

    total = 0
    for move_name, _ in path:
        total += MOVE_COST[move_name]
    return total


# =========================================================
# TXT SAVER METHOD
# =========================================================
def save_solution_to_desktop(board, start, goal, path, total_cost, filename="solution.txt"):
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home()

    file_path = desktop / filename

    def cell_symbol(value, r, c):
        if (r, c) == start:
            return "V"
        if (r, c) == goal:
            return "D"
        if value == EMPTY:
            return "."
        if value == OBSTACLE:
            return "X"
        if value == DIRT:
            return "D"
        if value == VACUUM:
            return "V"
        return "?"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("VACUUM BREADTH FIRST SEARCH SOLUTION\n")
        f.write("=" * 45 + "\n\n")

        f.write("Initial Board:\n")
        for r in range(ROWS):
            row_symbols = []
            for c in range(COLS):
                row_symbols.append(cell_symbol(board[r][c], r, c))
            f.write(" ".join(row_symbols) + "\n")

        f.write("\nLegend:\n")
        f.write("V = Vacuum\n")
        f.write("D = Dirt\n")
        f.write("X = Obstacle\n")
        f.write(". = Empty cell\n\n")

        f.write(f"Vacuum Start Position: {start}\n")
        f.write(f"Dirt Position: {goal}\n\n")

        if path is None:
            f.write("There is no solution because of obstacles.\n")
            return str(file_path)

        f.write("Steps to Solution:\n")
        cumulative = 0
        for i, (move_name, pos) in enumerate(path, start=1):
            cumulative += MOVE_COST[move_name]
            f.write(
                f"Step {i}: Move {move_name:<5} -> Position {pos} | "
                f"Move Cost = {MOVE_COST[move_name]} | Total So Far = {cumulative}\n"
            )

        f.write(f"\nNumber of Steps: {len(path)}\n")
        f.write(f"Overall Cost: {total_cost}\n")

    return str(file_path)


# =========================================================
# GUI
# =========================================================
class VacuumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vacuum BFS Solver")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(True, True)

        self.board = None
        self.start = None
        self.goal = None
        self.path = None
        self.total_cost = None
        self.file_path = None
        self.explored_order = []

        self.current_step_index = -1
        self.current_unsolved_index = -1
        self.playing = False

        self.build_ui()
        self.start_new_run()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Main.TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["panel"])
        style.configure(
            "Title.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=("Segoe UI", 22, "bold")
        )
        style.configure(
            "Sub.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 10)
        )

        outer = ttk.Frame(self.root, style="Main.TFrame", padding=16)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(
            outer, text="Vacuum Breadth-First Search", style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            outer,
            text="Random board • Background computation • Solution and BFS tries shown visually",
            style="Sub.TLabel"
        )
        subtitle.pack(anchor="w", pady=(0, 14))

        top = ttk.Frame(outer, style="Main.TFrame")
        top.pack(fill="x", pady=(0, 12))

        self.info_card = tk.Frame(
            top, bg=COLORS["panel"], bd=0, highlightthickness=0)
        self.info_card.pack(side="left", fill="x", expand=True)

        self.status_label = tk.Label(
            self.info_card,
            text="Preparing...",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            padx=16,
            pady=10
        )
        self.status_label.pack(fill="x")

        self.details_label = tk.Label(
            self.info_card,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            padx=16,
            pady=0
        )
        self.details_label.pack(fill="x", pady=(0, 10))

        btn_frame = tk.Frame(top, bg=COLORS["bg"])
        btn_frame.pack(side="right", padx=(12, 0))

        self.new_btn = tk.Button(
            btn_frame, text="New Board", command=self.start_new_run,
            bg=COLORS["button"], fg="white", activebackground=COLORS["button_hover"],
            activeforeground="white", relief="flat", bd=0, padx=18, pady=10,
            font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        self.new_btn.pack(fill="x", pady=(0, 8))

        self.next_btn = tk.Button(
            btn_frame, text="Next Step", command=self.next_step,
            bg=COLORS["panel2"], fg="white", relief="flat", bd=0, padx=18, pady=10,
            font=("Segoe UI", 10, "bold"), cursor="hand2", state="disabled"
        )
        self.next_btn.pack(fill="x", pady=(0, 8))

        self.auto_btn = tk.Button(
            btn_frame, text="Auto Play", command=self.toggle_auto_play,
            bg=COLORS["panel2"], fg="white", relief="flat", bd=0, padx=18, pady=10,
            font=("Segoe UI", 10, "bold"), cursor="hand2", state="disabled"
        )
        self.auto_btn.pack(fill="x", pady=(0, 8))

        self.unsolved_btn = tk.Button(
            btn_frame, text="Next Step Unsolved", command=self.next_step_unsolved,
            bg=COLORS["panel2"], fg="white", relief="flat", bd=0, padx=18, pady=10,
            font=("Segoe UI", 10, "bold"), cursor="hand2", state="disabled"
        )
        self.unsolved_btn.pack(fill="x")

        board_card = tk.Frame(
            outer, bg=COLORS["panel"], bd=0, highlightthickness=0)
        board_card.pack(fill="both", expand=True)

        # =========================================================
        # SCROLLABLE BOARD AREA
        # =========================================================
        board_container = tk.Frame(board_card, bg=COLORS["panel"])
        board_container.pack(fill="both", expand=True, padx=12, pady=12)

        self.canvas = tk.Canvas(
            board_container,
            bg=COLORS["panel"],
            bd=0,
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = tk.Scrollbar(
            board_container, orient="vertical", command=self.canvas.yview
        )
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        self.h_scroll = tk.Scrollbar(
            board_container, orient="horizontal", command=self.canvas.xview
        )
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set
        )

        board_container.grid_rowconfigure(0, weight=1)
        board_container.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self.on_canvas_configure)

        bottom = tk.Frame(outer, bg=COLORS["bg"])
        bottom.pack(fill="x", pady=(12, 0))

        self.step_label = tk.Label(
            bottom,
            text="",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 11)
        )
        self.step_label.pack(anchor="w")

        self.root.after(100, self.enable_mousewheel)

    def enable_mousewheel(self):
        self.canvas.bind_all(
            "<MouseWheel>", self._on_mousewheel)      # Windows
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shiftwheel)
        self.canvas.bind_all(
            "<Button-4>", self._on_mousewheel_linux)  # Linux up
        self.canvas.bind_all(
            "<Button-5>", self._on_mousewheel_linux)  # Linux down

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shiftwheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def on_canvas_configure(self, event=None):
        self.update_scroll_region()

    def update_scroll_region(self):
        offset = 20
        board_width = offset + COLS * CELL_SIZE + 20
        board_height = offset + ROWS * CELL_SIZE + 20
        self.canvas.configure(scrollregion=(0, 0, board_width, board_height))

    def start_new_run(self):
        self.playing = False
        self.auto_btn.config(text="Auto Play")

        self.next_btn.config(state="disabled")
        self.auto_btn.config(state="disabled")
        self.unsolved_btn.config(state="disabled")

        self.board, self.start, self.goal = generate_board()
        self.path = None
        self.total_cost = None
        self.file_path = None
        self.explored_order = []

        self.current_step_index = -1
        self.current_unsolved_index = -1

        self.status_label.config(
            text="Solving in background...", fg=COLORS["text"])
        self.details_label.config(
            text="Please wait while BFS finds the solution and saves solution.txt")
        self.step_label.config(text="")

        self.draw_board(current_vacuum=self.start,
                        highlight_path=False, highlight_unsolved=False)

        threading.Thread(target=self.run_solver_in_background,
                         daemon=True).start()

    def run_solver_in_background(self):
        path, explored_order = solve_bfs(self.board, self.start, self.goal)
        total_cost = calculate_cost(path)
        file_path = save_solution_to_desktop(
            self.board, self.start, self.goal, path, total_cost, "solution.txt"
        )

        self.root.after(
            0,
            lambda: self.finish_background_work(
                path, explored_order, total_cost, file_path)
        )

    def finish_background_work(self, path, explored_order, total_cost, file_path):
        self.path = path
        self.explored_order = explored_order
        self.total_cost = total_cost
        self.file_path = file_path
        self.current_step_index = -1
        self.current_unsolved_index = -1

        if self.path is None:
            self.status_label.config(
                text="No solution found", fg=COLORS["danger"])
            self.details_label.config(
                text=(
                    f"solution.txt saved to:\n{self.file_path}\n\n"
                    f"There is no solution because of obstacles.\n"
                    f"BFS explored {len(self.explored_order)} states."
                )
            )
            self.step_label.config(
                text="You can still use 'Next Step Unsolved' to see BFS tries.")
            self.draw_board(current_vacuum=self.start,
                            highlight_path=False, highlight_unsolved=False)
            self.unsolved_btn.config(state="normal")
            return

        self.status_label.config(text="Solution ready", fg=COLORS["success"])
        self.details_label.config(
            text=(
                f"Steps: {len(self.path)}\n"
                f"Overall Cost: {self.total_cost}\n"
                f"BFS explored states: {len(self.explored_order)}\n"
                f"Saved to: {self.file_path}"
            )
        )
        self.step_label.config(
            text="Press Next Step for solution path, Auto Play for full path, or Next Step Unsolved for BFS tries."
        )
        self.draw_board(current_vacuum=self.start,
                        highlight_path=False, highlight_unsolved=False)

        self.next_btn.config(state="normal")
        self.auto_btn.config(state="normal")
        self.unsolved_btn.config(state="normal")

    def toggle_auto_play(self):
        if self.path is None:
            return

        self.playing = not self.playing
        self.auto_btn.config(text="Stop" if self.playing else "Auto Play")

        if self.playing:
            self.auto_play()

    def auto_play(self):
        if not self.playing:
            return

        if self.path is None:
            self.playing = False
            self.auto_btn.config(text="Auto Play")
            return

        if self.current_step_index >= len(self.path) - 1:
            self.playing = False
            self.auto_btn.config(text="Auto Play")
            return

        self.next_step()
        self.root.after(650, self.auto_play)

    def next_step(self):
        if self.path is None:
            return

        if self.current_step_index >= len(self.path) - 1:
            self.next_btn.config(state="disabled")
            self.auto_btn.config(state="disabled")
            return

        self.current_step_index += 1
        move_name, pos = self.path[self.current_step_index]

        current_partial = self.path[:self.current_step_index + 1]
        current_cost = calculate_cost(current_partial)

        self.draw_board(current_vacuum=pos, highlight_path=True,
                        highlight_unsolved=False)

        self.step_label.config(
            text=(
                f"Solution Step {self.current_step_index + 1}/{len(self.path)}  |  "
                f"Move: {move_name}  |  "
                f"Position: {pos}  |  "
                f"Cost so far: {current_cost}"
            )
        )

        if self.current_step_index == len(self.path) - 1:
            self.step_label.config(
                text=(
                    f"Goal reached  |  Total Steps: {len(self.path)}  |  "
                    f"Overall Cost: {self.total_cost}"
                )
            )
            self.next_btn.config(state="disabled")
            self.auto_btn.config(state="disabled")
            self.playing = False
            self.auto_btn.config(text="Auto Play")

    def next_step_unsolved(self):
        if not self.explored_order:
            return

        if self.current_unsolved_index >= len(self.explored_order) - 1:
            self.unsolved_btn.config(state="disabled")
            return

        self.current_unsolved_index += 1
        pos = self.explored_order[self.current_unsolved_index]

        self.draw_board(current_vacuum=pos, highlight_path=False,
                        highlight_unsolved=True)

        is_goal = (pos == self.goal)

        if is_goal:
            if self.path is None:
                self.step_label.config(
                    text=(
                        f"BFS Try {self.current_unsolved_index + 1}/{len(self.explored_order)}  |  "
                        f"Position: {pos}  |  Goal cell reached, but no valid saved solution path."
                    )
                )
            else:
                self.step_label.config(
                    text=(
                        f"BFS Try {self.current_unsolved_index + 1}/{len(self.explored_order)}  |  "
                        f"Position: {pos}  |  Goal found by BFS."
                    )
                )
                self.unsolved_btn.config(state="disabled")
        else:
            self.step_label.config(
                text=(
                    f"BFS Try {self.current_unsolved_index + 1}/{len(self.explored_order)}  |  "
                    f"Visited Position: {pos}"
                )
            )

    def draw_board(self, current_vacuum, highlight_path=False, highlight_unsolved=False):
        self.canvas.delete("all")

        offset = 20

        board_width = COLS * CELL_SIZE + 32
        board_height = ROWS * CELL_SIZE + 32

        self.canvas.create_rectangle(
            8, 8,
            board_width,
            board_height,
            fill=COLORS["panel2"],
            outline=""
        )

        solved_positions = set()
        if highlight_path and self.path is not None and self.current_step_index >= 0:
            for _, pos in self.path[:self.current_step_index + 1]:
                solved_positions.add(pos)

        unsolved_positions = set()
        if highlight_unsolved and self.current_unsolved_index >= 0:
            for pos in self.explored_order[:self.current_unsolved_index + 1]:
                unsolved_positions.add(pos)

        for r in range(ROWS):
            for c in range(COLS):
                x1 = offset + c * CELL_SIZE
                y1 = offset + r * CELL_SIZE
                x2 = x1 + CELL_SIZE - 6
                y2 = y1 + CELL_SIZE - 6

                fill = COLORS["empty"]

                if self.board[r][c] == OBSTACLE:
                    fill = COLORS["obstacle"]
                elif self.board[r][c] == DIRT:
                    fill = COLORS["dirt"]

                if (r, c) in solved_positions and (r, c) != self.goal:
                    fill = COLORS["path"]

                if (r, c) in unsolved_positions and (r, c) != self.goal and self.board[r][c] != OBSTACLE:
                    fill = COLORS["wrong_try"]

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill, outline=COLORS["grid"], width=2
                )

        gr, gc = self.goal
        gx1 = offset + gc * CELL_SIZE
        gy1 = offset + gr * CELL_SIZE
        gx2 = gx1 + CELL_SIZE - 6
        gy2 = gy1 + CELL_SIZE - 6

        if self.board[gr][gc] != OBSTACLE:
            self.canvas.create_text(
                (gx1 + gx2) / 2,
                (gy1 + gy2) / 2,
                text="DIRT",
                fill="#111827",
                font=("Segoe UI", 11, "bold")
            )

        vr, vc = current_vacuum
        vx1 = offset + vc * CELL_SIZE + 14
        vy1 = offset + vr * CELL_SIZE + 14
        vx2 = offset + vc * CELL_SIZE + CELL_SIZE - 20
        vy2 = offset + vr * CELL_SIZE + CELL_SIZE - 20

        self.canvas.create_oval(
            vx1, vy1, vx2, vy2,
            fill=COLORS["vacuum"], outline="", width=0
        )
        self.canvas.create_text(
            (vx1 + vx2) / 2,
            (vy1 + vy2) / 2,
            text="V",
            fill="white",
            font=("Segoe UI", 16, "bold")
        )

        self.update_scroll_region()


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x700")
    root.minsize(700, 500)
    app = VacuumApp(root)
    root.mainloop()
