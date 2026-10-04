import json
from html import escape

MAX_JSON_TEXT = 35000
MAX_JSON_DEPTH = 40

class DuplicateKeyError(ValueError):
    pass

def _pairs_hook(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(f'Dublikat kalit: {key}')
        obj[key] = value
    return obj

def _reject_constant(value):
    raise ValueError(f'JSON standarti bo‘yicha ruxsat etilmagan qiymat: {value}')

def _depth(value, level=0):
    if level > MAX_JSON_DEPTH:
        raise ValueError(f'JSON juda chuqur. Maksimum {MAX_JSON_DEPTH} daraja.')
    if isinstance(value, dict):
        for v in value.values(): _depth(v, level + 1)
    elif isinstance(value, list):
        for v in value: _depth(v, level + 1)

def validate_json(text: str) -> str:
    if not text or not text.strip():
        raise ValueError('JSON bo‘sh bo‘lishi mumkin emas.')
    if len(text) > MAX_JSON_TEXT:
        raise ValueError(f'JSON juda uzun. Maksimum {MAX_JSON_TEXT} belgi.')
    try:
        obj = json.loads(
            text,
            object_pairs_hook=_pairs_hook,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError as e:
        raise ValueError(str(e)) from e
    except json.JSONDecodeError as e:
        raise ValueError(f'JSON xato: {e.msg} (qator {e.lineno}, ustun {e.colno})') from e
    except ValueError as e:
        raise ValueError(str(e)) from e
    if not isinstance(obj, (dict, list)):
        raise ValueError('JSON asosiy qiymati object yoki array bo‘lishi kerak.')
    _depth(obj)
    return json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)

def html_code_block(text: str) -> str:
    return '<pre><code>' + escape(text) + '</code></pre>'
