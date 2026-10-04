from pathlib import Path
from datetime import datetime
import shutil

def make_backup(db_path):
    src=Path(db_path); out=src.with_name(f'backup_{datetime.now():%Y%m%d_%H%M%S}.db'); shutil.copy2(src,out); return str(out)
