import io
import os
import requests

BASE = "http://localhost:8000/api"
CREATED_PROJECTS: list[tuple[dict, int]] = []
CSV_PATH = os.path.join(os.path.dirname(__file__), "data.csv")


def get_auth_header(username: str, password="123456") -> dict:
    session = requests.Session()
    session.post(f"{BASE}/auth/register", json={"username": username, "password": password})
    res = session.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def create_project(headers: dict, name="History Test Project") -> int:
    res = requests.post(f"{BASE}/projects", json={"name": name}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]
    CREATED_PROJECTS.append((headers, project_id))
    return project_id


def upload_csv(headers: dict, project_id: int) -> int:
    with open(CSV_PATH, "rb") as f:
        content = f.read()
    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files={"file": ("data.csv", io.BytesIO(content), "text/csv")},
        headers=headers,
    )
    assert res.status_code == 201, f"Upload failed: {res.text}"
    return res.json()["id"]


def run_query(headers: dict, project_id: int, file_id: int, question="") -> dict:
    res = requests.post(
        f"{BASE}/projects/{project_id}/files/{file_id}/query",
        json={"question": question},
        headers=headers,
        timeout=60,
    )
    assert res.status_code == 200, res.text
    return res.json()


class _Fixture:
    """
    Shared fixture — creates one user, project, file, and query result.
    Reused across all tests to minimize LLM calls.
    Reset after test_history_delete so the fixture can be recreated cleanly.
    """
    headers: dict = None
    headers_b: dict = None
    project_id: int = None
    file_id: int = None
    record_id: int = None
    question = "What is the total revenue?"

    @classmethod
    def get(cls):
        if cls.file_id is None:
            cls.headers    = get_auth_header("history_user_main")
            cls.headers_b  = get_auth_header("history_user_b")
            cls.project_id = create_project(cls.headers, "History Shared Project")
            cls.file_id    = upload_csv(cls.headers, cls.project_id)
            run_query(cls.headers, cls.project_id, cls.file_id, question=cls.question)
            items = requests.get(f"{BASE}/history", headers=cls.headers).json()
            cls.record_id = items[0]["id"]
        return cls.headers, cls.project_id, cls.file_id


def test_history_created_after_query():
    """Query must create a history record with all required fields."""
    headers, _, _ = _Fixture.get()

    items = requests.get(f"{BASE}/history", headers=headers).json()
    assert len(items) >= 1

    item = items[0]
    for field in ("id", "filename", "insight", "created_at", "project_id", "file_id"):
        assert field in item, f"Missing field: {field}"

    print(f"test_history_created_after_query OK: {len(items)} item(s), insight={item['insight'][:80]!r}")


def test_history_list_pagination():
    """limit/offset params must slice the list correctly."""
    headers, _, _ = _Fixture.get()

    total = len(requests.get(f"{BASE}/history", headers=headers).json())
    res1  = requests.get(f"{BASE}/history?limit=1&offset=0", headers=headers)
    assert res1.status_code == 200
    assert len(res1.json()) == min(1, total)

    if total > 1:
        res2 = requests.get(f"{BASE}/history?limit=1&offset=1", headers=headers)
        assert res1.json()[0]["id"] != res2.json()[0]["id"]

    print(f"test_history_list_pagination OK: total={total}")


def test_history_detail_has_result_json():
    """Detail endpoint must return full result_json with all QueryResponse fields."""
    headers, _, _ = _Fixture.get()

    res = requests.get(f"{BASE}/history/{_Fixture.record_id}", headers=headers)
    assert res.status_code == 200, res.text

    rj = res.json().get("result_json", {})
    for field in ("insight", "result", "code", "charts", "interesting_charts", "cost_report"):
        assert field in rj, f"result_json missing field: {field}"

    print(f"test_history_detail_has_result_json OK: id={_Fixture.record_id}")


def test_history_detail_not_found():
    """Non-existent history id must return 404."""
    headers, _, _ = _Fixture.get()
    assert requests.get(f"{BASE}/history/999999", headers=headers).status_code == 404
    print("test_history_detail_not_found OK: 404")


def test_history_question_stored_correctly():
    """Question sent during query must be persisted in the history record."""
    headers, _, _ = _Fixture.get()
    items = requests.get(f"{BASE}/history", headers=headers).json()
    assert items[0]["question"] == _Fixture.question
    print(f"test_history_question_stored_correctly OK: {_Fixture.question!r}")


def test_history_isolation():
    """User B must not be able to list, view, or delete User A's history."""
    _Fixture.get()
    headers_b = _Fixture.headers_b
    record_id = _Fixture.record_id

    ids_b = [i["id"] for i in requests.get(f"{BASE}/history", headers=headers_b).json()]
    assert record_id not in ids_b, "User B can see User A's history — isolation broken"

    assert requests.get(f"{BASE}/history/{record_id}", headers=headers_b).status_code == 404
    assert requests.delete(f"{BASE}/history/{record_id}", headers=headers_b).status_code == 404

    print(f"test_history_isolation OK: user B blocked from record {record_id}")


def test_history_auto_explore_question_is_null():
    """Auto-explore (empty question) must store null in the history record."""
    headers    = get_auth_header("history_null_q_user")
    project_id = create_project(headers, "Null Question Project")
    file_id    = upload_csv(headers, project_id)
    run_query(headers, project_id, file_id, question="")

    items = requests.get(f"{BASE}/history", headers=headers).json()
    assert items[0]["question"] is None, f"Expected null, got {items[0]['question']!r}"
    print("test_history_auto_explore_question_is_null OK")


def test_history_delete():
    """DELETE must remove the record; further GET and DELETE must return 404."""
    headers, _, _ = _Fixture.get()
    record_id = _Fixture.record_id

    assert requests.delete(f"{BASE}/history/{record_id}", headers=headers).status_code == 204
    assert requests.get(f"{BASE}/history/{record_id}", headers=headers).status_code == 404
    assert requests.delete(f"{BASE}/history/999999", headers=headers).status_code == 404

    # Reset fixture so tests that run after this get a fresh record
    _Fixture.record_id = None
    _Fixture.file_id   = None

    print(f"test_history_delete OK: id={record_id} → 404")


def cleanup():
    print("\n=== CLEANUP ===")
    for headers, project_id in CREATED_PROJECTS:
        res = requests.delete(f"{BASE}/projects/{project_id}", headers=headers)
        if res.status_code in (204, 404):
            print(f"Cleaned project {project_id}")
        else:
            print(f"Failed to clean {project_id}: {res.status_code} - {res.text}")


if __name__ == "__main__":
    try:
        test_history_created_after_query()
        test_history_list_pagination()
        test_history_detail_has_result_json()
        test_history_detail_not_found()
        test_history_question_stored_correctly()
        test_history_isolation()
        test_history_auto_explore_question_is_null()
        test_history_delete()

        print("\nAll history tests passed!")
    finally:
        cleanup()