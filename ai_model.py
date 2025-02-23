#ai_model
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import indicators
import data_handler
import drl_agent
import gym_trading_env
import risk_management
import logging

# Configurazione logging per monitorare AI in tempo reale
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VolatilityPredictor:
    """Modello AI per prevedere la volatilità futura e ottimizzare il rischio."""

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    def train(self, historical_data):
        """Allena il modello sulla volatilità passata per prevedere quella futura."""
        features = historical_data[['volume', 'price_change', 'rsi', 'bollinger_width']]
        target = historical_data['volatility']
        
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
    
    def predict_volatility(self, current_data):
        """Prevede la volatilità futura basandosi sui dati attuali."""
        return self.model.predict(current_data)

# Configurazione percorsi per archiviazione USB e locale
MODEL_DIR = "/mnt/usb_trading_data/models" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_data/models"
CLOUD_MODEL_DIR = Path("/mnt/google_drive/trading_models")  # Backup in cloud

# 📌 Assicurarsi che le directory esistano
MODEL_DIR.mkdir(parents=True, exist_ok=True)
CLOUD_MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = os.path.join(MODEL_DIR, "trading_model.h5")
XGB_MODEL_FILE = os.path.join(MODEL_DIR, "xgb_trading_model.json")

# Creazione della directory del modello se non esiste
os.makedirs(MODEL_DIR, exist_ok=True)

def create_lstm_model(input_shape):
    """Crea e restituisce un modello LSTM compilato."""
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(25))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_lstm_model(X_train, y_train, X_val, y_val):
    """Allena il modello LSTM sui dati di addestramento e validazione."""
    model = create_lstm_model((X_train.shape[1], 1))
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    history = model.fit(X_train, y_train, batch_size=32, epochs=50, validation_data=(X_val, y_val), callbacks=[early_stop])
    model.save(MODEL_FILE)
    logging.info(f"Modello LSTM salvato in {MODEL_FILE}")
    return model, history

def create_xgboost_model():
    """Crea e restituisce un modello XGBoost."""
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1)
    return model

def train_xgboost_model(X_train, y_train, X_val, y_val):
    """Allena il modello XGBoost sui dati di addestramento e validazione."""
    model = create_xgboost_model()
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=10, verbose=True)
    model.save_model(XGB_MODEL_FILE)
    logging.info(f"Modello XGBoost salvato in {XGB_MODEL_FILE}")
    return model

def load_lstm_model():
    """Carica e restituisce il modello LSTM salvato."""
    if os.path.exists(MODEL_FILE):
        model = load_model(MODEL_FILE)
        logging.info(f"Modello LSTM caricato da {MODEL_FILE}")
        return model
    else:
        logging.error(f"Il file del modello LSTM {MODEL_FILE} non esiste.")
        return None

def load_xgboost_model():
    """Carica e restituisce il modello XGBoost salvato."""
    if os.path.exists(XGB_MODEL_FILE):
        model = xgb.XGBRegressor()
        model.load_model(XGB_MODEL_FILE)
        logging.info(f"Modello XGBoost caricato da {XGB_MODEL_FILE}")
        return model
    else:
        logging.error(f"Il file del modello XGBoost {XGB_MODEL_FILE} non esiste.")
        return None

def preprocess_data(data):
    """Preprocessa i dati per l'input nel modello."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    return scaled_data, scaler

def prepare_lstm_data(data, look_back=60):
    """Prepara i dati per l'input nel modello LSTM."""
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i-look_back:i, 0])
        y.append(data[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y

def prepare_xgboost_data(data, look_back=60):
    """Prepara i dati per l'input nel modello XGBoost."""
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i-look_back:i, 0])
        y.append(data[i, 0])
    X, y = np.array(X), np.array(y)
    return X, y

def predict_with_lstm(model, data):
    """Effettua previsioni utilizzando il modello LSTM."""
    predictions = model.predict(data)
    return predictions

def predict_with_xgboost(model, data):
    """Effettua previsioni utilizzando il modello XGBoost."""
    predictions = model.predict(data)
    return predictions

def main():
    # Caricamento e preprocessamento dei dati
    data = data_handler.load_data()
    scaled_data, scaler = preprocess_data(data['close'].values.reshape(-1, 1))

    # Preparazione dei dati per LSTM
    X_lstm, y_lstm = prepare_lstm_data(scaled_data)
    X_train_lstm, X_val_lstm = X_lstm[:int(0.8*len(X_lstm))], X_lstm[int(0.8*len(X_lstm)):]
    y_train_lstm, y_val_lstm = y_lstm[:int(0.8*len(y_lstm))], y_lstm[int(0.8*len(y_lstm)):]

    # Addestramento del modello LSTM
    lstm_model, lstm_history = train_lstm_model(X_train_lstm, y_train_lstm, X_val_lstm, y_val_lstm)

    # Preparazione dei dati per XGBoost
    X_xgb, y_xgb = prepare_xgboost_data(scaled_data)
    X_train_xgb, X_val_xgb = X_xgb[:int(0.8*len(X_xgb))], X_xgb[int(0.8*len(X_xgb)):]
    y_train_xgb, y_val_xgb = y_xgb[:int(0.8*len(y_xgb))], y_xgb[int(0.8*len(y_xgb)):]

    # Addestramento del modello XGBoost
    xgb_model = train_xgboost_model(X_train_xgb, y_train_xgb, X_val_xgb, y_val_xgb)

def example_prediction():
    """Esegue una previsione di esempio con i modelli AI."""
    data = data_handler.load_data()
    scaled_data, scaler = preprocess_data(data['close'].values.reshape(-1, 1))

    # Preparazione dei dati per la previsione
    X_lstm, _ = prepare_lstm_data(scaled_data)
    X_xgb, _ = prepare_xgboost_data(scaled_data)

    # Caricamento dei modelli
    lstm_model = load_lstm_model()
    xgb_model = load_xgboost_model()

    if lstm_model:
        lstm_predictions = predict_with_lstm(lstm_model, X_lstm)
        print("📊 Previsione LSTM:", lstm_predictions[-1])

    if xgb_model:
        xgb_predictions = predict_with_xgboost(xgb_model, X_xgb)
        print("📊 Previsione XGBoost:", xgb_predictions[-1])

example_prediction()  # Esegui una previsione di esempio

# 📌 Inizializzazione e training del modello AI per la previsione della volatilità
historical_data = pd.read_csv("market_history.csv")  # Dati storici per il training
predictor = VolatilityPredictor()
predictor.train(historical_data)

# Esempio di utilizzo del predittore
current_data = np.array([[500000, 2.5, 65, 0.05]])  # Dati di mercato attuali
future_volatility = predictor.predict_volatility(current_data)
print(f"🔮 Previsione volatilità futura: {future_volatility}")
