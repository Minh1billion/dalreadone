import subprocess
import sys
import os

TESTS = [
    ("S3 Connection",  "app/test/test_s3.py"),
    ("Groq Connection", "app/test/test_groq.py"),
    ("DB Connection",   "app/test/test_db.py"),
    ("Auth Flow",       "app/test/test_auth.py"),
    ("Project Flow",    "app/test/test_projects.py"),
    ("File Flow",       "app/test/test_files.py"),
    ("Query Flow",      "app/test/test_query.py"),
]

from app.db.session import engine
from app.models.base import Base

def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset!")


def run(label: str, path: str) -> bool:
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    result = subprocess.run([sys.executable, path], env=env)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {label}")
        return False
    print(f"\n✅ PASSED: {label}")
    return True


if __name__ == "__main__":
    results = []

    for label, path in TESTS:
        ok = run(label, path)
        results.append((label, ok))
        if not ok:
            print("\n⛔ Stopping — fix the failure above before continuing.")
            break

    print(f"\n{'='*50}")
    print("  SUMMARY")
    print(f"{'='*50}")
    for label, ok in results:
        status = "✅ PASSED" if ok else "❌ FAILED"
        print(f"  {status}  {label}")

    skipped = len(TESTS) - len(results)
    if skipped:
        for label, _ in TESTS[len(results):]:
            print(f"  ⏭  SKIPPED  {label}")

    print()
    all_passed = all(ok for _, ok in results) and skipped == 0
    print("====== RESET DATABASE =======")
    reset_db()

    sys.exit(0 if all_passed else 1)