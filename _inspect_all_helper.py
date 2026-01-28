from pathlib import Path
text = Path('index.html').read_text(encoding='utf-8')
start = 0
while True:
    try:
        idx = text.index("'delivery_fee_label'", start)
    except ValueError:
        break
    end = text.index("'delivery_fee_note'", idx)
    print(repr(text[idx:end]))
    start = end
