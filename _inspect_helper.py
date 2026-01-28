from pathlib import Path
text = Path('index.html').read_text(encoding='utf-8')
idx = text.index("'delivery_fee_label'")
print(text[idx-120:idx+220])
