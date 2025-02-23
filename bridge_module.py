# bridge_module.py
import os
import importlib
import logging
import shutil
import time
import ast
import threading

# 📌 Configurazione avanzata del logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Directory principale dei moduli personalizzati
MODULES_DIR = "auto_generated_modules"
BACKUP_DIR = "backup_modules"

# 📌 Creazione della directory di backup se non esiste
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# 📌 Lista dei moduli principali con dipendenze
CORE_MODULES = {
    'risk_management': ['portfolio_optimization', 'trading_bot'],  # Collegato a Portfolio Optimization e Trading Bot
    'portfolio_optimization': [],  # Modulo autonomo
    'data_handler': ['data_loader'],  # Carica i dati dallo storico e da API in Data Loader
    'indicators': [],  # Indicatori tecnici indipendenti
    'drl_agent': ['gym_trading_env', 'ai_model'],  # Collegato all'ambiente Gym e al modello AI
    'ai_model': [],  # Modello AI indipendente
    'gym_trading_env': [],  # Ambiente di simulazione per DRL
    'trading_environment': ['gym_trading_env'],  # Ambiente di trading che utilizza Gym Trading Env
    'trading_bot': ['risk_management', 'trading_environment', 'data_handler'],  # Collegato alla gestione del rischio, ambiente e dati
    'main': ['trading_bot'],  # Modulo principale che gestisce tutto il bot
    'DynamicTradingManager': ['data_api_module', 'risk_management'],  # Collegato alle API e alla gestione del rischio
    'data_api_module': ['market_data_apis.json'],  # Modulo che comunica con API di mercato
    'data_loader': ['market_data.json', 'data_handler'],  # Modulo che carica i dati di mercato e comunica con Data Handler
    'script': ['bridge_module'],  # Genera strategie e moduli, collegato al Bridge
    'bridge_module': ['script', 'main'],  # Modulo che connette tutto il sistema
}


def check_module_compatibility(module_name):
    """Verifica se il modulo esiste prima di caricarlo, evitando crash."""
    try:
        importlib.import_module(module_name)
        return True
    except ModuleNotFoundError:
        logging.warning(f"⚠️ Modulo {module_name} non trovato. Controlla se il file esiste nella directory corretta.")
        return False
    except ImportError as e:
        logging.error(f"❌ Errore di importazione del modulo {module_name}: {e}")
        return False


def backup_module(module_name):
    """Esegue backup multipli per proteggere le versioni precedenti."""
    module_path = os.path.join(MODULES_DIR, f"{module_name}.py")
    backup_paths = [
        os.path.join(BACKUP_DIR, f"{module_name}.bak1.py"),
        os.path.join(BACKUP_DIR, f"{module_name}.bak2.py"),
        os.path.join(BACKUP_DIR, f"{module_name}.bak3.py"),
    ]
    if os.path.exists(module_path):
        shutil.copy(module_path, backup_paths[2])  # Sposta la versione più recente
        shutil.copy(backup_paths[1], backup_paths[2]) if os.path.exists(backup_paths[1]) else None
        shutil.copy(backup_paths[0], backup_paths[1]) if os.path.exists(backup_paths[0]) else None
        shutil.copy(module_path, backup_paths[0])
        logging.info(f"🔒 Backup multiplo eseguito per {module_name}.")

def check_missing_imports(module_path):
    """Analizza il modulo e verifica se ci sono import mancanti."""
    required_imports = set()
    with open(module_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=module_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    required_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                required_imports.add(node.module)

    missing_imports = []
    for imp in required_imports:
        try:
            importlib.import_module(imp)
        except ModuleNotFoundError:
            missing_imports.append(imp)

    if missing_imports:
        logging.warning(f"⚠️ Modulo {module_path} ha import mancanti: {missing_imports}")
        return missing_imports
    return []

def fix_missing_imports(module_path):
    """Aggiunge automaticamente gli import mancanti."""
    missing_imports = check_missing_imports(module_path)
    if missing_imports:
        with open(module_path, "r+", encoding="utf-8") as file:
            content = file.readlines()
            file.seek(0, 0)
            for imp in missing_imports:
                file.write(f"import {imp}\n")
            file.writelines(content)
        logging.info(f"✅ Import mancanti aggiunti automaticamente in {module_path}.")

def check_missing_functions(module_path):
    """Verifica se un modulo chiama funzioni inesistenti."""
    with open(module_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=module_path)
    
    called_functions = set()
    defined_functions = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_functions.add(node.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_functions.add(node.func.id)

    missing_functions = called_functions - defined_functions

    if missing_functions:
        logging.warning(f"⚠️ Funzioni mancanti in {module_path}: {missing_functions}")
        return missing_functions
    return []

def fix_missing_functions(module_path):
    """Aggiunge automaticamente funzioni segnaposto per evitare crash."""
    missing_functions = check_missing_functions(module_path)
    if missing_functions:
        with open(module_path, "a", encoding="utf-8") as file:
            for func in missing_functions:
                file.write(f"\ndef {func}(*args, **kwargs):\n    logging.warning('⚠️ Funzione {func} non implementata!')\n    return None\n")
        logging.info(f"✅ Funzioni mancanti aggiunte automaticamente in {module_path}.")

def load_custom_modules():
    """Carica automaticamente tutti i moduli generati dinamicamente."""
    if not os.path.exists(MODULES_DIR):
        logging.info(f"📂 Creazione della cartella {MODULES_DIR} per i moduli dinamici.")
        os.makedirs(MODULES_DIR)

    module_files = [f for f in os.listdir(MODULES_DIR) if f.endswith(".py")]
    for module_file in module_files:
        module_name = module_file.replace(".py", "")
        try:
            if check_module_compatibility(module_name):
                backup_module(module_name)
                fix_missing_imports(os.path.join(MODULES_DIR, f"{module_name}.py"))
                fix_missing_functions(os.path.join(MODULES_DIR, f"{module_name}.py"))
                imported_module = importlib.import_module(f"{MODULES_DIR}.{module_name}")
                importlib.reload(imported_module)
                logging.info(f"✅ Modulo {module_name} caricato con successo.")
        except Exception as e:
            logging.error(f"❌ Errore nel caricamento del modulo {module_name}: {e}")

def load_module(module_name, class_name):
    """Carica dinamicamente un modulo e restituisce una classe specifica."""
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name, None)
    except ModuleNotFoundError:
        logging.error(f"❌ Il modulo {module_name} non è stato trovato.")
        return None
    except AttributeError:
        logging.error(f"❌ La classe {class_name} non è stata trovata nel modulo {module_name}.")
        return None


def update_system_modules():
    """Aggiorna tutti i moduli principali del sistema senza riavviare il bot, con protezione avanzata."""
    for module, dependencies in CORE_MODULES.items():
        if check_module_compatibility(module):
            try:
                backup_module(module)
                fix_missing_imports(f"{module}.py")
                fix_missing_functions(f"{module}.py")
                start_time = time.time()
                importlib.reload(importlib.import_module(module))
                execution_time = time.time() - start_time
                logging.info(f"🔄 Modulo {module} aggiornato in {execution_time:.2f} sec.")
            except Exception as e:
                logging.error(f"❌ Errore nell'aggiornare il modulo {module}: {e}")

def getattr(*args, **kwargs):
    logging.warning('⚠️ Funzione getattr non implementata!')
    return None

def open(*args, **kwargs):
    logging.warning('⚠️ Funzione open non implementata!')
    return None

def set(*args, **kwargs):
    logging.warning('⚠️ Funzione set non implementata!')
    return None

def isinstance(*args, **kwargs):
    logging.warning('⚠️ Funzione isinstance non implementata!')
    return None
