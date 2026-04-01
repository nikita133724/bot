
import customtkinter as ctk

# ─── ЦВЕТОВАЯ ПАЛИТРА ──────────────────────────────────────────────────────────
# Современная темная тема с яркими акцентами.
THEME = {
    "bg_dark": "#0A0A0A",        # Темный фон окна
    "bg_card": "#121212",        # Фон карточек и панелей
    "accent_primary": "#00F5FF",  # Неоновый голубой (основной акцент)
    "accent_secondary": "#FF0055", # Рубиновый (второстепенный акцент)
    "text_main": "#E1E1E1",      # Основной текст
    "text_dim": "#808080",       # Тусклый текст (подсказки)
    "border": "#252525",         # Цвет границ
    "hover": "#1C1C1C",          # Цвет при наведении
    "success": "#00FF7F",        # Цвет успеха (зеленый)
    "error": "#FF3131"           # Цвет ошибки (красный)
}

# ─── НАСТРОЙКИ ШРИФТОВ ───────────────────────────────────────────────────────
FONTS = {
    "title": ("Orbitron", 28, "bold"),      # Заголовки
    "header": ("Inter", 18, "bold"),        # Подзаголовки
    "body": ("Inter", 14),                   # Основной текст
    "mono": ("Fira Code", 12),              # Моноширинный шрифт для логов
    "stats": ("Roboto Mono", 22, "bold")     # Шрифт для статистики
}

# ─── СТИЛИ КОМПОНЕНТОВ ──────────────────────────────────────────────────────
# Основная карточка (фрейм)
def get_card_style():
    return {
        "fg_color": THEME["bg_card"],
        "border_color": THEME["border"],
        "border_width": 1,
        "corner_radius": 12
    }

# Основная кнопка (яркая)
def get_button_primary():
    return {
        "fg_color": THEME["accent_primary"],
        "hover_color": "#00CCD6",
        "text_color": "#000000",
        "font": FONTS["body"],
        "corner_radius": 8,
        "border_width": 0,
        "height": 40
    }

# Второстепенная кнопка (прозрачная)
def get_button_secondary():
    return {
        "fg_color": "transparent",
        "border_color": THEME["accent_primary"],
        "border_width": 1,
        "hover_color": THEME["hover"],
        "text_color": THEME["accent_primary"],
        "font": FONTS["body"],
        "corner_radius": 8,
        "height": 40
    }

# Стиль поля ввода
def get_entry_style():
    return {
        "fg_color": "#000000",
        "border_color": THEME["border"],
        "border_width": 1,
        "text_color": THEME["text_main"],
        "placeholder_text_color": THEME["text_dim"],
        "corner_radius": 6
    }

# Стиль выпадающего списка
def get_combo_style():
    style = get_entry_style().copy()
    style.pop("placeholder_text_color", None) # ComboBox не поддерживает этот аргумент
    return style
