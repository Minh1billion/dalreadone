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


# HELPERS
def assert_base_fields(data: dict):
    """Assert fields present in every successful query response."""
    for field in ("explore_reason", "result", "insight", "code"):
        assert field in data, f"Missing field: {field}"
        assert data[field], f"{field} should not be empty"

    # interesting_* are optional but must be present as keys
    assert "interesting_reason" in data, "Missing key: interesting_reason"
    assert "interesting_result" in data, "Missing key: interesting_result"


def print_response(data: dict):
    print("Explore reason:", data["explore_reason"])
    print("Insight preview:", data["insight"][:100], "...")
    print("\n--- CODE ---")
    print(data["code"])
    print("\n--- RESULT ---")
    print(data["result"])
    if data.get("interesting_reason"):
        print("\n--- INTERESTING REASON ---")
        print(data["interesting_reason"])
    if data.get("interesting_result"):
        print("\n--- INTERESTING RESULT ---")
        print(data["interesting_result"])


# TESTS
def test_query_success():
    """Happy path: upload CSV then query."""
    headers = get_auth_header()
    project_id = create_project(headers)
    file_id = upload_csv(headers, project_id)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": "Which region has the highest revenue?"},
        headers=headers,
        timeout=60,
    )

    assert res.status_code == 200, res.text

    data = res.json()

    assert data["user_question"] == "Which region has the highest revenue?"
    assert_base_fields(data)

    print("Query success OK:", data["explore_reason"])
    print_response(data)


def test_query_interesting_findings():
    """
    Dataset with known anomalies (large revenue spike on one date, one region
    dominating) should trigger a non-null interesting_reason from pass 2.
    Not a hard assertion since LLM output is non-deterministic, but we verify
    the pipeline runs end-to-end and the fields are present and well-typed.
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

    # interesting_reason and interesting_result must be str or None — never crash
    assert isinstance(data["interesting_reason"], (str, type(None))), (
        "interesting_reason must be str or None"
    )
    assert isinstance(data["interesting_result"], (str, type(None))), (
        "interesting_result must be str or None"
    )

    # If pass 2 fired, both fields should be populated together
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
        print("Interesting reason:", data["interesting_reason"])
        print("Interesting result preview:", str(data["interesting_result"])[:200])


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
    """Irrelevant question should fallback to general exploration."""
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

    print("Irrelevant question handled OK")
    print("Explore reason:", data["explore_reason"])


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
        test_query_interesting_findings()
        test_query_wrong_owner()
        test_query_project_not_found()
        test_query_file_not_found()
        test_query_irrelevant_question()

        print("\nAll query tests passed!")

    finally:
        cleanup_projects()