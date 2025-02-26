#ultils
import logging
import os
from datetime import datetime
import time
import data_api_module  # Per raccogliere i dati grezzi

# Configura il logger
def setup_logger(account_id):
    """
    Set up a logger for each account.
    """
    # Verifica se la cartella 'logs' esiste, altrimenti la crea
    log_directory = r"D:\trading_data\logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Crea un logger per l'account specifico
    logger = logging.getLogger(account_id)
    logger.setLevel(logging.INFO)

    # Crea un handler per il file di log
    handler = logging.FileHandler(f'{log_directory}/{account_id}_{datetime.now().strftime("%Y-%m-%d")}.log')
    handler.setLevel(logging.INFO)

    # Definisci il formato dei log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Aggiungi il handler al logger
    logger.addHandler(handler)

    return logger

def log_trade(account_id, trade_details):
    """
    Logs a trade operation.
    """
    logger = setup_logger(account_id)
    logger.info(f"Trade executed: {trade_details}")

def log_error(account_id, error_details):
    """
    Logs errors.
    """
    logger = setup_logger(account_id)
    logger.error(f"Error: {error_details}")

# Funzione per ottenere i dati di mercato (utilizzando data_api_module)
def get_market_data(pair):
    """
    Funzione che recupera i dati di mercato per una coppia specifica.
    """
    market_data = data_api_module.get_market_data(pair)  # Chiamata al modulo per ottenere i dati grezzi
    return {
        'pair': pair,
        'price': market_data['price'],  # Prezzo di ultima transazione
        'volume': market_data['volume'],  # Volume scambiato
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Timestamp
    }

# Funzione per recuperare tutte le coppie EUR e USDT
def get_trading_pairs():
    """
    Recupera tutte le coppie di trading EUR e USDT tramite il modulo data_api_module
    """
    eur_pairs = data_api_module.get_eur_pairs()
    usdt_pairs = data_api_module.get_usdt_pairs()
    return eur_pairs + usdt_pairs

# Recupera i dati di mercato per tutte le coppie EUR e USDT
def log_market_data():
    """
    Recupera e logga i dati di mercato per tutte le coppie EUR e USDT.
    """
    pairs = get_trading_pairs()
    for pair in pairs:
        market_data = get_market_data(pair)
        log_trade('danny', market_data)  # Log per il primo account
        log_trade('giuseppe', market_data)  # Log per il secondo account

# Funzione per eliminare i log piu vecchi di max_age_days
def delete_old_logs(directory, max_age_days=30):
    """
    Elimina i file di log piu vecchi di 'max_age_days'.
    """
    now = time.time()
    for filename in os.listdir(directory):
        log_path = os.path.join(directory, filename)
        if filename.endswith('.log'):
            if os.path.isfile(log_path) and (now - os.path.getmtime(log_path) > max_age_days * 24 * 60 * 60):
                os.remove(log_path)
                print(f"Log vecchio eliminato: {log_path}")

if __name__ == "__main__":
    # Logga i dati di mercato per tutte le coppie
    log_market_data()
    delete_old_logs(r"D:\trading_data\logs", max_age_days=30)  # Rimuovi log vecchi di 30 giorni