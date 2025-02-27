# DynamicTradingManager.py
import ccxt
import json
import numpy as np
import os
import logging
import time
import requests
import shutil
from data_api_module import fetch_data_from_exchanges
import indicators
import portfolio_optimization
import risk_management

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Percorsi di Backup su USB o Cloud
USB_PATHS = [
    "/mnt/usb_trading_data/",
    "/media/usb/",
    "/mnt/external_usb/",
    "D:/trading_backup/",
    "E:/trading_backup/"
]
BACKUP_PATH = next((path for path in USB_PATHS if os.path.exists(path)), "backup_data/")
CLOUD_BACKUP = "/mnt/google_drive/trading_backup/"

class DynamicTradingManager:
    def __init__(self, top_n=10, volatility_threshold=0.02, min_volume=1000000, backup_file="trading_pairs.json"):
        """Gestisce dinamicamente la selezione delle coppie di trading."""
        self.top_n = top_n
        self.volatility_threshold = volatility_threshold
        self.min_volume = min_volume
        self.backup_file = os.path.join(BACKUP_PATH, backup_file)
        self.exchange = ccxt.binance()  # Connessione a Binance

    def fetch_eur_trading_pairs(self, retries=3, delay=2):
        """Recupera le coppie di trading in EUR con gestione avanzata della volatilità, spread e indicatori tecnici."""
        for attempt in range(retries):
            try:
                markets = self.exchange.load_markets()
                pairs = []

                for symbol, market in markets.items():
                    if "/EUR" in symbol and market['active']:
                        ticker = self.exchange.fetch_ticker(symbol)
                        volume = ticker.get('quoteVolume', 0)
                        price_change = abs(ticker.get('change', 0) / ticker.get('last', 1))
                        spread = (ticker['ask'] - ticker['bid']) / ticker['bid']  # Calcola lo spread

                        # Recupera le candele OHLCV per calcolare la volatilità recente (1h e 4h)
                        ohlcv_1h = self.exchange.fetch_ohlcv(symbol, timeframe="1h")
                        closes_1h = [candle[4] for candle in ohlcv_1h]
                        volatility_1h = np.std(closes_1h) / np.mean(closes_1h)

                        ohlcv_4h = self.exchange.fetch_ohlcv(symbol, timeframe="4h")
                        closes_4h = [candle[4] for candle in ohlcv_4h]
                        volatility_4h = np.std(closes_4h) / np.mean(closes_4h)

                        # Calcola indicatori tecnici
                        rsi = indicators.relative_strength_index(closes_1h)
                        macd, macd_signal = indicators.moving_average_convergence_divergence(closes_1h)

                        # Filtra coppie con volatilità alta, trend chiaro e spread basso
                        if (
                            volume >= self.min_volume and 
                            (volatility_1h >= self.volatility_threshold or volatility_4h >= self.volatility_threshold) and
                            spread < 0.002 and  # Evita coppie illiquide
                            rsi > 50 and macd > macd_signal  # Considera solo coppie in trend positivo
                        ):
                            pairs.append((symbol, volume, volatility_1h, volatility_4h, spread))

                # 🔹 **Selezione dinamica della strategia**
                if self.trading_strategy == "scalping" or self.trading_strategy == "intraday":
                    sort_by_volatility = True  # Se scalping o intraday, priorità a coppie più volatili
                else:
                    sort_by_volatility = False  # Se lungo termine, priorità a coppie più stabili

                # Ordina le coppie in base alla strategia scelta
                sorted_pairs = sorted(pairs, key=lambda x: (x[2] + x[3]), reverse=sort_by_volatility)
                trading_pairs = [pair[0] for pair in sorted_pairs]

                self.backup_trading_pairs(trading_pairs)
                return trading_pairs

            except Exception as e:
                logging.error(
                    f"⚠️ Errore nel recupero delle coppie EUR (tentativo {attempt+1}/{retries}): {e}"
                )
                time.sleep(delay * (2 ** attempt))  # Backoff esponenziale

        logging.error("❌ Impossibile recuperare le coppie di trading dopo più tentativi.")
        return self.load_backup_pairs()

    def backup_trading_pairs(self, trading_pairs):
        """Salva le coppie di trading in un file JSON di backup."""
        try:
            with open(self.backup_file, "w") as f:
                json.dump(trading_pairs, f)
            logging.info(f"✅ Coppie di trading salvate su {self.backup_file}")
        except Exception as e:
            logging.error(f"❌ Errore nel backup delle coppie: {e}")

    def load_backup_pairs(self):
        """Carica le coppie di trading dal file di backup."""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, "r") as f:
                    trading_pairs = json.load(f)
                logging.info(f"📂 Coppie di trading caricate dal backup.")
                return trading_pairs
            else:
                logging.warning("⚠️ Nessun file di backup trovato.")
                return []
        except Exception as e:
            logging.error(f"❌ Errore nel caricamento del backup: {e}")
            return []

    def select_trading_pairs(self):
        """Seleziona le migliori coppie di trading, caricando dal backup in caso di errore."""
        trading_pairs = self.fetch_eur_trading_pairs()
        if not trading_pairs:
            trading_pairs = self.load_backup_pairs()
        return trading_pairs

    def sync_to_cloud(self):
        """Sincronizza i dati con il cloud se la USB non è disponibile."""
        if not os.path.exists(BACKUP_PATH):
            try:
                os.makedirs(CLOUD_BACKUP, exist_ok=True)
                backup_file_path = os.path.join(CLOUD_BACKUP, "trading_pairs_backup.json")
                shutil.copy(self.backup_file, backup_file_path)
                logging.info("☁️ Dati di trading sincronizzati su Google Drive.")
            except Exception as e:
                logging.error(f"❌ Errore nel backup su Google Drive: {e}")

if __name__ == "__main__":
    manager = DynamicTradingManager()
    selected_pairs = manager.select_trading_pairs()
    logging.info(f"📊 Coppie di trading selezionate: {selected_pairs}")
    manager.sync_to_cloud()
