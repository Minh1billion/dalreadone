import requests

BASE = "http://localhost:8000"

CREATED_PROJECT_IDS = []


def get_auth_header(username="proj_testuser", password="123456") -> tuple[dict, requests.Session]:
    session = requests.Session()
    session.post(f"{BASE}/auth/register", json={"username": username, "password": password})
    res = session.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, session


def create_project(headers, name="My Project") -> dict:
    """Helper tạo project và tự động track để cleanup sau."""
    res = requests.post(f"{BASE}/projects", json={"name": name}, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    CREATED_PROJECT_IDS.append((headers, data["id"]))
    return data


# CREATE 

def test_create_project():
    headers, _ = get_auth_header()
    data = create_project(headers, "My Project")

    assert data["name"] == "My Project"
    assert "id" in data
    assert "created_at" in data
    assert data["files"] == []
    print("Create project OK:", data)
    return data["id"]


def test_create_project_unauthorized():
    res = requests.post(f"{BASE}/projects", json={"name": "No Auth"})
    assert res.status_code == 401, res.text
    print("Create project unauthorized OK: 401")


# LIST 

def test_list_projects():
    headers, _ = get_auth_header()
    create_project(headers, "List Test Project")  # tracked

    res = requests.get(f"{BASE}/projects", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    print(f"List projects OK: {len(data)} projects")


def test_list_projects_only_own():
    headers_a, _ = get_auth_header("proj_user_a", "123456")
    headers_b, _ = get_auth_header("proj_user_b", "123456")

    data_a = create_project(headers_a, "User A Project")  # tracked
    project_id_a = data_a["id"]

    res_b = requests.get(f"{BASE}/projects", headers=headers_b)
    ids_b = [p["id"] for p in res_b.json()]
    assert project_id_a not in ids_b
    print("List projects isolation OK: User B cannot see User A's project")


# GET ONE 
def test_get_project():
    headers, _ = get_auth_header()
    project_id = test_create_project()

    res = requests.get(f"{BASE}/projects/{project_id}", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["id"] == project_id
    assert "files" in data
    print("Get project OK:", data)


def test_get_project_not_found():
    headers, _ = get_auth_header()
    res = requests.get(f"{BASE}/projects/999999", headers=headers)
    assert res.status_code == 404, res.text
    print("Get project not found OK: 404")

def test_get_project_wrong_owner():
    headers_a, _ = get_auth_header("proj_user_a", "123456")
    headers_b, _ = get_auth_header("proj_user_b", "123456")

    data = create_project(headers_a, "A's project")  # tracked
    project_id = data["id"]

    res = requests.get(f"{BASE}/projects/{project_id}", headers=headers_b)
    assert res.status_code == 403, res.text
    print("Get project wrong owner OK: 403")


# UPDATE 
def test_update_project():
    headers, _ = get_auth_header()
    project_id = test_create_project()

    res = requests.patch(
        f"{BASE}/projects/{project_id}",
        json={"name": "Renamed Project"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["name"] == "Renamed Project"
    print("Update project OK:", data)

def test_update_project_wrong_owner():
    headers_a, _ = get_auth_header("proj_user_a", "123456")
    headers_b, _ = get_auth_header("proj_user_b", "123456")

    data = create_project(headers_a, "A's project")
    project_id = data["id"]

    res = requests.patch(
        f"{BASE}/projects/{project_id}",
        json={"name": "Hacked"},
        headers=headers_b,
    )
    assert res.status_code == 403, res.text
    print("Update project wrong owner OK: 403")


# DELETE 
def test_delete_project():
    headers, _ = get_auth_header()
    project_id = test_create_project()

    res = requests.delete(f"{BASE}/projects/{project_id}", headers=headers)
    assert res.status_code == 204, res.text

    res = requests.get(f"{BASE}/projects/{project_id}", headers=headers)
    assert res.status_code == 404, res.text
    print("Delete project OK: 204 → 404")

    CREATED_PROJECT_IDS[:] = [
        (h, pid) for h, pid in CREATED_PROJECT_IDS if pid != project_id
    ]


def test_delete_project_wrong_owner():
    headers_a, _ = get_auth_header("proj_user_a", "123456")
    headers_b, _ = get_auth_header("proj_user_b", "123456")

    data = create_project(headers_a, "A's project")
    project_id = data["id"]

    res = requests.delete(f"{BASE}/projects/{project_id}", headers=headers_b)
    assert res.status_code == 403, res.text
    print("Delete project wrong owner OK: 403")


# CLEANUP 
def cleanup_projects():
    print("\n=== CLEANUP ===")
    for headers, project_id in CREATED_PROJECT_IDS:
        res = requests.delete(f"{BASE}/projects/{project_id}", headers=headers)
        if res.status_code in (204, 404):
            print(f"Cleaned project {project_id} (and its S3 files)")
        else:
            print(f"Failed to clean {project_id}: {res.status_code} - {res.text}")


# MAIN 
if __name__ == "__main__":
    try:
        print("\n=== CREATE ===")
        test_create_project()
        test_create_project_unauthorized()

        print("\n=== LIST ===")
        test_list_projects()
        test_list_projects_only_own()

        print("\n=== GET ===")
        test_get_project()
        test_get_project_not_found()
        test_get_project_wrong_owner()

        print("\n=== UPDATE ===")
        test_update_project()
        test_update_project_wrong_owner()

        print("\n=== DELETE ===")
        test_delete_project()
        test_delete_project_wrong_owner()

        print("\nAll project tests passed!")

    finally:
        cleanup_projects()