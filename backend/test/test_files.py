import io
import requests

BASE = "http://localhost:8000"

CREATED_PROJECTS: list[tuple[dict, int]] = []


def get_auth_header(username="file_testuser", password="123456") -> dict:
    session = requests.Session()
    session.post(f"{BASE}/auth/register", json={"username": username, "password": password})
    res = session.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(headers: dict, name="Test Project") -> int:
    res = requests.post(f"{BASE}/projects", json={"name": name}, headers=headers)
    assert res.status_code == 201, res.text
    project_id = res.json()["id"]
    CREATED_PROJECTS.append((headers, project_id))
    return project_id


def make_file(filename="data.csv", content=b"id,name\n1,foo") -> dict:
    return {"file": (filename, io.BytesIO(content), "text/csv")}


# UPLOAD 
def test_upload_file():
    headers = get_auth_header()
    project_id = create_project(headers)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file("report.csv"),
        headers=headers,
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["filename"] == "report.csv"
    assert data["project_id"] == project_id
    assert "id" in data
    assert "uploaded_at" in data
    print("Upload file OK:", data)


def test_upload_invalid_type():
    headers = get_auth_header()
    project_id = create_project(headers)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files={"file": ("malware.exe", io.BytesIO(b"bad"), "application/octet-stream")},
        headers=headers,
    )
    assert res.status_code == 400, res.text
    print("Upload invalid type OK: 400")


def test_upload_wrong_owner():
    headers_a = get_auth_header("file_user_a", "123456")
    headers_b = get_auth_header("file_user_b", "123456")
    project_id = create_project(headers_a)

    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file(),
        headers=headers_b,
    )
    assert res.status_code == 403, res.text
    print("Upload wrong owner OK: 403")


def test_upload_exceeds_limit():
    headers = get_auth_header("file_limit_user", "123456")
    project_id = create_project(headers, name="Limit Project")

    for i in range(5):
        res = requests.post(
            f"{BASE}/projects/{project_id}/files",
            files=make_file(f"file_{i}.csv"),
            headers=headers,
        )
        assert res.status_code == 201, f"File {i} failed: {res.text}"

    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file("file_6.csv"),
        headers=headers,
    )
    assert res.status_code == 400, res.text
    print("Upload exceeds limit OK: 400 on 6th file")


def test_upload_overwrite():
    headers = get_auth_header()
    project_id = create_project(headers)

    requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file("data.csv", b"v1"),
        headers=headers,
    )

    res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file("data.csv", b"v2"),
        headers=headers,
    )
    assert res.status_code == 201, res.text

    res_list = requests.get(f"{BASE}/projects/{project_id}/files", headers=headers)
    files = res_list.json()
    names = [f["filename"] for f in files]
    assert names.count("data.csv") == 1
    print("Upload overwrite OK: still 1 file after re-upload")


# LIST 
def test_list_files():
    headers = get_auth_header()
    project_id = create_project(headers)

    requests.post(f"{BASE}/projects/{project_id}/files", files=make_file("a.csv"), headers=headers)
    requests.post(f"{BASE}/projects/{project_id}/files", files=make_file("b.xlsx"), headers=headers)

    res = requests.get(f"{BASE}/projects/{project_id}/files", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) == 2
    print(f"List files OK: {len(data)} files")


def test_list_files_wrong_owner():
    headers_a = get_auth_header("file_user_a", "123456")
    headers_b = get_auth_header("file_user_b", "123456")
    project_id = create_project(headers_a)

    res = requests.get(f"{BASE}/projects/{project_id}/files", headers=headers_b)
    assert res.status_code == 403, res.text
    print("List files wrong owner OK: 403")


# DELETE 
def test_delete_file():
    headers = get_auth_header()
    project_id = create_project(headers)

    upload_res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file("todelete.csv"),
        headers=headers,
    )
    file_id = upload_res.json()["id"]

    res = requests.delete(f"{BASE}/projects/{project_id}/files/{file_id}", headers=headers)
    assert res.status_code == 204, res.text

    list_res = requests.get(f"{BASE}/projects/{project_id}/files", headers=headers)
    ids = [f["id"] for f in list_res.json()]
    assert file_id not in ids
    print("Delete file OK: 204 removed from list")


def test_delete_file_wrong_owner():
    headers_a = get_auth_header("file_user_a", "123456")
    headers_b = get_auth_header("file_user_b", "123456")
    project_id = create_project(headers_a)

    upload_res = requests.post(
        f"{BASE}/projects/{project_id}/files",
        files=make_file(),
        headers=headers_a,
    )
    file_id = upload_res.json()["id"]

    res = requests.delete(f"{BASE}/projects/{project_id}/files/{file_id}", headers=headers_b)
    assert res.status_code == 403, res.text
    print("Delete file wrong owner OK: 403")


def test_delete_file_not_found():
    headers = get_auth_header()
    project_id = create_project(headers)

    res = requests.delete(f"{BASE}/projects/{project_id}/files/999999", headers=headers)
    assert res.status_code == 404, res.text
    print("Delete file not found OK: 404")


def test_delete_project_cascades_files():
    headers = get_auth_header()
    project_id = create_project(headers)

    requests.post(f"{BASE}/projects/{project_id}/files", files=make_file("cascade.csv"), headers=headers)

    requests.delete(f"{BASE}/projects/{project_id}", headers=headers)

    CREATED_PROJECTS[:] = [(h, pid) for h, pid in CREATED_PROJECTS if pid != project_id]

    res = requests.get(f"{BASE}/projects/{project_id}/files", headers=headers)
    assert res.status_code == 404, res.text
    print("Delete project cascades files OK: 404 on files endpoint")


def cleanup_projects():
    print("\n=== CLEANUP ===")
    for headers, project_id in CREATED_PROJECTS:
        res = requests.delete(f"{BASE}/projects/{project_id}", headers=headers)
        if res.status_code in (204, 404):
            print(f"Cleaned project {project_id} (and its S3 files)")
        else:
            print(f"Failed to clean {project_id}: {res.status_code} - {res.text}")


if __name__ == "__main__":
    try:
        print("\n=== UPLOAD ===")
        test_upload_file()
        test_upload_invalid_type()
        test_upload_wrong_owner()
        test_upload_exceeds_limit()
        test_upload_overwrite()

        print("\n=== LIST ===")
        test_list_files()
        test_list_files_wrong_owner()

        print("\n=== DELETE ===")
        test_delete_file()
        test_delete_file_wrong_owner()
        test_delete_file_not_found()
        test_delete_project_cascades_files()

        print("\nAll file tests passed!")

    finally:
        cleanup_projects()