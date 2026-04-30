# main.py
import customtkinter as ctk
import numpy as np
import tkinter as tk
import re
import threading
from tkinter import messagebox
from data import SLABS_DATA, ARTIFACTS_DATA, SET_NAMES, COMBOS_DATA
import logic

PIXEL_FONT = "DungGeunMo" 

GRADE_COLORS = {
    '일반': '#ffffff',
    '고급': '#3b82f6',
    '희귀': '#fbbf24',
    '전설': '#f472b6',
    '영원': '#4ade80',
    '결속': '#4ade80'
}

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def show(self, title, combo_text, desc_text, grade_text, flavor_text, grade, level):
        if self.tipwindow: return
        x = self.widget.winfo_rootx() + 85
        y = self.widget.winfo_rooty() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        outer_frame = tk.Frame(tw, background="#94a3b8", padx=3, pady=3)
        outer_frame.pack()
        inner_frame = tk.Frame(outer_frame, background="#2b2b36", padx=12, pady=12)
        inner_frame.pack()

        title_color = GRADE_COLORS.get(grade, "#fbbf24")
        tk.Label(inner_frame, text=title, bg="#2b2b36", fg=title_color, font=(PIXEL_FONT, 14, "bold")).pack(anchor="w", pady=(0, 2))
        
        if combo_text:
            tk.Label(inner_frame, text=combo_text, bg="#2b2b36", fg="#86efac", font=(PIXEL_FONT, 11)).pack(anchor="w", pady=(0, 6))

        tk.Frame(inner_frame, background="#4b5563", height=2, width=240).pack(fill="x", pady=(0, 8))

        if desc_text:
            calc_height = desc_text.count('\n') + 1
            text_widget = tk.Text(inner_frame, background="#2b2b36", foreground="#d1d5db", borderwidth=0, font=(PIXEL_FONT, 11), wrap="word", width=42, height=calc_height)
            text_widget.pack(anchor="w", pady=(0, 10))
            
            text_widget.tag_configure("green", foreground="#4ade80")
            text_widget.tag_configure("default", foreground="#d1d5db")
            
            last_idx = 0
            pattern = r'\d+(?:\.\d+)?[^\s/]*?(?:/\d+(?:\.\d+)?[^\s/]*?)+'
            for match in re.finditer(pattern, desc_text):
                text_widget.insert(tk.END, desc_text[last_idx:match.start()], "default")
                parts = match.group().split('/')
                
                for i, part in enumerate(parts):
                    target_level = min(max(level, 0), len(parts)-1)
                    tag = "green" if i == target_level else "default"
                    text_widget.insert(tk.END, part, tag)
                    if i < len(parts) - 1:
                        text_widget.insert(tk.END, "/", "default")
                        
                last_idx = match.end()
            text_widget.insert(tk.END, desc_text[last_idx:], "default")
            text_widget.configure(state="disabled")

        if grade_text:
            tk.Label(inner_frame, text=grade_text, bg="#2b2b36", fg="#9ca3af", font=(PIXEL_FONT, 10)).pack(anchor="w")
        if flavor_text:
            f_calc_height = flavor_text.count('\n') + 1
            flavor_widget = tk.Text(inner_frame, background="#2b2b36", foreground="#9ca3af", borderwidth=0, font=(PIXEL_FONT, 10), wrap="word", width=45, height=f_calc_height)
            flavor_widget.pack(anchor="w")
            flavor_widget.insert("1.0", f"'{flavor_text}'")
            flavor_widget.configure(state="disabled")

    def hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class SephiriaOptimizer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sephiria Bag Organizer v1.0 (베타)")
        self.geometry("1200x900")
        ctk.set_appearance_mode("dark")

        self.rows, self.cols = 8, 6
        self.grid_data = np.full((self.rows, self.cols), None)
        self.locked = np.full((self.rows, self.cols), True) 
        self.rotations = np.zeros((self.rows, self.cols), dtype=int)
        self.levels = np.zeros((self.rows, self.cols), dtype=int)
        self.scores = np.zeros((self.rows, self.cols), dtype=int)
        self.mystery_buffs = np.zeros((self.rows, self.cols), dtype=int)
        self.ignored_cells = set()
        
        default_calges = ['견고', '잉걸불', '빙하', '마법공학']
        self.calges_mapping = {i: default_calges[(i // 2) % 4] for i in range(8)}
        self.calges_comboboxes = []
        self.build_priority_menus = {}
        self.build_priorities = {'1순위': '없음', '2순위': '없음', '3순위': '없음'}
        
        for r in range(5):
            for c in range(6): self.locked[r, c] = False

        self.current_tool = "select"
        self.pending_item = None 
        self.pending_rot = 0
        self.selected_cell = None
        self.drag_start = None
        self.is_dragging = False

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)

        self.setup_ui()
        self.bind_all("<KeyRelease>", self.handle_key_all)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=320)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="SEPHIRIA\nOPTIMIZER", font=ctk.CTkFont(family=PIXEL_FONT, size=24, weight="bold")).pack(pady=(20, 10))

        self.tool_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tool_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkButton(self.tool_frame, text="선택 / 드래그 (기본)", fg_color="#64748b", font=ctk.CTkFont(family=PIXEL_FONT, size=12), command=lambda: self.set_tool("select")).pack(pady=2, fill="x")
        ctk.CTkButton(self.tool_frame, text="신비 칸 지정", fg_color="#8b5cf6", hover_color="#7c3aed", font=ctk.CTkFont(family=PIXEL_FONT, size=12), command=lambda: self.set_tool("mystery")).pack(pady=2, fill="x")
        ctk.CTkButton(self.tool_frame, text="칸 해제/잠금", fg_color="#f59e0b", font=ctk.CTkFont(family=PIXEL_FONT, size=12), command=lambda: self.set_tool("unlock")).pack(pady=2, fill="x")
        ctk.CTkButton(self.tool_frame, text="지우기", fg_color="#ef4444", font=ctk.CTkFont(family=PIXEL_FONT, size=12), command=lambda: self.set_tool("erase")).pack(pady=2, fill="x")

        search_entry = ctk.CTkEntry(self.sidebar, textvariable=self.search_var, placeholder_text="아이템 이름 검색...", font=ctk.CTkFont(family=PIXEL_FONT, size=12))
        search_entry.pack(pady=(10, 0), padx=10, fill="x")

        self.tabview = ctk.CTkTabview(self.sidebar)
        self.tabview.pack(pady=5, padx=10, fill="both", expand=True)
        self.tabview.add("석판")
        self.tabview.add("아티팩트")
        self.tabview.add("내 콤보")
        self.tabview.add("설정")
        self.tabview.configure(command=self.on_tab_change)

        self.slab_filter_menu = ctk.CTkOptionMenu(self.tabview.tab("석판"), values=["전체", "일반", "고급", "희귀", "전설", "영원"], font=ctk.CTkFont(family=PIXEL_FONT, size=12), command=self.update_slab_list)
        self.slab_filter_menu.pack(pady=5, fill="x")
        slab_container = ctk.CTkFrame(self.tabview.tab("석판"), fg_color="#0f172a", corner_radius=6)
        slab_container.pack(fill="both", expand=True, pady=5)
        self.slab_scroll = ctk.CTkScrollbar(slab_container)
        self.slab_scroll.pack(side="right", fill="y", padx=2, pady=2)
        self.slab_listbox = tk.Listbox(slab_container, bg="#0f172a", fg="#4ade80", selectbackground="#047857", selectforeground="white", highlightthickness=0, borderwidth=0, font=(PIXEL_FONT, 12))
        self.slab_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.slab_scroll.configure(command=self.slab_listbox.yview)
        self.slab_listbox.configure(yscrollcommand=self.slab_scroll.set)
        self.slab_listbox.bind("<<ListboxSelect>>", self.on_slab_select)

        self.art_filter_frame = ctk.CTkFrame(self.tabview.tab("아티팩트"), fg_color="transparent")
        self.art_filter_frame.pack(fill="x", pady=5)
        self.art_combo_menu = ctk.CTkOptionMenu(self.art_filter_frame, values=["콤보 전체"] + SET_NAMES, font=ctk.CTkFont(family=PIXEL_FONT, size=11), command=self.update_art_list)
        self.art_combo_menu.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self.art_grade_menu = ctk.CTkOptionMenu(self.art_filter_frame, values=["등급 전체", "일반", "고급", "희귀", "전설", "영원"], font=ctk.CTkFont(family=PIXEL_FONT, size=11), command=self.update_art_list)
        self.art_grade_menu.pack(side="right", fill="x", expand=True, padx=(2, 0))
        art_container = ctk.CTkFrame(self.tabview.tab("아티팩트"), fg_color="#0f172a", corner_radius=6)
        art_container.pack(fill="both", expand=True, pady=5)
        self.art_scroll = ctk.CTkScrollbar(art_container)
        self.art_scroll.pack(side="right", fill="y", padx=2, pady=2)
        self.art_listbox = tk.Listbox(art_container, bg="#0f172a", fg="#93c5fd", selectbackground="#1d4ed8", selectforeground="white", highlightthickness=0, borderwidth=0, font=(PIXEL_FONT, 12))
        self.art_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.art_scroll.configure(command=self.art_listbox.yview)
        self.art_listbox.configure(yscrollcommand=self.art_scroll.set)
        self.art_listbox.bind("<<ListboxSelect>>", self.on_art_select)
        
        self.combo_container = ctk.CTkScrollableFrame(self.tabview.tab("내 콤보"), fg_color="transparent")
        self.combo_container.pack(fill="both", expand=True)

        settings_frame = ctk.CTkScrollableFrame(self.tabview.tab("설정"), fg_color="transparent")
        settings_frame.pack(fill="both", expand=True)

        # ── 빌드 우선순위 설정 ──
        ctk.CTkLabel(settings_frame, text="빌드 우선순위 설정", font=ctk.CTkFont(family=PIXEL_FONT, size=14, weight="bold"), text_color="#38bdf8").pack(pady=(10, 4), anchor="w")
        ctk.CTkLabel(settings_frame, text="최적화 시 선택한 스탯을 올리는 아이템에\n가산점을 부여합니다.", font=ctk.CTkFont(family=PIXEL_FONT, size=11), text_color="#64748b", justify="left").pack(anchor="w", pady=(0, 6))

        stat_options = ['없음'] + logic.ALL_STATS
        for rank, color in [('1순위', '#f59e0b'), ('2순위', '#94a3b8'), ('3순위', '#78716c')]:
            row_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=3)
            ctk.CTkLabel(row_frame, text=f"{rank}:", font=ctk.CTkFont(family=PIXEL_FONT, size=12), text_color=color, width=50, anchor="w").pack(side="left")
            menu = ctk.CTkOptionMenu(row_frame, values=stat_options, font=ctk.CTkFont(family=PIXEL_FONT, size=11),
                                     fg_color="#1e293b", button_color="#334155",
                                     command=lambda v, r=rank: self.update_build_priority(r, v))
            menu.set('없음')
            menu.pack(side="left", fill="x", expand=True)
            self.build_priority_menus[rank] = menu

        ctk.CTkFrame(settings_frame, fg_color="#334155", height=1).pack(fill="x", pady=10)

        ctk.CTkLabel(settings_frame, text="[캘세더니 열쇠] 콤보 배치", font=ctk.CTkFont(family=PIXEL_FONT, size=14, weight="bold"), text_color="#fbbf24").pack(pady=(0, 10), anchor="w")
        
        for i in range(self.rows):
            frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            frame.pack(fill="x", pady=4)
            ctk.CTkLabel(frame, text=f"{i+1}번째 줄:", font=ctk.CTkFont(family=PIXEL_FONT, size=12), width=65, anchor="w").pack(side="left")
            menu = ctk.CTkOptionMenu(frame, values=SET_NAMES, font=ctk.CTkFont(family=PIXEL_FONT, size=12), command=lambda v, idx=i: self.update_calges_mapping(idx, v))
            menu.set(self.calges_mapping[i])
            menu.pack(side="left", fill="x", expand=True)
            self.calges_comboboxes.append(menu)

        self.update_slab_list()
        self.update_art_list()

        self.rot_label = ctk.CTkLabel(self.sidebar, text="선택: 없음", text_color="#f59e0b", font=ctk.CTkFont(family=PIXEL_FONT, size=12))
        self.rot_label.pack(pady=(5, 0))
        self.warn_label = ctk.CTkLabel(self.sidebar, text="[E] 레벨 업  [Q] 레벨 다운", text_color="#94a3b8", font=ctk.CTkFont(family=PIXEL_FONT, size=11))
        self.warn_label.pack(pady=(0, 5))
        
        self.btn_run = ctk.CTkButton(self.sidebar, text="자동 배치 최적화 (BETA)", height=40, fg_color="#10b981", hover_color="#059669", font=ctk.CTkFont(family=PIXEL_FONT, size=14, weight="bold"), command=self.run_optimization)
        self.btn_run.pack(side="bottom", pady=(5, 20), padx=10, fill="x")

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20)
        
        self.grid_cells = []
        self.tooltips = {}
        self.create_inventory_ui()

    def update_build_priority(self, rank, val):
        self.build_priorities[rank] = val

    def run_optimization(self):
        self.btn_run.configure(text="연산 중... (잠시만 기다려주세요)", state="disabled")
        
        # '없음' 제외한 실제 우선순위만 전달
        active_priorities = {k: v for k, v in self.build_priorities.items() if v and v != '없음'}
        
        def optimize_thread():
            best_g, best_r, best_l = logic.optimize_layout(
                self.grid_data.copy(),
                self.rotations.copy(),
                self.levels.copy(),
                self.mystery_buffs.copy(),
                self.locked.copy(),
                self.rows, self.cols,
                build_priorities=active_priorities if active_priorities else None
            )
            self.after(0, self.apply_optimized_layout, best_g, best_r, best_l)
            
        threading.Thread(target=optimize_thread, daemon=True).start()

    def apply_optimized_layout(self, best_grid, best_rotations, best_levels):
        self.grid_data = np.array(best_grid)
        self.rotations = np.array(best_rotations)
        self.levels = np.array(best_levels)
        self.update_grid_ui()
        self.btn_run.configure(text="자동 배치 최적화 (BETA)", state="normal")

    def update_calges_mapping(self, idx, val):
        self.calges_mapping[idx] = val
        self.update_grid_ui()

    def update_settings_ui(self):
        for r in range(self.rows):
            if all(self.locked[r]):
                self.calges_comboboxes[r].configure(state="disabled")
            else:
                self.calges_comboboxes[r].configure(state="normal")

    def on_search_change(self, *args):
        self.update_slab_list()
        self.update_art_list()

    def on_slab_select(self, event):
        sel = self.slab_listbox.curselection()
        if sel: self.select_item("slab", self.slab_listbox.get(sel[0]))

    def on_art_select(self, event):
        sel = self.art_listbox.curselection()
        if sel: self.select_item("artifact", self.art_listbox.get(sel[0]))

    def update_slab_list(self, _=None):
        filter_grade = self.slab_filter_menu.get()
        search_kw = self.search_var.get().lower()
        self.slab_listbox.delete(0, tk.END)
        for slab_name, slab_info in SLABS_DATA.items():
            if (filter_grade == "전체" or slab_info.get('g') == filter_grade) and (search_kw in slab_name.lower()):
                self.slab_listbox.insert(tk.END, slab_name)

    def update_art_list(self, _=None):
        sel_combo = self.art_combo_menu.get()
        sel_grade = self.art_grade_menu.get()
        search_kw = self.search_var.get().lower()
        
        self.art_listbox.delete(0, tk.END)
        for art_name, art_info in ARTIFACTS_DATA.items():
            match_combo = (sel_combo == "콤보 전체")
            if not match_combo:
                art_sets = art_info.get('sets', [])
                if isinstance(art_sets, str): art_sets = [art_sets]
                elif not art_sets and 'set' in art_info: art_sets = [art_info['set']]
                if sel_combo in art_sets: match_combo = True

            match_grade = (sel_grade == "등급 전체" or art_info.get('g') == sel_grade)

            if match_combo and match_grade and (search_kw in art_name.lower()):
                self.art_listbox.insert(tk.END, art_name)

    def on_tab_change(self):
        tab = self.tabview.get()
        if tab in ["설정", "내 콤보"]: return
        self.current_tool = "slab" if tab == "석판" else "artifact"
        self.pending_item = None
        self.slab_listbox.selection_clear(0, tk.END)
        self.art_listbox.selection_clear(0, tk.END)
        self.update_rot_label()

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        if tool_name != "select" and tool_name != "mystery": 
            self.selected_cell = None
        self.update_grid_ui()

    def select_item(self, item_type, item_name):
        self.current_tool = item_type
        self.pending_item = item_name
        self.pending_rot = 0
        self.update_rot_label()

    def get_cell_from_coords(self, root_x, root_y):
        for r in range(self.rows):
            for c in range(self.cols):
                lbl = self.grid_cells[r][c]
                x1 = lbl.winfo_rootx()
                y1 = lbl.winfo_rooty()
                x2 = x1 + lbl.winfo_width()
                y2 = y1 + lbl.winfo_height()
                if x1 <= root_x <= x2 and y1 <= root_y <= y2:
                    return r, c
        return None

    def on_press(self, e, r, c):
        if self.current_tool == "select":
            if self.grid_data[r, c]:
                if self.selected_cell == (r, c):
                    self.selected_cell = None
                    self.drag_start = None
                else:
                    self.drag_start = (r, c)
                    self.selected_cell = (r, c)
                self.is_dragging = False
                self.update_rot_label()
            else:
                self.selected_cell = None
                
        elif self.current_tool == "mystery": 
            if not self.locked[r, c]:
                self.mystery_buffs[r, c] = (self.mystery_buffs[r, c] + 1) % 4
                self.selected_cell = (r, c)
                self.update_grid_ui()
                
        else:
            if self.current_tool == "unlock":
                self.locked[r, c] = not self.locked[r, c]
                if self.locked[r, c]:
                    self.grid_data[r, c] = None
                    self.rotations[r, c] = 0
                    self.levels[r, c] = 0
                    self.mystery_buffs[r, c] = 0
            elif not self.locked[r, c]:
                if self.current_tool == "erase":
                    self.grid_data[r, c] = None
                    self.rotations[r, c] = 0
                    self.levels[r, c] = 0
                    self.mystery_buffs[r, c] = 0
                    self.selected_cell = None
                elif (self.current_tool == "slab" or self.current_tool == "artifact") and self.pending_item:
                    if not self.grid_data[r, c]:
                        self.grid_data[r, c] = self.pending_item
                        self.rotations[r, c] = self.pending_rot
                        self.levels[r, c] = 0
                        self.pending_item = None
                        self.slab_listbox.selection_clear(0, tk.END)
                        self.art_listbox.selection_clear(0, tk.END)
                        self.set_tool("select")
        self.update_grid_ui()

    def on_motion(self, e, r, c):
        if not self.drag_start or self.current_tool != "select": return

        if not self.is_dragging:
            self.is_dragging = True
            val = self.grid_data[r, c]
            if val:
                bg = "#064e3b" if val in SLABS_DATA else "#1e3a8a"
                self.ghost = ctk.CTkLabel(self, text=val, width=75, height=75, fg_color=bg, corner_radius=6, text_color="white", wraplength=65, font=ctk.CTkFont(family=PIXEL_FONT, size=11))
                self.ghost.lift()
        
        if self.is_dragging and hasattr(self, 'ghost'):
            x = e.x_root - self.winfo_rootx() + 10
            y = e.y_root - self.winfo_rooty() + 10
            self.ghost.place(x=x, y=y)

    def on_release(self, e):
        if not self.drag_start: return
        r, c = self.drag_start

        if self.is_dragging and hasattr(self, 'ghost'):
            self.ghost.destroy()
            del self.ghost

        if self.is_dragging:
            target = self.get_cell_from_coords(e.x_root, e.y_root)
            if target:
                tr, tc = target
                if not self.locked[tr, tc] and (tr, tc) != (r, c):
                    self.grid_data[tr, tc], self.grid_data[r, c] = self.grid_data[r, c], self.grid_data[tr, tc]
                    self.rotations[tr, tc], self.rotations[r, c] = self.rotations[r, c], self.rotations[tr, tc]
                    self.levels[tr, tc], self.levels[r, c] = self.levels[r, c], self.levels[tr, tc]
                    self.selected_cell = (tr, tc)
            else:
                self.grid_data[r, c] = None
                self.rotations[r, c] = 0
                self.levels[r, c] = 0
                self.selected_cell = None

        self.drag_start = None
        self.is_dragging = False
        self.update_grid_ui()

    def on_enter(self, e, r, c):
        val = self.grid_data[r, c]
        if val in ARTIFACTS_DATA:
            is_ignored = (r, c) in self.ignored_cells
            tt_data = logic.get_tooltip_data(val, r, c, self.rows, self.cols, self.locked, self.calges_mapping, is_ignored, self.grid_data)
            if tt_data: 
                total_level = self.levels[r, c] + self.scores[r, c] + self.mystery_buffs[r, c]
                self.tooltips[(r, c)].show(*tt_data, total_level)

    def on_leave(self, e, r, c):
        self.tooltips[(r, c)].hide()

    def handle_key_all(self, e):
        char = getattr(e, 'char', '').lower()
        keysym = getattr(e, 'keysym', '').lower()
        keycode = getattr(e, 'keycode', -1)
        
        is_r = char in ('r', 'ㄱ', 'ㄲ') or keysym in ('r', 'korean_giyeog', 'korean_ssanggiyeog') or keycode == 82
        is_e = char in ('e', 'ㄷ', 'ㄸ') or keysym in ('e', 'korean_digeut', 'korean_ssangdigeut') or keycode == 69
        is_q = char in ('q', 'ㅂ', 'ㅃ') or keysym in ('q', 'korean_pieub', 'korean_ssangpieub') or keycode == 81
        is_esc = keysym == 'escape' or keycode == 27
        
        if is_r:
            if self.current_tool == "slab" and self.pending_item:
                if not SLABS_DATA[self.pending_item].get('nr'):
                    self.pending_rot = (self.pending_rot + 1) % 4
                    self.update_rot_label()
            elif self.selected_cell:
                r, c = self.selected_cell
                val = self.grid_data[r, c]
                if val in SLABS_DATA:
                    if not SLABS_DATA[val].get('nr'):
                        self.rotations[r, c] = (self.rotations[r, c] + 1) % 4
                        self.update_rot_label()
                        self.update_grid_ui()
                        
        elif is_e:
            if self.selected_cell:
                r, c = self.selected_cell
                if self.grid_data[r, c] in ARTIFACTS_DATA:
                    self.levels[r, c] = min(self.levels[r, c] + 1, 14)
                    self.update_grid_ui()
                    
                    self.tooltips[(r, c)].hide()
                    is_ignored = (r, c) in self.ignored_cells
                    tt_data = logic.get_tooltip_data(self.grid_data[r, c], r, c, self.rows, self.cols, self.locked, self.calges_mapping, is_ignored, self.grid_data)
                    if tt_data: 
                        total_level = self.levels[r, c] + self.scores[r, c] + self.mystery_buffs[r, c]
                        self.tooltips[(r, c)].show(*tt_data, total_level)
                        
        elif is_q:
            if self.selected_cell:
                r, c = self.selected_cell
                if self.grid_data[r, c] in ARTIFACTS_DATA:
                    self.levels[r, c] = max(self.levels[r, c] - 1, 0)
                    self.update_grid_ui()
                    
                    self.tooltips[(r, c)].hide()
                    is_ignored = (r, c) in self.ignored_cells
                    tt_data = logic.get_tooltip_data(self.grid_data[r, c], r, c, self.rows, self.cols, self.locked, self.calges_mapping, is_ignored, self.grid_data)
                    if tt_data: 
                        total_level = self.levels[r, c] + self.scores[r, c] + self.mystery_buffs[r, c]
                        self.tooltips[(r, c)].show(*tt_data, total_level)

        elif is_esc:
            self.set_tool("select")
            self.selected_cell = None
            self.slab_listbox.selection_clear(0, tk.END)
            self.art_listbox.selection_clear(0, tk.END)
            self.update_grid_ui()

    def update_rot_label(self):
        if (self.current_tool == "slab" or self.current_tool == "artifact") and self.pending_item:
            if self.current_tool == "artifact":
                self.rot_label.configure(text=f"배치 대기: {self.pending_item}")
            else:
                self.rot_label.configure(text=f"배치 대기 석판 회전: {self.pending_rot * 90}°")
        elif self.selected_cell:
            r, c = self.selected_cell
            val = self.grid_data[r, c]
            if val in SLABS_DATA:
                self.rot_label.configure(text=f"배치된 석판 회전: {self.rotations[r,c] * 90}°")
            elif val in ARTIFACTS_DATA:
                total_level = self.levels[r, c] + self.scores[r, c] + self.mystery_buffs[r, c]
                self.rot_label.configure(text=f"선택된 아티팩트: {val} (최종 레벨: {total_level})")
        else:
            self.rot_label.configure(text="선택된 항목: 없음")

    def create_inventory_ui(self):
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                cell_frame = ctk.CTkFrame(self.main_frame, width=75, height=75, corner_radius=6)
                cell_frame.grid(row=r, column=c, padx=3, pady=3)
                cell_frame.grid_propagate(False)

                lbl = ctk.CTkLabel(cell_frame, text="", width=75, height=75, corner_radius=6, wraplength=65, font=ctk.CTkFont(family=PIXEL_FONT, size=11))
                lbl.pack(fill="both", expand=True)
                
                lbl.bind("<Button-1>", lambda e, row=r, col=c: self.on_press(e, row, col))
                lbl.bind("<B1-Motion>", lambda e, row=r, col=c: self.on_motion(e, row, col))
                lbl.bind("<ButtonRelease-1>", lambda e: self.on_release(e))
                lbl.bind("<Enter>", lambda e, row=r, col=c: self.on_enter(e, row, col))
                lbl.bind("<Leave>", lambda e, row=r, col=c: self.on_leave(e, row, col))
                
                self.tooltips[(r, c)] = ToolTip(lbl)
                row_cells.append(lbl)
            self.grid_cells.append(row_cells)
        self.update_grid_ui()

    def update_combo_ui(self, active_combos):
        for widget in self.combo_container.winfo_children():
            widget.destroy()
            
        if not active_combos:
            ctk.CTkLabel(self.combo_container, text="현재 모은 콤보가 없습니다.", text_color="#94a3b8", font=ctk.CTkFont(family=PIXEL_FONT, size=12)).pack(pady=20)
            return

        for combo_name, data in active_combos.items():
            if not data['effects']: continue
            
            frame = ctk.CTkFrame(self.combo_container, fg_color="#1e293b", corner_radius=6)
            frame.pack(fill="x", pady=4, padx=2)
            
            ctk.CTkLabel(frame, text=f"✨ {combo_name} ({data['count']}개)", text_color="#fbbf24", font=ctk.CTkFont(family=PIXEL_FONT, size=14, weight="bold"), anchor="w").pack(fill="x", padx=8, pady=(6, 2))
            
            for effect in data['effects']:
                ctk.CTkLabel(frame, text=effect, text_color="#d1d5db", font=ctk.CTkFont(family=PIXEL_FONT, size=11), justify="left", wraplength=220).pack(anchor="w", padx=8, pady=(0, 4))

    def update_grid_ui(self):
        self.scores.fill(0)
        self.ignored_cells = set()
        
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.grid_data[r, c]
                if val in SLABS_DATA:
                    offs = logic.get_offs(val, r, c, self.rotations[r, c], self.rows, self.cols, self.locked)
                    for o in offs:
                        nr, nc = r + o['dr'], c + o['dc']
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.locked[nr, nc]:
                            self.scores[nr, nc] += o['val']
                            if o.get('ignore', False):
                                self.ignored_cells.add((nr, nc))

        self.update_settings_ui()

        active_combos = logic.calculate_active_combos(self.grid_data, self.rows, self.cols, COMBOS_DATA, ARTIFACTS_DATA, self.calges_mapping)
        self.update_combo_ui(active_combos)

        for r in range(self.rows):
            for c in range(self.cols):
                lbl = self.grid_cells[r][c]
                is_locked = self.locked[r, c]
                val = self.grid_data[r, c]
                score = self.scores[r, c]
                myst_val = self.mystery_buffs[r, c]
                is_selected = (self.selected_cell == (r, c))
                is_ignored = (r, c) in self.ignored_cells
                
                myst_prefix = f"🔮(+{myst_val})\n" if myst_val > 0 else ""

                if is_locked:
                    lbl.configure(text="X", fg_color="#0f172a", text_color="#334155")
                elif val in ARTIFACTS_DATA:
                    total_level = self.levels[r, c] + score + myst_val
                    score_str = f"\n(+{score})" if score > 0 else f"\n({score})" if score < 0 else ""
                    tt_data = logic.get_tooltip_data(val, r, c, self.rows, self.cols, self.locked, self.calges_mapping, is_ignored, self.grid_data)
                    
                    if is_ignored:
                        lbl.configure(text=f"🚫 무시됨\n{myst_prefix}{val}", fg_color="#334155", text_color="#94a3b8")
                    elif tt_data and "⚠" in tt_data[2] and not is_ignored:
                        lbl.configure(text=f"⚠\n{myst_prefix}{val}", fg_color="#7f1d1d", text_color="#fca5a5")
                    else:
                        lvl_str = f" [Lv.{total_level}]" if total_level > 0 else ""
                        lbl.configure(text=f"{myst_prefix}{val}{lvl_str}", fg_color="#1e3a8a", text_color="#93c5fd")
                elif val in SLABS_DATA:
                    rot_str = f"{self.rotations[r,c]*90}°"
                    cond_msg = None
                    s = SLABS_DATA[val]
                    if s.get('cond') and not is_ignored:
                        unlocked_rows = [i for i in range(self.rows) if not all(self.locked[i])]
                        unlocked_cols = [j for j in range(self.cols) if not all(self.locked[:, j])]
                        if unlocked_rows and unlocked_cols:
                            min_r, max_r = min(unlocked_rows), max(unlocked_rows)
                            min_c, max_c = min(unlocked_cols), max(unlocked_cols)
                            if s['cond'] == 'bottom' and r != max_r: cond_msg = "error"
                            if s['cond'] == 'top' and r != min_r: cond_msg = "error"
                            if s['cond'] == 'edge' and (c != min_c and c != max_c): cond_msg = "error"
                    
                    if cond_msg:
                        lbl.configure(text=f"⚠\n{myst_prefix}{val}", fg_color="#7f1d1d", text_color="#fca5a5")
                    else:
                        lbl.configure(text=f"{myst_prefix}{val}\n{rot_str}", fg_color="#064e3b", text_color="#4ade80")
                else: 
                    score_str = f"+{score}" if score > 0 else str(score) if score < 0 else ""
                    if myst_val > 0:
                        lbl.configure(text=f"🔮(+{myst_val})\n{score_str}", fg_color="#3b0764", text_color="#c4b5fd")
                    else:
                        lbl.configure(text=score_str, fg_color="#1e293b", text_color="#94a3b8")
                
                if is_selected:
                    lbl.configure(fg_color="#b45309" if val else "#92400e")

if __name__ == "__main__":
    app = SephiriaOptimizer()
    app.mainloop()