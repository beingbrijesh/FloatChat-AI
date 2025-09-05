import re, os, requests
MD='docs/TASKS.md'
checks=[
  (r"FE1 .*", lambda: os.path.exists('.venv')),
  (r"DM1 .*", lambda: os.path.exists('data/raw') and any(f.endswith('.nc') for f in os.listdir('data/raw'))),
  (r"DM3 .*", lambda: os.path.exists('data/processed') and any(p.endswith('.parquet') for p in os.listdir('data/processed'))),
  (r"DM5 .*", lambda: os.path.exists('vectorstore')),
  (r"BE1 .*", lambda: os.path.exists('app/backend/main.py')),
  (r"BE2 .*", lambda: os.path.exists('.env')),
  (r"QA2 .*", lambda: os.path.exists('tools/last_test.txt')),
  (r"QA4 .*", lambda: os.path.exists('MVP_LOCK')),
]

def _port(p):
  try:
    requests.get(f"http://127.0.0.1:{p}", timeout=0.3)
    return True
  except Exception:
    return False

with open(MD,'r',encoding='utf-8') as f:
  m=f.read()
for pat, fn in checks:
  done = fn()
  m = re.sub(rf"- \[.\] ({pat})", lambda s: f"- [{'x' if done else ' '}] "+s.group(1), m)
with open(MD,'w',encoding='utf-8') as f:
  f.write(m)
print('Updated TASKS.md')