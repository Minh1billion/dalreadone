import io
import os
import random
import uuid
import requests

BASE = "http://localhost:8000/api"
CREATED_PROJECTS: list[tuple[dict, int]] = []
CSV_PATH = os.path.join(os.path.dirname(__file__), "data.csv")

# Set FAST_TEST=1 to skip all LLM-heavy tests
FAST_TEST = os.environ.get("FAST_TEST", "0") == "1"

_VALID_CHART_TYPES = {"bar", "line", "pie", "scatter", "histogram", "grouped_bar"}

# ---------------------------------------------------------------------------
# Random question pool — drawn from the actual CSV columns:
#   order_id, order_date, customer_id, customer_name, region,
#   category, product_name, quantity, unit_price, discount, status
# ---------------------------------------------------------------------------
_QUESTION_POOL = [
    # Revenue / sales questions
    "Which product category generates the most revenue?",
    "What is the total revenue by region?",
    "Which product has the highest total sales value?",
    "Show me monthly revenue trend.",
    "What is the average order value per region?",

    # Customer questions
    "Who are the top 5 customers by total spending?",
    "How many unique customers placed orders each month?",
    "Which region has the most customers?",

    # Discount / status questions
    "Which products have the highest average discount?",
    "What percentage of orders were cancelled?",
    "Is there a correlation between discount and order status?",

    # Quantity / inventory questions
    "Which product sells the most units?",
    "What is the average quantity per order by category?",

    # Time-based questions
    "Which month had the highest number of orders?",
    "How does sales volume change week over week?",

    # Irrelevant (should gracefully fall back to exploration)
    "What is the weather in Paris today?",
    "Tell me a joke about data analysis.",
]


def _pick_random_question() -> str:
    """Return a random question from the pool."""
    return random.choice(_QUESTION_POOL)


# ─── Auth / project / file helpers ──────────────────────────────────────────

def get_auth_header(username=None, password="123456") -> dict:
    if username is None:
        username = f"user_{uuid.uuid4().hex[:8]}"
    session = requests.Session()
    session.post(
        f"{BASE}/auth/register",
        json={"username": username, "password": password},
        timeout=10,
    )
    res = session.post(
        f"{BASE}/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json().get("access_token")
    assert token, "No access_token returned"
    return {"Authorization": f"Bearer {token}"}


def create_project(headers: dict, name="Query Test Project") -> int:
    res = requests.post(
        f"{BASE}/projects",
        json={"name": name},
        headers=headers,
        timeout=10,
    )
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]
    CREATED_PROJECTS.append((headers, project_id))
    return project_id


def upload_csv(headers: dict, project_id: int, filename="data.csv") -> int:
    with open(CSV_PATH, "rb") as f:
        content = f.read()
    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files={"file": (filename, io.BytesIO(content), "text/csv")},
        headers=headers,
        timeout=10,
    )
    assert res.status_code == 201, f"Upload failed: {res.text}"
    return res.json()["id"]


# ─── Shared fixture (created once, reused by all happy-path tests) ───────────

class _SharedFixture:
    """Lazily creates 1 project + 1 uploaded file, reused across the session."""
    headers: dict = None
    project_id: int = None
    file_id: int = None

    @classmethod
    def get(cls):
        if cls.file_id is None:
            cls.headers = get_auth_header()
            cls.project_id = create_project(cls.headers, name="Shared Happy-Path Project")
            cls.file_id = upload_csv(cls.headers, cls.project_id)
        return cls.headers, cls.project_id, cls.file_id


def _query(headers, project_id, file_id, question="", timeout=60) -> dict:
    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": question},
        headers=headers,
        timeout=timeout,
    )
    assert res.status_code == 200, res.text
    return res.json()


# ─── Result printer ──────────────────────────────────────────────────────────

def print_full_result(data: dict, label: str = ""):
    """
    Print every field of the query response so test runs are fully visible.
    Truncates very long strings to keep output readable.
    """
    MAX_STR = 600   # max chars for long text fields before truncating
    sep = "─" * 60
    tag = f" [{label}]" if label else ""
    print(f"\n{'═'*60}")
    print(f"  FULL RESULT{tag}")
    print(f"{'═'*60}")

    # --- scalar fields ---
    print(f"\n  user_question    : {data.get('user_question')!r}")
    print(f"  explore_reason   : {data.get('explore_reason')!r}")
    print(f"  interesting_reason: {data.get('interesting_reason')!r}")

    # --- result (may be long markdown table) ---
    result_text = data.get("result", "")
    if len(result_text) > MAX_STR:
        print(f"\n  result ({len(result_text)} chars — first {MAX_STR} shown):\n{sep}")
        print(result_text[:MAX_STR] + "\n  ... [truncated]")
    else:
        print(f"\n  result:\n{sep}\n{result_text}")

    # --- interesting_result ---
    int_result = data.get("interesting_result") or ""
    if int_result:
        if len(int_result) > MAX_STR:
            print(f"\n  interesting_result ({len(int_result)} chars — first {MAX_STR} shown):\n{sep}")
            print(int_result[:MAX_STR] + "\n  ... [truncated]")
        else:
            print(f"\n  interesting_result:\n{sep}\n{int_result}")
    else:
        print(f"\n  interesting_result: (none)")

    # --- insight ---
    insight_text = data.get("insight", "")
    if len(insight_text) > MAX_STR:
        print(f"\n  insight ({len(insight_text)} chars — first {MAX_STR} shown):\n{sep}")
        print(insight_text[:MAX_STR] + "\n  ... [truncated]")
    else:
        print(f"\n  insight:\n{sep}\n{insight_text}")

    # --- code ---
    code_text = data.get("code", "")
    if len(code_text) > MAX_STR:
        print(f"\n  code ({len(code_text)} chars — first {MAX_STR} shown):\n{sep}")
        print(code_text[:MAX_STR] + "\n  ... [truncated]")
    else:
        print(f"\n  code:\n{sep}\n{code_text}")

    # --- charts ---
    charts = data.get("charts", [])
    print(f"\n  charts ({len(charts)} total):")
    for i, c in enumerate(charts):
        print(f"    [{i}] type={c.get('type')}  title={c.get('title')!r}"
              f"  labels={len(c.get('labels', []))} items")

    int_charts = data.get("interesting_charts", [])
    print(f"\n  interesting_charts ({len(int_charts)} total):")
    for i, c in enumerate(int_charts):
        print(f"    [{i}] type={c.get('type')}  title={c.get('title')!r}"
              f"  labels={len(c.get('labels', []))} items")

    print(f"\n{'═'*60}\n")


# ─── Assertion helpers ───────────────────────────────────────────────────────

def assert_base_fields(data: dict):
    for field in ("explore_reason", "result", "insight", "code"):
        assert field in data, f"Missing field: {field}"
        assert data[field], f"{field} should not be empty"
    assert "interesting_reason" in data
    assert "interesting_result" in data
    assert isinstance(data["charts"], list)
    assert isinstance(data["interesting_charts"], list)
    assert "cost_report" in data, "Missing cost_report — new query_service.py not deployed?"
    assert isinstance(data["cost_report"], dict)


def assert_chart(chart):
    assert isinstance(chart, dict)
    assert chart["type"] in _VALID_CHART_TYPES, f"Invalid chart type: {chart['type']}"
    assert isinstance(chart["labels"], list) and len(chart["labels"]) > 0
    assert isinstance(chart["data"], list)
    if chart["type"] == "grouped_bar":
        assert "series_labels" in chart
        for series in chart["data"]:
            assert isinstance(series, list)
            assert len(series) == len(chart["labels"])
    else:
        assert len(chart["labels"]) == len(chart["data"])


def assert_charts_list(charts):
    assert isinstance(charts, list)
    assert len(charts) <= 3
    for c in charts:
        assert_chart(c)


def print_cost_report(data: dict, label: str = ""):
    report = data.get("cost_report")
    if not report:
        print("  [cost] NO cost_report in response")
        return
    sep = "-" * 56
    tag = f" [{label}]" if label else ""
    print(f"\n{sep}\n  COST REPORT{tag}\n{sep}")
    print(f"  total_tokens : {report.get('total_tokens', 0):>6}")
    print(f"  prompt_tokens: {report.get('total_prompt_tokens', 0):>6}")
    print(f"  output_tokens: {report.get('total_completion_tokens', 0):>6}")
    print(f"  cost_usd     : ${report.get('total_cost_usd', 0):.6f}")
    print(f"  latency_ms   : {report.get('total_latency_ms', 0):>6} ms")
    skipped = report.get("skipped_stages", [])
    if skipped:
        print(f"  skipped      : {', '.join(skipped)}")
    print(f"  {'stage':<30} {'in':>5} {'out':>5}  {'cost_usd':>10}  {'ms':>6}")
    print(f"  {'-'*30} {'-'*5} {'-'*5}  {'-'*10}  {'-'*6}")
    for call in report.get("calls", []):
        if call.get("skipped"):
            print(f"  {call['stage']:<30}  SKIPPED  ({call.get('skip_reason', '')})")
        else:
            print(
                f"  {call['stage']:<30} {call['prompt_tokens']:>5} {call['completion_tokens']:>5}"
                f"  ${call['cost_usd']:>9.6f}  {call['latency_ms']:>6}"
            )
    print(sep + "\n")


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_query_happy_path():
    """
    Combined: test_query_success + test_query_chart_structure + test_query_interesting_findings.
    Uses a RANDOM question from the pool on every run to exercise varied inputs.
    Reuses shared fixture → only 1 project/file created.
    """
    if FAST_TEST:
        print("SKIPPED test_query_happy_path (FAST_TEST=1)")
        return

    question = _pick_random_question()
    print(f"\n  [happy_path] Random question selected: {question!r}")

    headers, project_id, file_id = _SharedFixture.get()
    data = _query(headers, project_id, file_id, question=question)

    # --- test_query_success ---
    assert data["user_question"] == question
    assert_base_fields(data)
    assert_charts_list(data["charts"])
    assert_charts_list(data["interesting_charts"])

    # --- test_query_chart_structure ---
    total = len(data["charts"]) + len(data["interesting_charts"])
    print(f"  Charts: pass1={len(data['charts'])}  pass2={len(data['interesting_charts'])}  total={total}")

    # --- test_query_interesting_findings ---
    assert isinstance(data["interesting_reason"], (str, type(None)))
    assert isinstance(data["interesting_result"], (str, type(None)))
    if data["interesting_reason"]:
        assert data["interesting_result"], "interesting_result must be set when interesting_reason is set"
    if data["interesting_result"]:
        assert data["interesting_reason"], "interesting_reason must be set when interesting_result is set"

    # Print full response so nothing is hidden
    print_full_result(data, label="happy_path")
    print_cost_report(data, label="happy_path")
    print("test_query_happy_path OK")


def test_query_irrelevant_question():
    """
    Irrelevant question should fall back to general exploration and still return a valid response.
    Always picks one of the two irrelevant entries from the pool so the behavior is deterministic.
    """
    if FAST_TEST:
        print("SKIPPED test_query_irrelevant_question (FAST_TEST=1)")
        return

    # Pick a question that is clearly off-topic for the sales CSV
    irrelevant_questions = [q for q in _QUESTION_POOL if "weather" in q or "joke" in q]
    question = random.choice(irrelevant_questions)
    print(f"\n  [irrelevant] Question: {question!r}")

    headers, project_id, file_id = _SharedFixture.get()
    data = _query(headers, project_id, file_id, question=question)

    assert data["user_question"] == question
    assert_base_fields(data)
    assert_charts_list(data["charts"])
    assert_charts_list(data["interesting_charts"])

    # Print full response so fallback behavior is visible
    print_full_result(data, label="irrelevant_question")
    print_cost_report(data, label="irrelevant_question")
    print("test_query_irrelevant_question OK:", data["explore_reason"])


def test_query_multiple_random():
    """
    Run N rounds with different random questions to stress-test the pipeline.
    Set env var QUERY_ROUNDS=N (default 1) to control iteration count.
    Each round reuses the shared fixture — no extra project/file created.
    """
    if FAST_TEST:
        print("SKIPPED test_query_multiple_random (FAST_TEST=1)")
        return

    rounds = int(os.environ.get("QUERY_ROUNDS", "1"))
    headers, project_id, file_id = _SharedFixture.get()

    # Sample without replacement so the same question is not repeated
    pool = _QUESTION_POOL.copy()
    random.shuffle(pool)
    selected = pool[:rounds]

    print(f"\n  [multiple_random] Running {rounds} round(s):")
    for i, question in enumerate(selected, start=1):
        print(f"\n  Round {i}/{rounds}: {question!r}")
        data = _query(headers, project_id, file_id, question=question)
        assert data["user_question"] == question
        assert_base_fields(data)
        assert_charts_list(data["charts"])
        assert_charts_list(data["interesting_charts"])
        print_full_result(data, label=f"round_{i}")
        print_cost_report(data, label=f"round_{i}")

    print(f"\ntest_query_multiple_random OK ({rounds} rounds)")


def test_query_wrong_owner():
    """User B cannot query User A's file → 403."""
    headers_a = get_auth_header()
    headers_b = get_auth_header()
    project_id = create_project(headers_a)
    file_id = upload_csv(headers_a, project_id)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": "test"},
        headers=headers_b,
        timeout=10,
    )
    assert res.status_code == 403, res.text
    print("test_query_wrong_owner OK: 403")


def test_query_project_not_found():
    """Non-existent project → 404."""
    headers = get_auth_header()
    res = requests.post(
        f"{BASE}/projects/999999/files/1/query",
        json={"question": "test"},
        headers=headers,
        timeout=10,
    )
    assert res.status_code == 404, res.text
    print("test_query_project_not_found OK: 404")


def test_query_file_not_found():
    """Non-existent file → 404."""
    headers = get_auth_header()
    project_id = create_project(headers)
    res = requests.post(
        f"{BASE}/projects/{project_id}/files/999999/query",
        json={"question": "test"},
        headers=headers,
        timeout=10,
    )
    assert res.status_code == 404, res.text
    print("test_query_file_not_found OK: 404")


# ─── Cleanup ─────────────────────────────────────────────────────────────────

def cleanup_projects():
    print("\n=== CLEANUP ===")
    for headers, project_id in CREATED_PROJECTS:
        res = requests.delete(
            f"{BASE}/projects/{project_id}",
            headers=headers,
            timeout=10,
        )
        assert res.status_code in (204, 404), (
            f"Cleanup failed {project_id}: {res.status_code} - {res.text}"
        )
        print(f"Cleaned project {project_id}")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--fast" in sys.argv:
        os.environ["FAST_TEST"] = "1"
        globals()["FAST_TEST"] = True

    try:
        print(f"\n=== QUERY TESTS (FAST_TEST={FAST_TEST}) ===\n")

        # Auth / existence error tests (cheap — no LLM calls)
        test_query_wrong_owner()
        test_query_project_not_found()
        test_query_file_not_found()

        # LLM-heavy tests
        test_query_happy_path()
        test_query_irrelevant_question()
        test_query_multiple_random()

        print("\nAll query tests passed!")
    finally:
        cleanup_projects()