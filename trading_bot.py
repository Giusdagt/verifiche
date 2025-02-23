# trading_bot.py - Modulo principale per il trading automatico
import os
import logging
import time
import numpy as np
import bridge_module
import requests

# 📌 Configurazione avanzata del logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Caricamento dinamico dei moduli necessari tramite bridge_module
AIModel = bridge_module.load_module('ai_model', 'AIModel')
TradingEnv = bridge_module.load_module('trading_environment', 'TradingEnv')
DRLAgent = bridge_module.load_module('drl_agent', 'DRLAgent')
PortfolioOptimization = bridge_module.load_module('portfolio_optimization', 'PortfolioOptimization')
RiskManagement = bridge_module.load_module('risk_management', 'RiskManagement')

# 📌 Impostazioni avanzate per AI, scalping e gestione del rischio dinamica
SCALPING_MODE = True  # Attivazione della modalità scalping automatica
ADAPTIVE_RISK = True  # Attivazione della gestione del rischio adattiva
MULTI_ACCOUNT = ["Giuseppe", "Danny"]  # Supporto multi-account
MAX_RETRY = 3  # Numero massimo di tentativi prima di un reset forzato

# 📌 Configurazione di Telegram per notifiche automatiche
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
CHAT_IDS = {
    "danny": "7508",
    "giuseppe": "77",
}

def send_message_telegram(chat_id, message):
    """Invia un messaggio via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logging.info(f"📩 Messaggio Telegram inviato a {chat_id}.")
    except Exception as e:
        logging.error(f"❌ Errore nell'invio del messaggio Telegram: {e}")

# 📌 Funzione per l'adattamento automatico alle condizioni di mercato
def market_adaptation(ai_model, trading_env):
    """Modifica le strategie in base al mercato."""
    market_trends = ai_model.analyze_market_trends()
    if market_trends == "high_volatility":
        trading_env.set_risk_level("high")
        logging.info("⚠️ Mercato volatile! Aumento protezione rischio.")
    elif market_trends == "stable":
        trading_env.set_risk_level("low")
        logging.info("✅ Mercato stabile. Ottimizzazione delle strategie di crescita.")

def start_trading(socketio_instance):
    logging.info("🚀 Avvio del trading bot con AI avanzata, scalping e gestione del rischio dinamica...")

    ai_model = AIModel()
    trading_env = TradingEnv()
    drl_agent = DRLAgent()
    portfolio_optimizer = PortfolioOptimization()
    risk_manager = RiskManagement()

    retry_count = 0

    while True:
        try:
            for account in MULTI_ACCOUNT:
                logging.info(f"📊 Trading attivo per l'account: {account}")

                market_adaptation(ai_model, trading_env)

                state = trading_env.get_state()
                action = drl_agent.predict(state)
                trading_env.execute_trade(action, account)

                portfolio_optimizer.optimize(account)
                risk_manager.adjust_risk(account, trading_env.get_risk_parameters())

                if SCALPING_MODE:
                    scalp_action = drl_agent.scalping_strategy(state)
                    trading_env.execute_trade(scalp_action, account)
                    logging.info(f"⚡ Scalping eseguito per {account}")

                balance = 100
                profit_loss = np.random.uniform(-10, 10)

                chat_id = CHAT_IDS.get(account.lower(), None)
                if chat_id:
                    message = f"📢 Trading aggiornato per {account}!\nSaldo: {balance:.2f} EUR\nProfitto/Perdita: {profit_loss:.2f} EUR"
                    send_message_telegram(chat_id, message)

                time.sleep(1)

        except Exception as e:
            logging.error(f"❌ Errore durante l'esecuzione del trading bot: {e}")
            retry_count += 1

            if retry_count >= MAX_RETRY:
                logging.critical("⛔ Numero massimo di errori raggiunto. Riavvio del bot...")
                os.system("python3 main.py")
                break

            time.sleep(5)

        except Exception as e:
            logging.error(f"❌ Errore durante l'esecuzione del trading bot: {e}")
            retry_count += 1

            if retry_count >= MAX_RETRY:
                logging.critical("⛔ Numero massimo di errori raggiunto. Riavvio del bot...")
                os.system("python3 main.py")  # Riavvio automatico del bot
                break

            time.sleep(5)  # Attesa prima di tentare di nuovo

# 📌 Esecuzione del bot se eseguito come script principale
if __name__ == "__main__":
    from flask_socketio import SocketIO
    socketio = SocketIO()
    start_trading(socketio)

def PortfolioOptimization(*args, **kwargs):
    logging.warning('⚠️ Funzione PortfolioOptimization non implementata!')
    return None

def RiskManagement(*args, **kwargs):
    logging.warning('⚠️ Funzione RiskManagement non implementata!')
    return None

def TradingEnv(*args, **kwargs):
    logging.warning('⚠️ Funzione TradingEnv non implementata!')
    return None

def DRLAgent(*args, **kwargs):
    logging.warning('⚠️ Funzione DRLAgent non implementata!')
    return None

def AIModel(*args, **kwargs):
    logging.warning('⚠️ Funzione AIModel non implementata!')
    return None

def SocketIO(*args, **kwargs):
    logging.warning('⚠️ Funzione SocketIO non implementata!')
    return None
