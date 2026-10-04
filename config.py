import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().with_name('.env')
load_dotenv(ENV_PATH)

def int_list(v: str):
    out=[]
    for x in (v or '').split(','):
        x=x.strip()
        if x:
            try: out.append(int(x))
            except ValueError: raise RuntimeError(f'ADMIN_IDS noto‘g‘ri: {x}')
    return out

@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int]

def load_config():
    token=os.getenv('BOT_TOKEN','').strip()
    if not token: raise RuntimeError(f'BOT_TOKEN topilmadi. .env kerak: {ENV_PATH}')
    return Config(token, int_list(os.getenv('ADMIN_IDS','')))
