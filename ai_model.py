# ai_model.py - Modello AI per il trading automatico
import os
import pandas as pd
import logging
import numpy as np
import xgboost as xgb
from datetime import datetime
from pathlib import Path
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from indicators import TradingIndicators
from data_handler import load_data
from drl_agent import DRLAgent
from gym_trading_env import TradingEnv
from risk_management import RiskManagement

# 📌 Configurazione logging per monitorare AI in tempo reale
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 📌 Percorsi per il salvataggio dei modelli su USB e Cloud
MODEL_DIR = Path("/mnt/usb_trading_data/models") if Path(
    "/mnt/usb_trading_data").exists() else Path("D:/trading_data/models")
CLOUD_MODEL_DIR = Path("/mnt/google_drive/trading_models")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
CLOUD_MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "trading_model.h5"
XGB_MODEL_FILE = MODEL_DIR / "xgb_trading_model.json"

# ===========================
# 🔹 Modello AI per la previsione della volatilità
# ===========================
class VolatilityPredictor:
    """Modello AI per prevedere la volatilità futura e ottimizzare il rischio."""

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    def train(self, historical_data):
        """Allena il modello sulla volatilità passata per prevedere quella futura."""
        features = historical_data[['volume', 'price_change', 'rsi', 'bollinger_width']]
        target = historical_data['volatility']

        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

    def predict_volatility(self, current_data):
        """Prevede la volatilità futura basandosi sui dati attuali."""
        return self.model.predict(current_data)

# ===========================
# 🔹 Creazione e Addestramento dei Modelli AI
# ===========================
def create_lstm_model(input_shape):
    """Crea e restituisce un modello LSTM compilato."""
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_lstm_model(X_train, y_train, X_val, y_val):
    """Allena il modello LSTM sui dati di addestramento e validazione."""
    model = create_lstm_model((X_train.shape[1], 1))
    early_stop = EarlyStopping(
        monitor='val_loss', patience=5, restore_best_weights=True)
    model.fit(X_train, y_train, batch_size=32, epochs=50,
              validation_data=(X_val, y_val), callbacks=[early_stop])
    model.save(MODEL_FILE)
    logging.info(f"✅ Modello LSTM salvato in {MODEL_FILE}")
    return model

def create_xgboost_model():
    """Crea e restituisce un modello XGBoost."""
    return xgb.XGBRegressor(objective='reg:squarederror',
                            n_estimators=100, learning_rate=0.1)

def train_xgboost_model(X_train, y_train, X_val, y_val):
    """Allena il modello XGBoost sui dati di addestramento e validazione."""
    model = create_xgboost_model()
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
              early_stopping_rounds=10, verbose=True)
    model.save_model(XGB_MODEL_FILE)
    logging.info(f"✅ Modello XGBoost salvato in {XGB_MODEL_FILE}")
    return model

def load_lstm_model():
    """Carica e restituisce il modello LSTM salvato."""
    if MODEL_FILE.exists():
        model = load_model(MODEL_FILE)
        logging.info(f"✅ Modello LSTM caricato da {MODEL_FILE}")
        return model
    logging.error(f"❌ Il file del modello LSTM {MODEL_FILE} non esiste.")
    return None

def load_xgboost_model():
    """Carica e restituisce il modello XGBoost salvato."""
    if XGB_MODEL_FILE.exists():
        model = xgb.XGBRegressor()
        model.load_model(XGB_MODEL_FILE)
        logging.info(f"✅ Modello XGBoost caricato da {XGB_MODEL_FILE}")
        return model
    logging.error(f"❌ Il file del modello XGBoost {XGB_MODEL_FILE} non esiste.")
    return None

# ===========================
# 🔹 Preprocessing Dati
# ===========================
def preprocess_data(data):
    """Preprocessa i dati per l'input nel modello."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    return scaler.fit_transform(data), scaler

def prepare_lstm_data(data, look_back=60):
    """Prepara i dati per l'input nel modello LSTM."""
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i-look_back:i, 0])
        y.append(data[i, 0])
    return np.array(X).reshape(-1, look_back, 1), np.array(y)

def prepare_xgboost_data(data, look_back=60):
    """Prepara i dati per l'input nel modello XGBoost."""
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i-look_back:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

# ===========================
# 🔹 Funzioni per le Previsioni
# ===========================
def predict_with_lstm(model, data):
    """Effettua previsioni utilizzando il modello LSTM."""
    return model.predict(data)

def predict_with_xgboost(model, data):
    """Effettua previsioni utilizzando il modello XGBoost."""
    return model.predict(data)

# ===========================
# 🔹 Esecuzione del Modello AI
# ===========================
def example_prediction():
    """Esegue una previsione di esempio con i modelli AI."""
    data = load_data()
    scaled_data, _ = preprocess_data(data['close'].values.reshape(-1, 1))

    X_lstm, _ = prepare_lstm_data(scaled_data)
    X_xgb, _ = prepare_xgboost_data(scaled_data)

    lstm_model = load_lstm_model()
    xgb_model = load_xgboost_model()

    if lstm_model:
        lstm_predictions = predict_with_lstm(lstm_model, X_lstm)
        print(f"📊 Previsione LSTM: {lstm_predictions[-1]}")

    if xgb_model:
        xgb_predictions = predict_with_xgboost(xgb_model, X_xgb)
        print(f"📊 Previsione XGBoost: {xgb_predictions[-1]}")

if __name__ == "__main__":
    logging.info("🚀 Avvio del modello AI per il trading automatico.")
    example_prediction()
