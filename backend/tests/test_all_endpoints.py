import sys
import uuid
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_full_suite():
    print("=== STARTING FULL BACKEND INTEGRATION TEST SUITE ===")
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("✓ 1. Health check online:", res.json())
    
    # 2. Admin Login
    res = client.post("/api/auth/login", json={
        "email": "admin@getitright.io",
        "password": "SuperAdminPassword2026!"
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    admin_data = res.json()
    assert admin_data.get("isAdmin") is True or admin_data.get("user", {}).get("role") == "admin"
    admin_token = admin_data["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✓ 2. Admin login successful:", admin_data.get("user", {}).get("full_name"))
    
    # 3. Customer Seed Login
    res = client.post("/api/auth/login", json={
        "email": "grace@umoja.org",
        "password": "Password123!"
    })
    assert res.status_code == 200, f"Seed user login failed: {res.text}"
    cust_data = res.json()
    print("✓ 3. Seed user login successful:", cust_data.get("user", {}).get("full_name"))
    
    # 4. Create new user (website/mobile registration)
    unique_email = f"test_{uuid.uuid4().hex[:6]}@civicguard.io"
    test_pw = "StrongPass2026!"
    res = client.post("/api/users", json={
        "name": "Jane Citizen",
        "email": unique_email,
        "password": test_pw,
        "role": "analyst",
        "organization": "Citizen Collective",
        "plan": "free"
    })
    assert res.status_code == 200, f"User creation failed: {res.text}"
    created_user = res.json()
    user_id = created_user["id"]
    print("✓ 4. New user registered successfully:", created_user["email"], "ID:", user_id)
    
    # 5. Login with newly created user
    res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": test_pw
    })
    assert res.status_code == 200, f"New user login failed: {res.text}"
    new_user_auth = res.json()
    user_token = new_user_auth["token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("✓ 5. Login with new user successful, token acquired")
    
    # 6. Choose / update plan (e.g. Free -> Civic Pro)
    res = client.post(f"/api/users/{user_id}/plan", json={"plan": "Civic Pro"}, headers=user_headers)
    assert res.status_code == 200, f"Plan update failed: {res.text}"
    updated_plan_user = res.json()
    # Backend stores canonical key "pro" in plan, display name "Civic Pro" in planName
    assert updated_plan_user.get("plan") == "pro" or updated_plan_user.get("planName") == "Civic Pro", f"Plan mismatch: {updated_plan_user}"
    print("✓ 6. User plan updated to Civic Pro:", updated_plan_user.get("planName"))
    
    # 7. Get user status
    res = client.post(f"/api/users/{user_id}/status", json={"status": "active"}, headers=admin_headers)
    assert res.status_code == 200, f"Status update failed: {res.text}"
    print("✓ 7. User status updated successfully")
    
    # 8. List Polls
    res = client.get("/api/polls")
    assert res.status_code == 200, f"List polls failed: {res.text}"
    polls = res.json()
    assert len(polls) > 0, "No polls found"
    first_poll = polls[0]
    poll_id = first_poll["id"]
    print(f"✓ 8. Listed {len(polls)} polls. Target poll ID: {poll_id}")
    
    # 9. Vote on Poll
    res = client.post(f"/api/polls/{poll_id}/vote", json={"optionIndex": 0, "voterKey": "citizen_42"}, headers=user_headers)
    assert res.status_code == 200, f"Vote failed: {res.text}"
    vote_res = res.json()
    assert "receiptHash" in vote_res or "receipt" in vote_res or "receipt_hash" in vote_res
    print("✓ 9. Vote submitted with cryptographic receipt:", vote_res.get("receiptHash") or vote_res.get("receipt"))
    
    # 10. List Surveys
    res = client.get("/api/surveys")
    assert res.status_code == 200, f"List surveys failed: {res.text}"
    surveys = res.json()
    print(f"✓ 10. Listed {len(surveys)} surveys")
    if surveys:
        survey_id = surveys[0]["id"]
        # Get first question ID if available
        questions = surveys[0].get("questions", [])
        q_id = questions[0]["id"] if questions else 1
        # 11. Submit survey response
        res = client.post(f"/api/surveys/{survey_id}/submit", json={
            "voterPseudonym": f"citizen_{user_id}",
            "answers": [{"questionId": q_id, "answer": "Strongly Agree"}]
        }, headers=user_headers)
        assert res.status_code == 200, f"Survey submit failed: {res.text}"
        print("✓ 11. Survey response submitted successfully via /submit")
    
    # 12. Governance Checkpoints
    res = client.get("/api/checkpoints")
    assert res.status_code == 200, f"Get checkpoints failed: {res.text}"
    print(f"✓ 12. Checkpoints retrieved: {len(res.json())} checkpoints")
    
    # 13. Publish Checkpoint
    res = client.post("/api/checkpoints/publish", json={"block_number": 9999}, headers=admin_headers)
    assert res.status_code == 200, f"Publish checkpoint failed: {res.text}"
    print("✓ 13. Published new checkpoint:", res.json().get("root_hash"))
    
    print("\nALL 13 BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY! 🚀")

if __name__ == "__main__":
    test_full_suite()
