# main (Non avvio originale)
import os
import time
import logging
import importlib
import multiprocessing
import bridge_module
import script
import functools
import requests_cache

# 📌 Configurazione avanzata del logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Configurazione del caching per le API
requests_cache.install_cache('bot_cache', expire_after=180)

# Funzione per il caching delle API
def cache_api_call(func):
    @functools.wraps(func)
    def wrapper_cache(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper_cache

# 📌 Parallel computing per migliorare le prestazioni
def start_parallel_tasks():
    """Avvia task paralleli per migliorare le prestazioni."""
    task1 = multiprocessing.Process(target=task_function_1)
    task2 = multiprocessing.Process(target=task_function_2)
    task1.start()
    task2.start()
    task1.join()
    task2.join()

# 📌 Controllo delle dipendenze prima dell'avvio
ESSENTIAL_MODULES = [
    "bridge_module", "script", "trading_bot", "data_handler",
    "risk_management", "portfolio_optimization", "drl_agent",
    "DynamicTradingManager", "ai_model", "gym_trading_env",
    "trading_environment", "indicators", "market_data",
    "market_data_apis", "data_loader", "data_api_module",
    "risk_management", "portfolio_optimization"
]

def check_dependencies():
    """Verifica che tutti i moduli essenziali siano presenti e funzionanti."""
    missing_modules = []
    for module in ESSENTIAL_MODULES:
        try:
            importlib.import_module(module)
            logging.info(f"✅ Modulo {module} caricato correttamente.")
        except ModuleNotFoundError:
            logging.error(f"❌ Modulo {module} non trovato!")
            missing_modules.append(module)

    if missing_modules:
        logging.critical(f"⛔ Il sistema non può avviarsi! Mancano i seguenti moduli: {missing_modules}")
        exit(1)

# 📌 Backup automatico prima dell'avvio
BACKUP_DIR = "/mnt/usb_trading_data/backup_main/"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def create_backup():
    """Esegue il backup del sistema prima di avviare il bot."""
    backup_file = os.path.join(BACKUP_DIR, f"backup_main_{int(time.time())}.zip")
    os.system(f"zip -r {backup_file} BOT_SUPREMO/")
    logging.info(f"✅ Backup completato in {backup_file}")

# 📌 Monitoraggio e auto-riavvio del bot
def monitor_and_restart():
    """Monitora il bot e lo riavvia automaticamente se si interrompe."""
    MAX_RETRIES = 10  # Numero massimo di tentativi di riavvio
retry_count = 0

while retry_count < MAX_RETRIES:
    process = multiprocessing.Process(target=start_bot)
    process.start()
    process.join()

    retry_count += 1
    logging.warning(f"⚠️ Il bot si è interrotto! Riavvio ({retry_count}/{MAX_RETRIES})...")
    time.sleep(5)  # Ritardo prima del riavvio

logging.critical("⛔ Il bot ha superato il numero massimo di riavvii. Controlla gli errori!")

# 📌 Avvio del bot principale
def start_bot():
    """Avvia il BOT SUPREMO e gestisce il caricamento dei moduli dinamici."""
    logging.info("🚀 Avvio del BOT SUPREMO...")

    # Controllo delle dipendenze
    check_dependencies()

    # Backup prima dell'esecuzione
    create_backup()

    # Caricamento di nuovi moduli generati automaticamente
    bridge_module.update_system_modules()

    # Avvio dello script principale di trading
    import trading_bot
    trading_bot.start_trading()

    logging.info("✅ BOT SUPREMO avviato con successo!")

# 📌 Esecuzione principale
if __name__ == "__main__":
    start_parallel_tasks()
    monitor_and_restart()
