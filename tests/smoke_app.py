"""Headless smoke test: run every page via Streamlit AppTest and assert no exceptions."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

from lib import seed  # noqa: E402

seed.seed_if_empty()

PAGES = {
    "views/browse.py": False,
    "views/compare.py": False,
    "views/how_it_works.py": False,
    "views/about.py": False,
    "views/dashboard.py": True,   # admin
    "views/requests.py": True,    # admin
    "views/manage.py": True,      # admin
    "views/upload.py": True,      # admin
}

failures = []
for page, admin in PAGES.items():
    at = AppTest.from_file(str(ROOT / page), default_timeout=60)
    if admin:
        at.session_state["ll_admin_ok"] = True
    at.run()
    status = "OK"
    if at.exception:
        status = "EXCEPTION"
        failures.append((page, [str(e) for e in at.exception]))
    n_md = len(at.markdown)
    n_btn = len(at.button)
    print(f"[{status}] {page}: markdown={n_md} buttons={n_btn}")

# Exercise a browse interaction: open the first deal's detail dialog (request form).
at = AppTest.from_file(str(ROOT / "views/browse.py"), default_timeout=60)
at.run()
detail_btns = [b for b in at.button if b.label == "View details"]
if detail_btns:
    detail_btns[0].click().run()
    print(f"[{'EXCEPTION' if at.exception else 'OK'}] browse detail dialog + request form")
    if at.exception:
        failures.append(("browse detail click", [str(e) for e in at.exception]))

print("-" * 50)
if failures:
    print("FAILURES:")
    for page, errs in failures:
        print(f"  {page}:")
        for e in errs:
            print("    " + e.replace("\n", "\n    "))
    sys.exit(1)
print("ALL PAGES RENDERED CLEANLY ✅")
