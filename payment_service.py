def format_money(value: int) -> str:
    return f'{int(value):,}'.replace(',', ' ') + ' so‘m'
