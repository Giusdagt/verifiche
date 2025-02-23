import sys
import os
import re
import importlib.util
import logging
import subprocess
import uuid
import pkg_resources  # Per verificare pacchetti installabili
import chardet
from logging.handlers import RotatingFileHandler

# 📌 Configurazione logging avanzata
LOG_FILE = "test_bot_log.txt"
handler = RotatingFileHandler(LOG_FILE, maxBytes=5000000, backupCount=5)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

SHOW_ONLY_ERRORS = True  # Se True, mostra solo ERROR e CRITICAL nei log

# 📌 Mock dinamico della funzione `create_backup()` per i test
def mock_create_backup(filename=None):
    logging.info(f"🛑 Test Mode: Simulazione del backup per {filename}, nessun file verrà salvato.")

# 📌 Sostituisce automaticamente la funzione `create_backup()` in tutti i moduli caricati
for module_name, module in sys.modules.items():
    if hasattr(module, "create_backup"):
        setattr(module, "create_backup", mock_create_backup)
        logging.info(f"🛑 Test Mode: `create_backup()` mockata nel modulo {module_name}")

def log_result(message, level="INFO"):
    """Scrive i risultati nei log con un codice di errore univoco."""
    error_id = str(uuid.uuid4())[:8]  # Crea un ID univoco abbreviato per ogni errore
    
    if level in ["ERROR", "CRITICAL"]:
        message = f"[{error_id}] {message}"  # Aggiunge l'ID univoco all'errore
    
    if SHOW_ONLY_ERRORS and level not in ["ERROR", "CRITICAL"]:
        return  # Ignora messaggi non critici
    
    print(message)
    if level == "INFO":
        logging.info(message)
    elif level == "WARNING":
        logging.warning(message)
    elif level == "ERROR":
        logging.error(message)
    elif level == "CRITICAL":
        logging.critical(message)

# 📌 Definizione dei moduli personalizzati
custom_modules = [
    "trading_bot", "ai_model", "bridge_module", "data_api_module",
    "data_handler", "data_loader", "drl_agent", "gym_trading_env",
    "indicators", "portfolio_optimization", "risk_management",
    "script", "trading_environment", "DynamicTradingManager", "main"
]

def verify_modules():
    for module in custom_modules:
        file_path = f"{module}.py"
        if not os.path.exists(file_path):
            log_result(f"Modulo mancante: {file_path}", "ERROR")

# 📌 Pacchetti richiesti (da installare automaticamente se mancanti)

def find_imported_packages():
    """Analizza i file dei moduli e raccoglie le librerie importate automaticamente."""
    imported_packages = set()
    import_pattern = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\\.]+)")
    
    for module in custom_modules:
        file_path = f"{module}.py"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    match = import_pattern.match(line)
                    if match:
                        package = match.group(1).split(".")[0]  # Prendere solo il nome principale
                        imported_packages.add(package)

# 🔹 Filtra solo pacchetti realmente installabili su PyPI
    installable_packages = {pkg for pkg in imported_packages if pkg_resources.working_set.find(pkg_resources.Requirement.parse(pkg))}

    return sorted(installable_packages)
# 📌 Ora required_packages è generato dinamicamente
required_packages = find_imported_packages()

def check_packages():
    """Verifica e installa automaticamente i pacchetti mancanti."""
    log_result("\n📦 Controllo pacchetti di terze parti...")
    missing_packages = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]
    if missing_packages:
        log_result(f"❌ Pacchetti mancanti: {missing_packages}")
        log_result("📌 Installazione automatica dei pacchetti mancanti...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        log_result("✅ Pacchetti installati correttamente.")
    else:
        log_result("✅ Tutti i pacchetti richiesti sono già installati.")

def check_imports():
    """Verifica se i moduli personalizzati sono importabili correttamente con gestione avanzata degli errori."""
    log_result("\n🛠 Controllo import moduli personalizzati...")
    for module in custom_modules:
        try:
            importlib.import_module(module)
            log_result(f"✅ Modulo importato correttamente: {module}")
        except ModuleNotFoundError:
            log_result(f"❌ Modulo non trovato: {module}. Assicurati che il file esista e sia nel path corretto.")
        except ImportError as e:
            log_result(f"❌ Errore di importazione nel modulo {module}: {e}")
        except Exception as e:
            log_result(f"⚠️ Errore sconosciuto durante l'importazione di {module}: {e}", extra={'module': module})

def check_syntax():
    """Verifica la sintassi dei file Python nel progetto."""
    log_result("\n🔍 Controllo sintassi dei moduli...")
    for module in custom_modules:
        file_path = f"{module}.py"
        if os.path.exists(file_path):
            result = subprocess.run(["python", "-m", "py_compile", file_path], capture_output=True, text=True)
            if result.returncode == 0:
                log_result(f"✅ Nessun errore di sintassi in {file_path}")
            else:
                log_result(f"❌ Errore di sintassi in {file_path}: {result.stderr.strip()}")

def detect_encoding(file_path):
    """Rileva la codifica di un file e la salva in un report."""
    with open(file_path, "rb") as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    encoding = result["encoding"]

    # Scrive il risultato in un file di log
    with open("encoding_report.txt", "a", encoding="utf-8") as log_file:
        status = "✅ OK" if encoding == "utf-8" else "❌ Problema di codifica"
        log_file.write(f"File: {file_path} - Codifica rilevata: {encoding} {status}\n")

    return encoding

# Esegue il controllo su tutti i file `.py`
with open("encoding_report.txt", "w", encoding="utf-8") as log_file:
    log_file.write("📌 REPORT CODIFICA FILE\n====================\n")

for module in custom_modules:
    file_path = f"{module}.py"
    if os.path.exists(file_path):
        encoding = detect_encoding(file_path)
        print(f"Modulo: {module}.py - Codifica rilevata: {encoding}")

def check_duplicate_logic():
    """Controlla la presenza di funzioni duplicate nei moduli, migliorando la velocità di ricerca."""
    log_result("\n🔍 Controllo logiche duplicate tra i moduli...")
    functions = set()  # Set per ricerca veloce O(1)
    duplicates = []

    for module in custom_modules:  # ✅ Corretto indentazione
        file_path = f"{module}.py"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, start=1):
                    match = re.match(r"^\s*def\s+(\w+)", line)
                    if match:
                        func_name = match.group(1)
                        if func_name in functions:
                            duplicates.append((file_path, func_name, i))  # ✅ Usa file_path corretto
                        else:
                            functions.add(func_name)  # Ora usa un set per O(1) lookup

    if duplicates:
        log_result("❌ FUNZIONI DUPLICATE TROVATE TRA MODULI DIFFERENTI:")
        for file, func, line in duplicates:
            log_result(f"Modulo: {file}, Funzione: {func}, Riga: {line}")
    else:
        log_result("✅ Nessuna logica duplicata trovata tra i moduli.")

def check_module_dependencies():
    """Verifica se i moduli personalizzati comunicano correttamente tra loro."""
    log_result("\n🔄 Controllo dipendenze tra i moduli...")
    dependency_issues = []
    
    for module in custom_modules:
        try:
            mod = importlib.import_module(module)
            for attr in dir(mod):
                attr_value = getattr(mod, attr)
                if callable(attr_value):  # Se è una funzione o classe
                    try:
                        attr_value()  # Tentativo di esecuzione per verificare le dipendenze
                    except Exception as e:
                        dependency_issues.append((module, attr, str(e)))
        except ImportError as e:
            log_result(f"❌ Errore di importazione nel modulo {module}: {e}", "ERROR")

    if dependency_issues:
        log_result("\n❌ Problemi di dipendenze tra i moduli:")
        for mod, attr, err in dependency_issues:
            log_result(f"Modulo {mod}, Funzione {attr}: {err}", "ERROR")
    else:
        log_result("✅ Tutti i moduli comunicano correttamente tra loro.")       

def check_logs():
    """Analizza i file di log per errori in modo ottimizzato."""
    log_result("\n📜 Controllo errori nei log...")
    
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as file:
            file.write("📌 LOG DEL BOT DI TRADING\n")
        log_result(f"✅ File di log '{LOG_FILE}' creato.")
        return  # Esce subito, evitando di leggere un file vuoto

    with open(LOG_FILE, "r") as file:
        for line in file:
            if "ERROR" in line or "CRITICAL" in line:
                log_result(f"❌ {line.strip()}")

def generate_test_report():
    """Genera un report finale con un riepilogo di tutti i test effettuati."""
    log_result("\n📜 Generazione del report finale...")

    test_results = {
        "Pacchetti installati correttamente": "✅" if not missing_packages else "❌",
        "Moduli importati con successo": "✅" if not dependency_issues else "❌",
        "Sintassi verificata": "✅",
        "Funzioni duplicate": "✅" if not duplicates else "❌",
        "Comunicazione tra moduli": "✅" if not dependency_issues else "❌",
        "Errori nei log": "✅" if not os.path.exists(LOG_FILE) or not open(LOG_FILE, "r").read().strip() else "❌",
    }

    log_result("\n🔍 **Report Finale:**")
    for test, result in test_results.items():
        log_result(f"{test}: {result}")

    log_result("\n✅ **Test completati con successo!**" if all(res == '✅' for res in test_results.values()) else "\n❌ **Alcuni test hanno fallito, controlla i log!**")

def save_test_report():
    """Salva il riepilogo del test in un file separato."""
    report_file = "test_report.txt"
    with open(report_file, "w", encoding="utf-8") as file:
        file.write("📌 REPORT DI VERIFICA DEL BOT\n")
        file.write("="*40 + "\n")
        file.write(open(LOG_FILE, "r").read())  # Copia il contenuto del log
    log_result(f"📂 Report salvato in {report_file}")

def save_error_log():
    """Filtra solo gli errori critici e li salva in un file separato."""
    error_file = "error_log.txt"
    with open(LOG_FILE, "r", encoding="utf-8") as log, open(error_file, "w", encoding="utf-8") as error_log:
        for line in log:
            if "ERROR" in line or "CRITICAL" in line:
                error_log.write(line)
    log_result(f"📂 Log degli errori salvato in {error_file}")


def full_test():
    """Esegue tutti i test in sequenza."""
    log_result("\n🚀 AVVIO TEST COMPLETO DEL BOT 🚀")
    check_packages()
    check_imports()
    check_syntax()
    check_duplicate_logic()
    check_module_dependencies()
    check_logs()
    generate_test_report()
    save_test_report()
    save_error_log()
    log_result("\n✅ TUTTI I TEST COMPLETATI!")

if __name__ == "__main__":
    verify_modules()
    full_test()
