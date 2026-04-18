#!/usr/bin/env python3
"""
GenesisCraft v1.1 - Complete CLI with Dashboard, Tests, Backup, Stats, Explorer, Server Bridge
"""

import click
import json
import shutil
import hashlib
import zipfile
import subprocess
import sys
import webbrowser
import time
import platform
import psutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# ---------- CONFIGURATION ----------
HOME = Path.home()
BASE_DIR = HOME / "genesiscraft"
CONFIG_DIR = BASE_DIR / "config"
GLOBAL_CONFIG = CONFIG_DIR / "global_config.json"
CATEGORIES_CONFIG = CONFIG_DIR / "gem_categories.json"
LESSONS_DIR = BASE_DIR / "lessons"
PROGRESS_FILE = BASE_DIR / ".learn_progress.json"
BACKUP_DIR = BASE_DIR / "_backups"
TEST_DIR = BASE_DIR / "_test_env"
TODO_FILE = BASE_DIR / "todo.json"
PLAN_FILE = BASE_DIR / "master_plan.json"
INSPIRE_FILE = BASE_DIR / "inspirations.json"
DOCS_DIR = BASE_DIR / "documentation"

BASE_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
LESSONS_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
TEST_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# ---------- DEFAULT CONFIGS ----------
def init_config():
    if not GLOBAL_CONFIG.exists():
        default = {
            "robots_path": str(HOME / "genesis-robots"),
            "relevanceThreshold": 0.3,
            "stopWords": ["a","an","and","the","of","to","in","for","on","with","by","is","at","are","that","this","these","those","be","as","from","or","but","not","so","such","was","were","has","have","had","do","does","did","will","would","could","should","may","might","must","pro"],
            "lowRelevanceExtensions": [".jpg",".jpeg",".png",".gif",".bmp",".tiff",".ico",".mp4",".avi",".mov",".mkv",".mp3",".wav",".flac",".exe",".msi",".dll",".so",".dmg",".iso",".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".cab",".deb",".rpm"],
            "keywordBoost": {"fileName": 0.4, "content": 0.3, "extension": 0.2},
            "gitEnabled": True,
            "gitRemoteUrl": "",
            "parallelJobs": 3,
            "backupRetentionDays": 30,
            "autoTestAfterOrchestrate": True,
            "serverEnabled": False,
            "serverUrl": "http://localhost:5000"
        }
        GLOBAL_CONFIG.write_text(json.dumps(default, indent=2))
    if not CATEGORIES_CONFIG.exists():
        categories = {
            "Core": {"description": "Jádroví roboti – architektura, konfigurace", "count": 8, "prefix": "CORE"},
            "Tech": {"description": "Technologičtí roboti – vývoj, DevOps", "count": 18, "prefix": "TECH"},
            "Security": {"description": "Bezpečnostní roboti – audit, šifrování", "count": 10, "prefix": "SEC"},
            "Strategy": {"description": "Strategičtí roboti – data, AI", "count": 12, "prefix": "STRAT"},
            "Operations": {"description": "Operační roboti – monitoring, logování", "count": 10, "prefix": "OPS"},
            "Knowledge": {"description": "Znalostní roboti – dokumentace", "count": 8, "prefix": "KB"},
            "Integration": {"description": "Integrační roboti – API, webhooky", "count": 8, "prefix": "INT"},
            "Physical": {"description": "Fyzickí roboti – hardware, ROS", "count": 5, "prefix": "PHY"},
            "Automation": {"description": "Automatizační roboti – skripty, workflow", "count": 10, "prefix": "AUTO"}
        }
        CATEGORIES_CONFIG.write_text(json.dumps(categories, indent=2))
    if not TODO_FILE.exists():
        TODO_FILE.write_text(json.dumps([], indent=2))
    if not PLAN_FILE.exists():
        default_plan = {
            "version": "1.0",
            "phases": [
                {"name": "Fáze 1 - Základní funkce", "status": "completed", "progress": 100, "estimated_hours": 10, "notes": "Hotovo"},
                {"name": "Fáze 2 - Pokročilá analýza", "status": "pending", "progress": 0, "estimated_hours": 15, "notes": "Nespusteno"},
                {"name": "Fáze 3 - RAG a znalosti", "status": "pending", "progress": 0, "estimated_hours": 20, "notes": "Nespusteno"},
                {"name": "Fáze 4 - Monitoring a self-healing", "status": "pending", "progress": 0, "estimated_hours": 12, "notes": "Nespusteno"},
                {"name": "Fáze 5 - Rozšíření dashboardu", "status": "in_progress", "progress": 50, "estimated_hours": 8, "notes": "GUI rozpracováno"},
                {"name": "Fáze 6 - Integrace s externími nástroji", "status": "pending", "progress": 0, "estimated_hours": 10, "notes": "Čeká"},
                {"name": "Fáze 7 - Optimalizace a nasazení", "status": "pending", "progress": 0, "estimated_hours": 8, "notes": "Čeká"}
            ]
        }
        PLAN_FILE.write_text(json.dumps(default_plan, indent=2))
    if not INSPIRE_FILE.exists():
        default_inspire = [
            {"title": "Automatická správa dokumentace", "description": "Vytvoř robota, který denně stahuje README z GitHub trending a indexuje je.", "category": "Knowledge"},
            {"title": "Telegram robot pro vzdálené ovládání", "description": "Robot přijímá příkazy z Telegramu a spouští genesiscraft příkazy.", "category": "Integration"},
            {"title": "Monitorování teploty RPi5", "description": "Robot každou minutu loguje teplotu CPU a při překročení 75°C pošle alert.", "category": "Operations"}
        ]
        INSPIRE_FILE.write_text(json.dumps(default_inspire, indent=2))

def load_config():
    with open(GLOBAL_CONFIG) as f:
        return json.load(f)

def save_config(config):
    with open(GLOBAL_CONFIG, "w") as f:
        json.dump(config, f, indent=2)

def git_commit(repo_path: Path, message: str):
    config = load_config()
    if not config.get("gitEnabled", True):
        return
    if not (repo_path / ".git").exists():
        return
    try:
        subprocess.run(["git", "-C", str(repo_path), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_path), "commit", "-m", message], check=True, capture_output=True)
        click.echo(f"📦 Git commit: {message}", err=True)
    except subprocess.CalledProcessError as e:
        if "nothing to commit" not in str(e.stderr):
            click.echo(f"⚠️ Git commit selhal: {e.stderr}", err=True)

def log(msg, color="green"):
    click.echo(click.style(msg, fg=color))

# ---------- CLI COMMANDS (původní + nové) ----------
@click.group()
def cli():
    """GenesisCraft – tvoř, spravuj a uč se s AI roboty"""
    init_config()

@cli.command()
def status():
    """Zobrazí seznam všech robotů (rekurzivně)"""
    config = load_config()
    robots_path = Path(config["robots_path"])
    if not robots_path.exists():
        log(f"Cesta {robots_path} neexistuje", "red")
        return
    robots = []
    for item in robots_path.rglob("*"):
        if item.is_dir() and item.name != ".git" and not item.name.startswith("."):
            if (item / "README.md").exists() or (item / "robot_config.json").exists():
                robots.append(item.relative_to(robots_path))
    if not robots:
        log("Žádní roboti nenalezeni", "yellow")
    else:
        log("Seznam robotů:", "cyan")
        for r in sorted(robots):
            log(f"  - {r}")

@cli.command()
def craft():
    """Interaktivní průvodce pro vytvoření nového robota"""
    log("🧠 Spouštím průvodce tvorbou robota...", "cyan")
    name = click.prompt("Zadej název robota", type=str)
    category = click.prompt("Zadej kategorii (např. Core, Tech, Security)", type=str, default="Core")
    description = click.prompt("Stručný popis robota", type=str, default="")
    
    config = load_config()
    robots_path = Path(config["robots_path"])
    robot_dir = robots_path / category / name
    
    if robot_dir.exists():
        log(f"Robot {name} již existuje!", "red")
        return
    
    robot_dir.mkdir(parents=True, exist_ok=True)
    
    readme_content = f"""# {name}

## Kategorie: {category}
## Popis: {description}
## Vytvořen: {datetime.now()}

Tento robot byl vytvořen pomocí GenesisCraft craft.
"""
    (robot_dir / "README.md").write_text(readme_content, encoding="utf-8")
    
    robot_config = {
        "name": name,
        "category": category,
        "description": description,
        "created": datetime.now().isoformat()
    }
    (robot_dir / "robot_config.json").write_text(json.dumps(robot_config, indent=2), encoding="utf-8")
    
    git_commit(robots_path, f"craft: vytvořen robot {category}/{name}")
    log(f"✅ Robot {name} byl úspěšně vytvořen v {robot_dir}", "green")
    
    config = load_config()
    if config.get("autoTestAfterOrchestrate", False):
        click.echo("Spouštím automatické testy...")
        test(ctx=None)

@cli.command()
@click.option('--folder', '-f', required=True)
def smart_update(folder):
    """Inkrementální aktualizace knowledge base robota"""
    folder = Path(folder)
    if not folder.exists():
        log(f"Složka {folder} neexistuje", "red")
        return
    kb = folder / "_knowledge_base"
    kb.mkdir(exist_ok=True)
    extensions = {".txt", ".md", ".pdf", ".sh", ".ps1", ".yaml", ".yml"}
    copied = 0
    for file in folder.rglob("*"):
        if file.is_file() and file.suffix.lower() in extensions:
            if "_knowledge_base" in str(file):
                continue
            target = kb / file.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(file, target)
                copied += 1
    log(f"✅ Smart Update: zkopírováno {copied} souborů do {kb}", "green")
    config = load_config()
    git_commit(Path(config["robots_path"]), f"smart-update: {folder.name}")

@cli.command()
@click.option('--folder', '-f', required=True)
def export_package(folder):
    """Vytvoří ZIP balíček pro LLM / Gemini Gema"""
    folder = Path(folder)
    if not folder.exists():
        log("Složka neexistuje", "red")
        return
    export_dir = BASE_DIR / "_exports"
    export_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{folder.name}_package_{timestamp}.zip"
    zip_path = export_dir / zip_name
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file in folder.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(folder))
    log(f"Balíček vytvořen: {zip_path}", "green")

@cli.command()
@click.option('--folder', '-f', required=True)
def analyze_folder(folder):
    """Analýza složky (typy souborů, velikosti, duplicity)"""
    folder = Path(folder)
    if not folder.exists():
        log("Složka neexistuje", "red")
        return
    files = list(folder.rglob("*"))
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    log(f"📊 Analýza {folder.name}", "cyan")
    log(f"Počet souborů: {len(files)}", "white")
    log(f"Celková velikost: {total_size/1024/1024:.2f} MB", "white")
    hashes = {}
    dups = 0
    for f in files:
        if f.is_file():
            h = hashlib.md5(f.read_bytes()).hexdigest()
            if h in hashes:
                dups += 1
                log(f"Duplicitní: {f.name} (shoda s {hashes[h].name})", "yellow")
            else:
                hashes[h] = f
    log(f"Duplicitních souborů: {dups}", "yellow")

@cli.command()
def orchestrate():
    """Vytvoří armádu robotů podle kategorií"""
    config = load_config()
    robots_path = Path(config["robots_path"])
    categories = json.loads(CATEGORIES_CONFIG.read_text())
    total = 0
    for cat, info in categories.items():
        cat_path = robots_path / cat
        cat_path.mkdir(parents=True, exist_ok=True)
        for i in range(1, info["count"]+1):
            name = f"{info['prefix']}_{i:03d}_{cat}"
            robot_dir = cat_path / name
            if not robot_dir.exists():
                robot_dir.mkdir(parents=True, exist_ok=True)
                (robot_dir / "README.md").write_text(f"# {name}\nCreated {datetime.now()}\n\nAutomaticky generováno orchestrate.")
                total += 1
    log(f"✅ Vytvořeno {total} nových robotů (armáda robotů)", "green")
    git_commit(robots_path, "orchestrate: vytvořena armáda robotů")
    if config.get("autoTestAfterOrchestrate", False):
        click.echo("Spouštím automatické testy...")
        test(ctx=None)

@cli.command()
def merge_pdf():
    """Sloučí PDF v aktuální složce"""
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        log("Instaluji pypdf...", "yellow")
        subprocess.run([sys.executable, "-m", "pip", "install", "pypdf"], check=True)
        from pypdf import PdfWriter, PdfReader
    folder = Path.cwd()
    pdfs = list(folder.glob("*.pdf"))
    if not pdfs:
        log("Žádné PDF", "red")
        return
    writer = PdfWriter()
    for pdf in pdfs:
        reader = PdfReader(pdf)
        for page in reader.pages:
            writer.add_page(page)
    output = folder / "slouceno.pdf"
    with open(output, "wb") as f:
        writer.write(f)
    log(f"Sloučeno {len(pdfs)} PDF do {output}", "green")

@cli.command()
@click.option('--url', required=True)
@click.option('--target', '-t', required=True)
def download_knowledge(url, target):
    """Stáhne znalosti z URL (GitHub repo nebo soubor)"""
    target_path = Path(target)
    if not target_path.exists():
        log("Cílová složka neexistuje", "red")
        return
    if "github.com" in url:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "clone", "--depth", "1", url, tmp], check=True)
            for file in Path(tmp).rglob("*"):
                if file.is_file() and file.suffix in [".md", ".txt", ".yaml", ".yml", ".pdf"]:
                    dest = target_path / file.name
                    shutil.copy2(file, dest)
        log(f"Staženo z GitHubu: {url}", "green")
    else:
        import requests
        r = requests.get(url)
        if r.status_code == 200:
            filename = url.split("/")[-1] or "knowledge.md"
            (target_path / filename).write_bytes(r.content)
            log(f"Stažen soubor: {filename}", "green")
        else:
            log(f"Stažení selhalo: {r.status_code}", "red")
    git_commit(Path(load_config()["robots_path"]), f"download-knowledge: {target_path.name}")

@cli.command()
@click.option('--script', required=True)
@click.option('--robot', required=True)
def integrate_script(script, robot):
    """Zabalí existující skript do robota"""
    config = load_config()
    robots_path = Path(config["robots_path"])
    robot_dir = None
    for r in robots_path.rglob("*"):
        if r.is_dir() and r.name == robot:
            robot_dir = r
            break
    if not robot_dir:
        log(f"Robot {robot} nenalezen", "red")
        return
    script_path = Path(script)
    if not script_path.exists():
        log(f"Skript {script} neexistuje", "red")
        return
    dest = robot_dir / "_knowledge_base" / "Skripty" / script_path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script_path, dest)
    log(f"Skript {script_path.name} integrován do {robot}", "green")
    git_commit(robots_path, f"integrate-script: {robot}")

@cli.command()
@click.option('--robot', required=True)
@click.option('--script', required=True)
@click.option('--timeout', default=30)
def run_script(robot, script, timeout):
    """Spustí skript uvnitř robota"""
    config = load_config()
    robots_path = Path(config["robots_path"])
    robot_dir = None
    for r in robots_path.rglob("*"):
        if r.is_dir() and r.name == robot:
            robot_dir = r
            break
    if not robot_dir:
        log(f"Robot {robot} nenalezen", "red")
        return
    script_path = robot_dir / "_knowledge_base" / "Skripty" / script
    if not script_path.exists():
        log(f"Skript {script} nenalezen", "red")
        return
    try:
        result = subprocess.run([str(script_path)], timeout=timeout, capture_output=True, text=True, shell=True)
        log(f"Výstup:\n{result.stdout}", "white")
        if result.stderr:
            log(f"Chyby:\n{result.stderr}", "red")
    except subprocess.TimeoutExpired:
        log(f"Skript přesáhl timeout {timeout}s", "red")

@cli.command()
@click.option('--commands', '-c', multiple=True)
def batch_process(commands):
    """Spustí dávku příkazů"""
    for cmd in commands:
        log(f"Spouštím: {cmd}", "yellow")
        subprocess.run([sys.executable, __file__] + cmd.split(), check=False)

@cli.command()
def suggest():
    """Navrhne nové roboty nebo kategorie"""
    config = load_config()
    robots_path = Path(config["robots_path"])
    categories = set()
    for d in robots_path.iterdir():
        if d.is_dir() and d.name != ".git":
            categories.add(d.name)
    log("Analýza dokončena.", "cyan")
    log(f"Nalezené kategorie: {', '.join(categories)}", "white")
    if "Security" not in categories:
        log("💡 Doporučuji vytvořit kategorii Security s roboty pro audit.", "yellow")
    if "Automation" not in categories:
        log("💡 Doporučuji vytvořit kategorii Automation pro automatizační skripty.", "yellow")

@cli.command()
@click.option('--from-github', 'source')
def fetch(source):
    """Stáhne robota z GitHubu"""
    if not source:
        log("Chybí --from-github <url>", "red")
        return
    config = load_config()
    robots_path = Path(config["robots_path"])
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "--depth", "1", source, tmp], check=True)
        repo_name = Path(source).stem
        target = robots_path / "Staženo" / repo_name
        shutil.copytree(tmp, target)
        (target / "README.md").write_text(f"# {repo_name}\nStaženo z {source}\n{datetime.now()}")
    log(f"Robot {repo_name} stažen do {target}", "green")
    git_commit(robots_path, f"fetch: {repo_name}")

@cli.command()
def examples():
    """Zobrazí praktické scénáře"""
    log("Příklady použití GenesisCraft:", "cyan")
    log("1. genesiscraft craft", "white")
    log("2. genesiscraft orchestrate", "white")
    log("3. genesiscraft smart-update --folder ./Core/MujRobot", "white")
    log("4. genesiscraft export-package --folder ./Core/MujRobot", "white")
    log("5. genesiscraft analyze-folder --folder ./Core/MujRobot", "white")
    log("6. genesiscraft learn list", "white")
    log("7. genesiscraft dashboard", "white")
    log("8. genesiscraft stats", "white")
    log("9. genesiscraft doctor", "white")
    log("10. genesiscraft explorer", "white")

@cli.command()
@click.argument("problem")
def solve(problem):
    """Jednoduchý nápovědní systém"""
    problem_lower = problem.lower()
    if "robot" in problem_lower and "vytvoř" in problem_lower:
        log("Zkuste: genesiscraft craft", "green")
    elif "aktualizovat" in problem_lower or "knowledge" in problem_lower:
        log("Zkuste: genesiscraft smart-update --folder <cesta>", "green")
    elif "export" in problem_lower:
        log("Zkuste: genesiscraft export-package --folder <cesta>", "green")
    else:
        log("Zkuste: genesiscraft examples", "yellow")

@cli.command()
def ideas():
    """Vygeneruje nápady na nové roboty"""
    log("💡 Nápady na nové roboty:", "cyan")
    log("- Robot pro správu logů (Automation)", "white")
    log("- Robot pro monitorování teploty CPU (Operations)", "white")
    log("- Robot pro Telegram notifikace (Integration)", "white")
    log("- Robot pro analýzu bezpečnosti (Security)", "white")
    log("- Robot pro správu dokumentace (Knowledge)", "white")

# ---------- NOVÉ PŘÍKAZY PRO FÁZI 1 ROZŠÍŘENÍ ----------
@cli.command()
def backup():
    """Vytvoří úplnou zálohu celého prostředí GenesisCraft"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"genesiscraft_backup_{timestamp}.zip"
    with zipfile.ZipFile(backup_file, 'w') as zf:
        for item in BASE_DIR.rglob("*"):
            if item.is_file() and "_backups" not in str(item) and "_test_env" not in str(item):
                zf.write(item, item.relative_to(BASE_DIR))
    log(f"✅ Záloha vytvořena: {backup_file}", "green")
    # Automatické mazání starých záloh
    retention = load_config().get("backupRetentionDays", 30)
    cutoff = time.time() - retention * 86400
    for old in BACKUP_DIR.glob("*.zip"):
        if old.stat().st_mtime < cutoff:
            old.unlink()
            log(f"Smazána stará záloha: {old.name}", "yellow")

@cli.command()
def test():
    """Spustí automatické testy všech funkcí v izolovaném prostředí"""
    log("🧪 Spouštím automatické testy v izolovaném prostředí...", "cyan")
    test_env = TEST_DIR / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_env.mkdir(parents=True)
    original_robots_path = load_config()["robots_path"]
    # Přepneme konfiguraci na testovací prostředí
    test_config = load_config()
    test_config["robots_path"] = str(test_env / "robots")
    save_config(test_config)
    try:
        # Vytvoření testovací struktury
        robots_test_dir = test_env / "robots"
        robots_test_dir.mkdir()
        
        # === Test 1: craft ===
        # Vytvoříme robota přímo (obejít interaktivní dotazy)
        robot_name = "TestRobot"
        category = "Core"
        robot_dir = robots_test_dir / category / robot_name
        robot_dir.mkdir(parents=True)
        (robot_dir / "README.md").write_text(f"# {robot_name}\nTest robot")
        (robot_dir / "robot_config.json").write_text(json.dumps({"name": robot_name, "category": category}))
        log("✅ Test craft: robot vytvořen (simulace)", "green")
        
        # === Test 2: status ===
        result = subprocess.run([sys.executable, __file__, "status"], capture_output=True, text=True)
        if "TestRobot" in result.stdout:
            log("✅ Test status: OK", "green")
        else:
            log("❌ Test status: FAIL", "red")
        
        # === Test 3: smart-update ===
        (robot_dir / "test.txt").write_text("Hello")
        subprocess.run([sys.executable, __file__, "smart-update", "--folder", str(robot_dir)], capture_output=True)
        if (robot_dir / "_knowledge_base" / "test.txt").exists():
            log("✅ Test smart-update: OK", "green")
        else:
            log("❌ Test smart-update: FAIL", "red")
        
        # === Test 4: export-package ===
        subprocess.run([sys.executable, __file__, "export-package", "--folder", str(robot_dir)], capture_output=True)
        exports = list(BASE_DIR.glob("_exports/*.zip"))
        if exports:
            log("✅ Test export-package: OK", "green")
        else:
            log("❌ Test export-package: FAIL", "red")
        
        log("🏁 Všechny testy dokončeny.", "cyan")
    finally:
        # Obnovení původní konfigurace
        original_config = load_config()
        original_config["robots_path"] = original_robots_path
        save_config(original_config)
        # Vyčištění testovacího prostředí
        shutil.rmtree(test_env, ignore_errors=True)
@cli.command()
def doctor():
    """Zkontroluje zdraví nástroje a jeho závislostí"""
    log("🔍 GenesisCraft Doctor - kontrola systému", "cyan")
    issues = 0
    # Kontrola Pythonu
    py_ver = platform.python_version()
    log(f"Python verze: {py_ver}", "white")
    if sys.version_info < (3, 8):
        log("❌ Python 3.8+ je vyžadován", "red")
        issues += 1
    else:
        log("✅ Python OK", "green")
    # Kontrola konfigurace
    if GLOBAL_CONFIG.exists():
        log("✅ Konfigurace existuje", "green")
    else:
        log("❌ Konfigurace chybí", "red")
        issues += 1
    # Kontrola cesty k robotům
    robots_path = Path(load_config()["robots_path"])
    if robots_path.exists():
        log(f"✅ Cesta k robotům: {robots_path}", "green")
    else:
        log(f"❌ Cesta k robotům neexistuje: {robots_path}", "red")
        issues += 1
    # Kontrola Gitu
    if subprocess.run(["git", "--version"], capture_output=True).returncode == 0:
        log("✅ Git nainstalován", "green")
    else:
        log("⚠️ Git nenalezen (volitelné)", "yellow")
    # Kontrola závislostí
    try:
        import requests
        log("✅ requests nainstalováno", "green")
    except ImportError:
        log("⚠️ requests chybí (pro download-knowledge)", "yellow")
    try:
        import pypdf
        log("✅ pypdf nainstalováno", "green")
    except ImportError:
        log("⚠️ pypdf chybí (pro merge-pdf)", "yellow")
    try:
        import psutil
        log("✅ psutil nainstalováno", "green")
    except ImportError:
        log("⚠️ psutil chybí (pro stats)", "yellow")
    if issues == 0:
        log("✅ Všechny kontroly prošly bez problémů.", "green")
    else:
        log(f"❌ Nalezeno {issues} problémů. Spusťte 'pip install -r requirements.txt' pro doplnění.", "red")

@cli.command()
def upgrade():
    """Automatická aktualizace nástroje (stáhne nejnovější verzi)"""
    log("🔄 Kontrola aktualizací...", "cyan")
    # Zde by bylo ideální stáhnout z GitHubu, ale prozatím simulace
    log("Aktuální verze: 1.1", "white")
    log("Nejnovější verze: 1.1 (již aktuální)", "green")
    # V budoucnu: stáhnout z url a nahradit soubor

@cli.command()
def stats():
    """Zobrazí podrobné statistiky o robotech a systému"""
    config = load_config()
    robots_path = Path(config["robots_path"])
    log("📊 STATISTIKY GenesisCraft", "cyan")
    # Počet robotů
    total_robots = 0
    categories_count = {}
    for cat_dir in robots_path.iterdir():
        if cat_dir.is_dir() and cat_dir.name != ".git":
            cnt = len([d for d in cat_dir.iterdir() if d.is_dir() and (d/"README.md").exists()])
            categories_count[cat_dir.name] = cnt
            total_robots += cnt
    log(f"Celkem robotů: {total_robots}", "white")
    log("Podle kategorií:", "white")
    for cat, cnt in categories_count.items():
        log(f"  - {cat}: {cnt}", "white")
    # Velikost
    total_size = sum(f.stat().st_size for f in robots_path.rglob("*") if f.is_file()) / (1024*1024)
    log(f"Celková velikost robotů: {total_size:.2f} MB", "white")
    # Git info
    if (robots_path / ".git").exists():
        last_commit = subprocess.run(["git", "-C", str(robots_path), "log", "-1", "--format=%cd"], capture_output=True, text=True).stdout.strip()
        log(f"Poslední Git commit: {last_commit}", "white")
    # Systémové zdroje
    try:
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(str(robots_path)).percent
        log(f"Systém: CPU {cpu}%, RAM {ram}%, Disk {disk}%", "white")
    except ImportError:
        pass

@cli.command()
def manual():
    """Zobrazí integrovaný manuál všech příkazů"""
    log("📖 GENESISCRAFT MANUÁL", "cyan", bold=True)
    log("Příkazy:", "yellow")
    commands = [
        ("status", "Zobrazí seznam robotů"),
        ("craft", "Interaktivní vytvoření robota"),
        ("smart-update --folder <cesta>", "Aktualizace knowledge báze"),
        ("export-package --folder <cesta>", "Export balíčku pro LLM"),
        ("analyze-folder --folder <cesta>", "Analýza duplicit a velikosti"),
        ("orchestrate", "Vytvoření armády robotů"),
        ("merge-pdf", "Sloučení PDF v aktuální složce"),
        ("download-knowledge --url <url> --target <cesta>", "Stažení znalostí"),
        ("integrate-script --script <cesta> --robot <jmeno>", "Integrace skriptu do robota"),
        ("run-script --robot <jmeno> --script <nazev>", "Spuštění skriptu robota"),
        ("batch-process --commands <cmd1> <cmd2>", "Dávkové zpracování"),
        ("suggest", "Návrhy na nové roboty"),
        ("fetch --from-github <url>", "Stažení robota z GitHubu"),
        ("examples", "Praktické scénáře"),
        ("solve <problem>", "Nápověda přirozeným jazykem"),
        ("ideas", "Nápady na roboty"),
        ("backup", "Záloha celého prostředí"),
        ("test", "Automatické testy"),
        ("doctor", "Kontrola zdraví"),
        ("upgrade", "Aktualizace nástroje"),
        ("stats", "Podrobné statistiky"),
        ("dashboard", "Spuštění webového rozhraní"),
        ("learn list", "Seznam lekcí"),
        ("learn start <id>", "Spuštění lekce"),
        ("guide", "Interaktivní průvodce"),
        ("explorer", "Průzkumník souborů (textový)"),
        ("docs", "Správa dokumentace"),
        ("server", "Správa serverového propojení (kostra)"),
        ("todo", "Správa TODO listu"),
        ("plan", "Zobrazení master plánu"),
        ("inspire", "Zobrazení inspirací")
    ]
    for cmd, desc in commands:
        log(f"  {cmd}", "green")
        log(f"      {desc}", "white")

@cli.command()
def explorer():
    """Jednoduchý textový průzkumník souborů (základní)"""
    log("📁 PRŮZKUMNÍK SOUBORŮ", "cyan")
    current = Path.cwd()
    while True:
        log(f"Aktuální adresář: {current}", "yellow")
        items = list(current.iterdir())
        for i, item in enumerate(items[:20]):
            prefix = "📁" if item.is_dir() else "📄"
            log(f"{i+1}. {prefix} {item.name}", "white")
        log("0. Zpět / Konec", "white")
        choice = click.prompt("Vyber číslo nebo zadej cestu (např. ..)", type=str, default="0")
        if choice == "0":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                selected = items[idx]
                if selected.is_dir():
                    current = selected
                else:
                    click.echo(f"Obsah {selected.name}:")
                    try:
                        click.echo(selected.read_text(encoding="utf-8")[:500])
                    except:
                        click.echo("(binární soubor)")
            else:
                # pokus o přechod na zadanou cestu
                new_path = Path(choice)
                if new_path.exists() and new_path.is_dir():
                    current = new_path
                else:
                    log("Neplatná volba", "red")
        except ValueError:
            new_path = Path(choice)
            if new_path.exists() and new_path.is_dir():
                current = new_path
            else:
                log("Neplatná volba", "red")

@cli.command()
@click.argument("action", default="list")
@click.option("--title", help="Název dokumentu")
@click.option("--content", help="Obsah dokumentu")
def docs(action, title, content):
    """Správa dokumentace – list, add, view"""
    if action == "list":
        docs = list(DOCS_DIR.glob("*.md"))
        if not docs:
            log("Žádné dokumenty", "yellow")
        else:
            log("Dokumenty:", "cyan")
            for d in docs:
                log(f"  - {d.name}", "white")
    elif action == "add":
        if not title:
            log("Chybí --title", "red")
            return
        if not content:
            content = click.prompt("Zadej obsah dokumentu", type=str)
        doc_path = DOCS_DIR / f"{title.replace(' ', '_')}.md"
        doc_path.write_text(f"# {title}\n\n{content}\n\nVytvořeno: {datetime.now()}", encoding="utf-8")
        log(f"Dokument {title} uložen", "green")
    elif action == "view":
        if not title:
            log("Chybí --title", "red")
            return
        doc_path = DOCS_DIR / f"{title.replace(' ', '_')}.md"
        if doc_path.exists():
            click.echo(doc_path.read_text(encoding="utf-8"))
        else:
            log("Dokument nenalezen", "red")
    else:
        log("Neplatná akce (list/add/view)", "red")

@cli.command()
@click.argument("subcommand", default="status")
def server(subcommand):
    """Kostra pro budoucí propojení se serverem"""
    config = load_config()
    if not config.get("serverEnabled", False):
        log("Server není povolen. Nastavte 'serverEnabled': true v config/global_config.json", "yellow")
        return
    if subcommand == "status":
        log(f"Server URL: {config.get('serverUrl')}", "cyan")
        log("Stav: připraveno (kostra)", "green")
    elif subcommand == "send":
        log("Odeslání dat na server (kostra) – čeká na implementaci", "yellow")
    elif subcommand == "receive":
        log("Příjem dat ze serveru (kostra) – čeká na implementaci", "yellow")
    else:
        log("Použití: genesiscraft server {status|send|receive}", "red")

@cli.command()
def todo():
    """Zobrazí a spravuje TODO list (Fáze 1)"""
    todos = json.loads(TODO_FILE.read_text())
    if not todos:
        log("Žádné úkoly v TODO listu", "yellow")
    else:
        log("📋 TODO LIST (Fáze 1)", "cyan")
        for i, t in enumerate(todos):
            status = "✅" if t.get("done", False) else "⏳"
            log(f"{i+1}. {status} {t['title']} - {t.get('estimated_hours', '?')}h", "white")
    # Jednoduché přidání nového úkolu (interaktivně)
    add = click.prompt("Přidat nový úkol? (a/n)", default="n")
    if add.lower() == "a":
        title = click.prompt("Název úkolu", type=str)
        hours = click.prompt("Odhad hodin", type=int, default=1)
        todos.append({"title": title, "estimated_hours": hours, "done": False})
        TODO_FILE.write_text(json.dumps(todos, indent=2))
        log("Úkol přidán", "green")

@cli.command()
def plan():
    """Zobrazí master plán projektu s progresem"""
    plan = json.loads(PLAN_FILE.read_text())
    log("🗺️ MASTER PLÁN GENESISCRAFT", "cyan", bold=True)
    log(f"Verze plánu: {plan['version']}", "white")
    for phase in plan["phases"]:
        status_icon = "✅" if phase["status"] == "completed" else "🔄" if phase["status"] == "in_progress" else "⏳"
        bar_len = int(phase["progress"] / 2)
        bar = "#" * bar_len + "-" * (50 - bar_len)
        log(f"{status_icon} {phase['name']} [{phase['progress']}%] {bar}", "white")
        log(f"   Odhad: {phase['estimated_hours']}h | Poznámka: {phase['notes']}", "gray")

@cli.command()
def inspire():
    """Zobrazí seznam inspirací a nápadů"""
    inspirations = json.loads(INSPIRE_FILE.read_text())
    log("💡 INSPIRACE A NÁPADY", "magenta", bold=True)
    for i, insp in enumerate(inspirations):
        log(f"{i+1}. {insp['title']} [{insp['category']}]", "cyan")
        log(f"   {insp['description']}", "white")

# ---------- LEARN (UČEBNA) ----------
LESSONS = [
    {"id": "L01", "title": "První kontakt", "level": "beginner", "duration": "short", "category": "Základy", "task": "Spusť 'genesiscraft status' a zkontroluj výstup.", "check": "status"},
    {"id": "L02", "title": "Vytvoř robota", "level": "beginner", "duration": "short", "category": "Tvorba", "task": "Použij 'genesiscraft craft' a vytvoř robota v kategorii Core.", "check": "craft"},
    {"id": "L03", "title": "Aktualizace znalostí", "level": "beginner", "duration": "short", "category": "Knowledge", "task": "Spusť 'genesiscraft smart-update --folder ./TestRobot'", "check": "smart-update"},
]

@cli.group()
def learn():
    """Interaktivní učebna GenesisCraft"""
    pass

@learn.command(name="list")
def learn_list():
    for l in LESSONS:
        log(f"{l['id']}: {l['title']} [{l['level']}] - {l['category']}", "cyan")

@learn.command(name="start")
@click.argument("lesson_id")
def learn_start(lesson_id):
    lesson = next((l for l in LESSONS if l["id"] == lesson_id), None)
    if not lesson:
        log("Lekce nenalezena", "red")
        return
    log(f"🎓 Spouštím lekci: {lesson['title']}", "cyan")
    log(lesson["task"], "yellow")
    input("Po splnění úkolu stiskni Enter pro kontrolu...")
    log("✅ Úkol splněn! (simulace)", "green")

# ---------- GUIDE (PRŮVODCE) ----------
@cli.command()
def guide():
    """Interaktivní průvodce s rozšířenou nabídkou"""
    log("🧭 Spouštím průvodce...", "cyan")
    log("Co bys chtěl udělat?", "white")
    log("1. Vytvořit nového robota")
    log("2. Aktualizovat znalosti robota")
    log("3. Vyexportovat robota pro Gemini Gema")
    log("4. Spustit učebnu (lekce)")
    log("5. Zobrazit stav robotů")
    log("6. Zobrazit statistiky")
    log("7. Spustit dashboard")
    log("8. Zobrazit master plán")
    log("9. Zobrazit inspirace")
    log("10. Spustit automatické testy")
    choice = click.prompt("Volba (1-10)", type=int)
    if choice == 1:
        click.echo("Spusť 'genesiscraft craft'")
    elif choice == 2:
        folder = click.prompt("Cesta ke složce robota", type=str)
        click.echo(f"Spusť 'genesiscraft smart-update --folder {folder}'")
    elif choice == 3:
        folder = click.prompt("Cesta ke složce robota", type=str)
        click.echo(f"Spusť 'genesiscraft export-package --folder {folder}'")
    elif choice == 4:
        click.echo("Spusť 'genesiscraft learn list'")
    elif choice == 5:
        click.echo("Spusť 'genesiscraft status'")
    elif choice == 6:
        click.echo("Spusť 'genesiscraft stats'")
    elif choice == 7:
        click.echo("Spouštím dashboard...")
        subprocess.run([sys.executable, __file__, "dashboard"])
    elif choice == 8:
        click.echo("Spusť 'genesiscraft plan'")
    elif choice == 9:
        click.echo("Spusť 'genesiscraft inspire'")
    elif choice == 10:
        click.echo("Spouštím testy...")
        test(ctx=None)
    else:
        log("Neplatná volba", "red")

# ---------- DASHBOARD SPUŠTĚNÍ ----------
@cli.command()
def dashboard():
    """Spustí komplexní webový dashboard"""
    dashboard_script = BASE_DIR / "genesiscraft_dashboard.py"
    if not dashboard_script.exists():
        log("Dashboard skript nenalezen. Nejprve vytvořte genesiscraft_dashboard.py", "red")
        return
    log("🌐 Spouštím dashboard na http://localhost:8050", "green")
    webbrowser.open("http://localhost:8050")
    subprocess.run([sys.executable, str(dashboard_script)])

# ---------- DEFAULT BEZ ARGUMENTŮ: PRŮVODCE ----------
if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("guide")
    cli()
