import requests

BASE = "http://localhost:8000"
session = requests.Session()


# Register  
def test_register():
    res = session.post(f"{BASE}/auth/register", json={
        "username": "testuser",
        "password": "123456"
    })
    assert res.status_code == 201, res.text
    data = res.json()
    assert "access_token" in data
    print("Register OK:", data["access_token"][:40], "...")
    return data["access_token"]


#   Login  
def test_login():
    res = session.post(f"{BASE}/auth/login", json={
        "username": "testuser",
        "password": "123456"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    print("Login OK:", data["access_token"][:40], "...")
    return data["access_token"]

def test_login_wrong_password():
    res = session.post(f"{BASE}/auth/login", json={
        "username": "testuser",
        "password": "wrongpass"
    })
    assert res.status_code == 401, res.text
    print("Login wrong password OK: 401")

def test_login_wrong_username():
    res = session.post(f"{BASE}/auth/login", json={
        "username": "nobody",
        "password": "123456"
    })
    assert res.status_code == 401, res.text
    print("Login wrong username OK: 401")


#   Refresh  
def test_refresh():
    res = session.post(f"{BASE}/auth/refresh")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    print("Refresh OK:", data["access_token"][:40], "...")
    return data["access_token"]


#   Logout  
def test_logout():
    res = session.post(f"{BASE}/auth/logout")
    assert res.status_code == 200, res.text
    print("Logout OK:", res.json())

def test_refresh_after_logout():
    res = session.post(f"{BASE}/auth/refresh")
    assert res.status_code == 401, res.text
    print("Refresh after logout OK: 401")


#   OAuth  
def test_oauth_links():
    print("\nOAuth URLs:")
    print("Google :", f"{BASE}/auth/google")
    print("Github :", f"{BASE}/auth/github")


#   Run  
if __name__ == "__main__":
    print("\n=== REGISTER ===")
    test_register()

    print("\n=== LOGIN ===")
    test_login()
    test_login_wrong_password()
    test_login_wrong_username()

    print("\n=== REFRESH ===")
    test_refresh()

    print("\n=== LOGOUT ===")
    test_logout()
    test_refresh_after_logout()

    print("\n=== OAUTH ===")
    test_oauth_links()

    print("\nAll tests passed!")