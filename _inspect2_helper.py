from pathlib import Path
text = Path('index.html').read_text(encoding='utf-8')
start = text.index("'delivery_fee_label'")
end = text.index("'delivery_fee_note'", start)
print(repr(text[start:end]))
