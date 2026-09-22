import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# GPU auto-detect (FIX 7 / FIX 13)
# We probe torch once here so that every module can read settings.USE_GPU
# instead of calling torch.cuda.is_available() in multiple places.
# ---------------------------------------------------------------------------
def _detect_gpu() -> bool:
    try:
        import torch
        available = torch.cuda.is_available()
        if available:
            print("[config] CUDA GPU detected — ANPR / YOLO will use GPU.", flush=True)
        else:
            print("[config] No CUDA GPU — running on CPU.", flush=True)
        return available
    except Exception:
        print("[config] torch not importable — CPU mode.", flush=True)
        return False

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

env_path = ROOT_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class UnifiedSettings:
    ROOT_DIR: Path = ROOT_DIR
    BACKEND_DIR: Path = BACKEND_DIR
    APP_DIR: Path = APP_DIR
    DATA_DIR: Path = BACKEND_DIR / 'data'
    CROPS_DIR: Path = DATA_DIR / 'crops'
    AUDIO_EVIDENCE_DIR: Path = DATA_DIR / 'audio_evidence'
    VECTOR_DB_DIR: Path = DATA_DIR / 'vector_db'
    WEIGHTS_DIR: Path = BACKEND_DIR / 'weights'
    PUBLIC_DIR: Path = ROOT_DIR / 'public'
    
    YOLO_MODEL_PATH: str = os.getenv('YOLO_MODEL_PATH', str(WEIGHTS_DIR / 'yolo11n.pt'))
    # Path to the dedicated YOLO model for license plate detection
    LICENSE_PLATE_DETECTOR_PATH: str = os.getenv(
        'LICENSE_PLATE_DETECTOR_PATH', 
        str(BACKEND_DIR / 'models' / 'license_plate_detector.pt')
    )
    DEVICE: str = os.getenv('DEVICE', 'cuda' if _detect_gpu() else 'cpu')
    ANPR_OCR: str = os.getenv('ANPR_OCR', 'rapidocr')
    # FIX 13: default to ~/.easyocr so it works on Linux / Docker / macOS as well.
    # Set EASYOCR_MODULE_PATH env var to override (e.g. a fast local SSD path).
    EASYOCR_MODULE_PATH: str = os.getenv(
        'EASYOCR_MODULE_PATH',
        str(Path.home() / '.easyocr')
    )
    WATCHLIST_PATH: str = os.getenv('WATCHLIST_PATH', str(DATA_DIR / 'watchlist'))
    
    REID_SIMILARITY_THRESHOLD: float = float(os.getenv('REID_SIMILARITY_THRESHOLD', '0.72'))
    REID_FEATURE_DIM: int = int(os.getenv('REID_FEATURE_DIM', '512'))
    REID_BACKBONE: str = os.getenv('REID_BACKBONE', 'osnet_x0_25')
    
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'groq').lower()
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'openai/gpt-oss-120b')
    LLM_TEMPERATURE: float = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    GROQ_API_KEY: str = os.getenv('GROQ_API_KEY', '')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    CLASSIFICATION: str = 'SECRET // REL TO BHARAT DEFENCE FORCES'
    ORGANISATION: str = 'Border Security Force - Acoustic Intelligence Division'
    DEFAULT_POST: str = 'POST-LONGITUDE-09'
    DEFAULT_SECTOR: str = 'WESTERN-THAR-SECTOR-4'
    YAMNET_PATH: str = os.getenv('YAMNET_PATH', str(WEIGHTS_DIR / 'yamnet'))
    WHISPER_MODEL_SIZE: str = os.getenv('WHISPER_MODEL_SIZE', 'base')
    DRONE_SENSITIVITY: float = float(os.getenv('DRONE_SENSITIVITY', '0.75'))
    
    DATABASE_URL: str = os.getenv('DATABASE_URL', f'sqlite:///{ROOT_DIR}/surveillance.db')
    AUDIO_DB_PATH: str = os.getenv('AUDIO_DB_PATH', str(DATA_DIR / 'border_intel.db'))
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8000'))
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

    # ── ANPR / OCR settings (FIX 1, 7, 12, 13) ─────────────────────────────
    # USE_GPU: resolved once at import time via torch probe above.
    USE_GPU: bool = _detect_gpu()

    # Maximum items in the ANPRWorker OCR queue before oldest are dropped.
    # Keeps memory bounded under sustained load (FIX 12).
    ANPR_OCR_QUEUE_MAXSIZE: int = int(os.getenv('ANPR_OCR_QUEUE_MAXSIZE', '8'))

    # Portable YOLO weight search order (FIX 13).
    # Populated at class-body evaluation time so Path expressions are valid.
    YOLO_WEIGHT_CANDIDATES: tuple = (
        Path(os.getenv('YOLO_MODEL_PATH', str(BACKEND_DIR / 'weights' / 'yolo11n.pt'))),
        BACKEND_DIR / 'weights' / 'yolo11n.pt',
        ROOT_DIR / 'yolo11n.pt',
        Path('yolo11n.pt'),
        Path.home() / '.cache' / 'ultralytics' / 'yolo11n.pt',
    )

    def ensure_directories(self):
        for d in [self.DATA_DIR, self.CROPS_DIR, self.AUDIO_EVIDENCE_DIR, self.VECTOR_DB_DIR, self.WEIGHTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

settings = UnifiedSettings()
settings.ensure_directories()
