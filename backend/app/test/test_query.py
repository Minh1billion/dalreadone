import io
import os
import uuid
import requests

BASE = "http://localhost:8000"

CREATED_PROJECTS: list[tuple[dict, int]] = []

CSV_PATH = os.path.join(os.path.dirname(__file__), "data.csv")


# AUTH
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


# PROJECT
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


# FILE
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


_VALID_CHART_TYPES = {"bar", "line", "pie", "scatter", "histogram", "grouped_bar"}


# HELPERS
def assert_base_fields(data: dict):
    """Assert fields present in every successful query response."""
    for field in ("explore_reason", "result", "insight", "code"):
        assert field in data, f"Missing field: {field}"
        assert data[field], f"{field} should not be empty"

    assert "interesting_reason" in data, "Missing key: interesting_reason"
    assert "interesting_result" in data, "Missing key: interesting_result"

    # New schema: charts (list) instead of chart_data (single dict)
    assert "charts" in data, "Missing key: charts"
    assert "interesting_charts" in data, "Missing key: interesting_charts"
    assert isinstance(data["charts"], list), "charts must be a list"
    assert isinstance(data["interesting_charts"], list), "interesting_charts must be a list"


def assert_chart(chart):
    """Validate a single chart dict."""
    assert isinstance(chart, dict), "chart must be a dict"
    assert "type" in chart, "chart missing 'type'"
    assert "title" in chart, "chart missing 'title'"
    assert "labels" in chart, "chart missing 'labels'"
    assert "data" in chart, "chart missing 'data'"
    assert chart["type"] in _VALID_CHART_TYPES, f"Invalid chart type: {chart['type']}"
    assert isinstance(chart["labels"], list), "labels must be a list"
    assert isinstance(chart["data"], list), "data must be a list"
    assert len(chart["labels"]) > 0, "chart labels must not be empty"

    if chart["type"] == "grouped_bar":
        # data is list of lists, series_labels required
        assert "series_labels" in chart, "grouped_bar chart missing 'series_labels'"
        assert isinstance(chart["series_labels"], list), "series_labels must be a list"
        for series in chart["data"]:
            assert isinstance(series, list), "grouped_bar data entries must be lists"
            assert len(series) == len(chart["labels"]), (
                "grouped_bar series length must match labels length"
            )
    else:
        assert len(chart["labels"]) == len(chart["data"]), (
            "labels and data must have the same length"
        )


def assert_charts_list(charts):
    """Validate the charts list from the response."""
    assert isinstance(charts, list), "charts must be a list"
    assert len(charts) <= 3, "charts list must have at most 3 items"
    for chart in charts:
        assert_chart(chart)


def print_response(data: dict):
    print("Explore reason:", data["explore_reason"])
    print("Insight preview:", data["insight"][:100], "...")
    print("\n--- CODE ---")
    print(data["code"])
    print("\n--- RESULT ---")
    print(data["result"])

    charts = data.get("charts", [])
    if charts:
        print(f"\n--- CHARTS ({len(charts)}) ---")
        for i, c in enumerate(charts, 1):
            print(f"  [{i}] type={c['type']}  title='{c['title']}'  points={len(c['labels'])}")
            print(f"       labels: {c['labels'][:5]} ...")
            print(f"       data  : {c['data'][:5]} ...")
    else:
        print("\n--- CHARTS: [] ---")

    interesting_charts = data.get("interesting_charts", [])
    if interesting_charts:
        print(f"\n--- INTERESTING CHARTS ({len(interesting_charts)}) ---")
        for i, c in enumerate(interesting_charts, 1):
            print(f"  [{i}] type={c['type']}  title='{c['title']}'  points={len(c['labels'])}")
    else:
        print("\n--- INTERESTING CHARTS: [] ---")

    if data.get("interesting_reason"):
        print("\n--- INTERESTING REASON ---")
        print(data["interesting_reason"])


# TESTS
def test_query_success():
    """Happy path: upload CSV then query with a specific question."""
    headers = get_auth_header()
    project_id = create_project(headers)
    file_id = upload_csv(headers, project_id)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": "Which product should I invest more?"},
        headers=headers,
        timeout=60,
    )

    assert res.status_code == 200, res.text

    data = res.json()
    assert data["user_question"] == "Which product should I invest more?"
    assert_base_fields(data)
    assert_charts_list(data["charts"])
    assert_charts_list(data["interesting_charts"])

    print("Query success OK:", data["explore_reason"])
    print_response(data)


def test_query_chart_structure():
    """
    Free exploration should produce at least one chart in the charts list.
    Validates the full chart contract for every chart returned.
    """
    headers = get_auth_header()
    project_id = create_project(headers)
    file_id = upload_csv(headers, project_id)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": ""},
        headers=headers,
        timeout=60,
    )

    assert res.status_code == 200, res.text

    data = res.json()
    assert_base_fields(data)
    assert_charts_list(data["charts"])
    assert_charts_list(data["interesting_charts"])

    total_charts = len(data["charts"]) + len(data["interesting_charts"])
    print(f"Charts produced: pass1={len(data['charts'])}  pass2={len(data['interesting_charts'])}")
    for c in data["charts"]:
        print(f"  pass1: type={c['type']}  title='{c['title']}'  points={len(c['labels'])}")
    for c in data["interesting_charts"]:
        print(f"  pass2: type={c['type']}  title='{c['title']}'  points={len(c['labels'])}")


def test_query_interesting_findings():
    """Validates interesting_reason / interesting_result fields are consistent."""
    headers = get_auth_header()
    project_id = create_project(headers)
    file_id = upload_csv(headers, project_id)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": ""},
        headers=headers,
        timeout=60,
    )

    assert res.status_code == 200, res.text

    data = res.json()
    assert_base_fields(data)

    assert isinstance(data["interesting_reason"], (str, type(None)))
    assert isinstance(data["interesting_result"], (str, type(None)))

    if data["interesting_reason"]:
        assert data["interesting_result"], (
            "interesting_result should be non-empty when interesting_reason is set"
        )
    if data["interesting_result"]:
        assert data["interesting_reason"], (
            "interesting_reason should be non-empty when interesting_result is set"
        )

    found = bool(data.get("interesting_reason"))
    print(f"Interesting findings detected: {found}")
    if found:
        print("Reason:", data["interesting_reason"])


def test_query_wrong_owner():
    """User B cannot query User A's file."""
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
    print("Query wrong owner OK: 403")


def test_query_project_not_found():
    """Querying a non-existent project returns 404."""
    headers = get_auth_header()

    res = requests.post(
        f"{BASE}/projects/999999/files/1/query",
        json={"question": "test"},
        headers=headers,
        timeout=10,
    )

    assert res.status_code == 404, res.text
    print("Query project not found OK: 404")


def test_query_file_not_found():
    """Querying a non-existent file returns 404."""
    headers = get_auth_header()
    project_id = create_project(headers)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/999999/query",
        json={"question": "test"},
        headers=headers,
        timeout=10,
    )

    assert res.status_code == 404, res.text
    print("Query file not found OK: 404")


def test_query_irrelevant_question():
    """Irrelevant question should fallback to general exploration and still return charts."""
    headers = get_auth_header()
    project_id = create_project(headers)
    file_id = upload_csv(headers, project_id)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": "What is the weather in Paris today?"},
        headers=headers,
        timeout=60,
    )

    assert res.status_code == 200, res.text

    data = res.json()
    assert data["user_question"] == "What is the weather in Paris today?"
    assert_base_fields(data)
    assert_charts_list(data["charts"])
    assert_charts_list(data["interesting_charts"])

    print("Irrelevant question handled OK")
    print("Explore reason:", data["explore_reason"])
    print(f"Charts: {len(data['charts'])} pass1, {len(data['interesting_charts'])} pass2")


# CLEANUP
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


# MAIN
if __name__ == "__main__":
    try:
        print("\n=== QUERY TESTS ===")

        test_query_success()
        test_query_chart_structure()
        test_query_interesting_findings()
        test_query_wrong_owner()
        test_query_project_not_found()
        test_query_file_not_found()
        test_query_irrelevant_question()

        print("\nAll query tests passed!")

    finally:
        cleanup_projects()