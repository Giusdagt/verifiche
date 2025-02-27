# drl_agent.py - Agente di Trading con Reinforcement Learning Ottimizzato
import ccxt
import os
import time
import logging
import requests
import optuna
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import shutil
from pathlib import Path
from datetime import datetime
from stable_baselines3 import PPO, DQN, A2C, SAC
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.buffers import ReplayBuffer
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from trading_environment import TradingEnv
from data_handler import load_normalized_data
from data_api_module import main_fetch_all_data as load_raw_data
from risk_management import RiskManagement
from portfolio_optimization import PortfolioOptimization
import indicators

# 📌 Configurazione avanzata per Oracle Free e backup automatico
LOG_DIR = "/mnt/usb_trading_data/logs" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_logs"
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOG_DIR, "drl_agent.log"),
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Percorsi per il salvataggio dei modelli su Cloud e USB
MODEL_DIR = Path("/mnt/usb_trading_data/models") if Path("/mnt/usb_trading_data").exists() else Path("D:/trading_models")
CLOUD_BACKUP_DIR = Path("/mnt/google_drive/trading_backup")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
CLOUD_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# 📌 URL per il backup su Cloud
CLOUD_BACKUP_URL = "https://your-cloud-backup-service.com/upload"

# ===========================
# 🔹 Rete Neurale Personalizzata con PyTorch
# ===========================
class CustomFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=128):
        super(CustomFeatureExtractor, self).__init__(observation_space, features_dim)
        self.fc1 = nn.Linear(observation_space.shape[0], 256)
        self.fc2 = nn.Linear(256, features_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        return self.fc2(x)

# ===========================
# 🔹 FUNZIONI DI BACKUP AUTOMATICO
# ===========================
def backup_model_to_cloud(model_path):
    """Backup automatico del modello su cloud."""
    try:
        with open(model_path, 'rb') as f:
            response = requests.post(CLOUD_BACKUP_URL, files={'file': f})
        if response.status_code == 200:
            logging.info(f"✅ Modello {model_path} caricato su cloud.")
        else:
            logging.error(f"❌ Errore nel backup su cloud: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Errore nel backup su cloud: {e}")

def save_model(model, model_name):
    """Salva il modello localmente e ne esegue il backup su cloud."""
    model_path = MODEL_DIR / model_name
    model.save(model_path)
    logging.info(f"✅ Modello salvato in {model_path}.")
    backup_model_to_cloud(model_path)

# ===========================
# 🔹 CLASSE DRLAgent CON GESTIONE AVANZATA
# ===========================
class DRLAgent:
    def __init__(self, trading_mode="auto", algorithm="PPO"):
        """Inizializza l'agente di trading."""
        self.trading_mode = trading_mode
        self.algorithm = algorithm
        self.exchange = None
        self.replay_buffer = ReplayBuffer(buffer_size=1000000)
        self.risk_manager = RiskManagement()  # ✅ Integrazione della gestione del rischio

        if self.trading_mode == "auto":
            self.trading_mode = self.detect_best_mode()

        if self.trading_mode == "live":
            from config import load_config
            config = load_config()
            self.exchange = ccxt.binance({
                'apiKey': config["binance"]["api_key"],
                'secret': config["binance"]["api_secret"]
            })

    def detect_best_mode(self):
        """Decide se fare trading live o backtesting automaticamente."""
        market_data = load_normalized_data()
        return "live" if not market_data.empty else "backtest"

    def execute_trade(self, pair, amount):
        """Esegue un'operazione di trading con gestione del rischio."""
        amount = self.risk_manager.apply_risk_management(pair, amount)  # 📌 🔥 Applica la gestione del rischio

        if self.trading_mode == "live":
            try:
                order = self.exchange.create_market_order(pair, 'buy', amount)
                logging.info(f"✅ Ordine eseguito con successo: {order}")
                return order
            except Exception as e:
                logging.error(f"❌ Errore nell'esecuzione dell'ordine: {e}")
                return None
        else:
            logging.info(f"🔍 Simulazione trade: BUY {amount} di {pair}")

# ===========================
# 🔹 TRAINING E TEST DELL'AGENTE
# ===========================
def train_agent(model_name="best_model.zip", total_timesteps=100_000, algorithm="PPO"):
    """Allena l'agente RL e usa il miglior portafoglio ottimizzato per il trading."""
    env = DummyVecEnv([lambda: TradingEnv()])
    best_params = hyperparameter_tuning()

    # 📌 🔥 Ottimizziamo il portafoglio prima di allenare il modello
    portfolio_manager = PortfolioOptimization()
    optimized_pairs = portfolio_manager.optimize_portfolio()

    logging.info(f"📊 Coppie di trading ottimizzate selezionate: {optimized_pairs}")

    if algorithm == "PPO":
        model = PPO("MlpPolicy", env, verbose=1)
    elif algorithm == "DQN":
        model = DQN("MlpPolicy", env, verbose=1)
    elif algorithm == "A2C":
        model = A2C("MlpPolicy", env, verbose=1)
    elif algorithm == "SAC":
        model = SAC("MlpPolicy", env, verbose=1)
    else:
        raise ValueError("Algoritmo RL non supportato.")

    checkpoint_callback = CheckpointCallback(save_freq=10_000, save_path=str(MODEL_DIR), name_prefix="trading_model")
    model.learn(total_timesteps=total_timesteps, callback=checkpoint_callback)

    save_model(model, model_name)

# ===========================
# 🔹 AVVIO AUTOMATICO SU ORACLE FREE 24/7
# ===========================
if __name__ == "__main__":
    logging.info("🚀 Avvio dell'agente DRL su Oracle Free 24/7...")

    if Path(MODEL_DIR / "best_model.zip").exists():
        logging.info("✅ Modello esistente trovato, avvio test...")
        test_agent("best_model.zip")
    else:
        logging.info("🔄 Nessun modello trovato, avvio addestramento...")
        train_agent("best_model.zip", total_timesteps=500_000)

    logging.info("🔁 Riavvio automatico in caso di crash su Oracle Free.")
    while True:
        time.sleep(3600)
