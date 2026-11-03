import subprocess
import time
import tempfile
from pywinauto import Desktop

d = tempfile.mkdtemp()
print("Temp directory:", d)
# Using --new-window forces VS Code to spawn a new window for this directory
res = subprocess.run(["cmd.exe", "/c", "code", "--new-window", d], capture_output=True, text=True)
print("Returncode:", res.returncode, "stdout:", res.stdout, "stderr:", res.stderr)

for i in range(15):
    time.sleep(1)
    matching = []
    try:
        for w in Desktop(backend="uia").windows():
            try:
                wt = w.window_text()
                if "code" in wt.lower():
                    matching.append(wt)
            except Exception:
                pass
    except Exception as e:
        print("Error:", e)
    if matching:
        print(f"[{i+1}s] Found matching windows:", matching)
        break
    else:
        print(f"[{i+1}s] Waiting for window...")
