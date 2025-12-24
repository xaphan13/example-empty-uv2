import time
import sys
import signal
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
import logging

# Настройка логирования для лучшего понимания происходящего
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Настройки SSH сервера ---
# Замените эти данные на данные вашего удаленного SSH сервера
SSH_HOST = "your_remote_ssh_server_ip_or_hostname"  # IP или hostname вашего удаленного SSH сервера
SSH_PORT = 22  # Порт SSH (обычно 22)
SSH_USER = "your_ssh_username"  # Имя пользователя для SSH
# Выберите один из способов аутентификации: пароль или ключ
SSH_PASSWORD = "your_ssh_password"  # Пароль для SSH (закомментируйте, если используете ключ)
SSH_PKEY = (
    "/path/to/your/private/key.pem"  # Путь к вашему приватному SSH ключу (закомментируйте, если используете пароль)
)
# SSH_PASSPHRASE = 'your_key_passphrase'        # Пароль для приватного ключа (если он защищен паролем)


# --- Настройки локального SOCKS5 прокси ---
LOCAL_SOCKS_HOST = "localhost"
LOCAL_SOCKS_PORT = 1080

# --- Настройки восстановления соединения ---
RECONNECT_DELAY_SECONDS = 5  # Задержка в секундах перед попыткой восстановления

# Флаг для управления основным циклом
running = True


def signal_handler(_sig, _frame):
    """Обработчик сигналов для корректного завершения работы (например, по Ctrl+C)"""
    logging.info("\nПолучен сигнал завершения. Останавливаю туннель...")
    global running
    running = False
    # В зависимости от того, где находится выполнение (в sleep или внутри sshtunnel),
    # завершение может произойти не мгновенно. Основной цикл проверит флаг `running`.


# Регистрируем обработчики сигналов SIGINT (Ctrl+C) и SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def start_socks_tunnel():
    """Функция для старта SSH туннеля с SOCKS прокси"""
    server = None
    try:
        logging.info(f"Попытка подключения к SSH серверу {SSH_HOST}:{SSH_PORT}")

        # Создаем экземпляр SSHTunnelForwarder
        server = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            # Выбираем аутентификацию: пароль или ключ
            # ssh_password=SSH_PASSWORD if 'SSH_PASSWORD' in locals() else None,
            # ssh_pkey=SSH_PKEY if 'SSH_PKEY' in locals() else None,
            # ssh_private_key=SSH_PKEY if 'SSH_PKEY' in locals() else None, # Альтернативное имя параметра
            # ssh_private_key_password=SSH_PASSPHRASE if 'SSH_PASSPHRASE' in locals() else None,
            ssh_password=(SSH_PASSWORD if "SSH_PASSWORD" in globals() and SSH_PASSWORD else None),
            # Указываем локальный адрес и порт для SOCKS5 прокси
            # sshtunnel автоматически определяет, что это динамический (SOCKS),
            # если remote_bind_address не указан.
            ssh_tunnel_bind_address=(LOCAL_SOCKS_HOST, LOCAL_SOCKS_PORT),
            # Дополнительные опции (можно настроить):
            # connect_timeout=10, # Таймаут подключения к SSH серверу
            # ssh_keepalive=10,   # Отправлять keepalive пакеты каждые N секунд
        )

        # Запускаем туннель
        server.start()
        logging.info(f"SOCKS5 прокси успешно запущен и слушает на {LOCAL_SOCKS_HOST}:{LOCAL_SOCKS_PORT}")
        logging.info("Нажмите Ctrl+C для остановки.")

        # Держим скрипт активным, пока туннель работает и не получен сигнал на выход
        while running and server.is_alive():
            time.sleep(1)  # Проверяем состояние туннеля каждую секунду

        # Если цикл завершился, но running=True, значит туннель упал
        if running and not server.is_alive():
            logging.warning("Туннель SSH разорван. Попытка восстановления...")

    except BaseSSHTunnelForwarderError as e:
        logging.error(f"Ошибка при работе sshtunnel: {e}")
    except Exception as e:
        logging.error(f"Произошла неожиданная ошибка: {e}")

    finally:
        # Гарантируем, что туннель будет остановлен при выходе из try/except
        if server and server.is_alive():
            logging.info("Останавливаю туннель перед завершением или перезапуском...")
            try:
                server.stop()
                logging.info("Туннель остановлен.")
            except Exception as stop_e:
                logging.error(f"Ошибка при остановке туннеля: {stop_e}")
        elif server:
            logging.info("Туннель не был активен или уже остановлен.")


# --- Основной цикл для автоматического восстановления ---
if __name__ == "__main__":
    logging.info("Запуск скрипта SOCKS5 туннеля с автоматическим восстановлением.")

    while running:
        start_socks_tunnel()  # Пытаемся запустить или перезапустить туннель

        if running:
            # Если `running` все еще True, значит туннель упал или не запустился,
            # и мы ждем перед следующей попыткой.
            logging.info(f"Ожидание {RECONNECT_DELAY_SECONDS} секунд перед следующей попыткой подключения...")
            time.sleep(RECONNECT_DELAY_SECONDS)

    logging.info("Скрипт завершен.")
    sys.exit(0)
