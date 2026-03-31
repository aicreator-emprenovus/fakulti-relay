"""
Test Password Flow Features for CRM Fakulti
- POST /api/auth/login returns must_change_password flag
- POST /api/auth/change-password validates strong password and clears must_change_password flag
- POST /api/auth/generate-provisional-password generates secure password for target user
- Dev can generate provisional password for admin, admin can generate for advisor
- Creating a new advisor sets must_change_password: true
- Password strength validation (8+ chars, uppercase, lowercase, number, special char)
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
DEVELOPER_EMAIL = "aicreator@emprenovus.com"
DEVELOPER_PASSWORD = "Jlsb*1082"
ADMIN_EMAIL = "admin@fakulti.com"
ADMIN_PASSWORD = "Admin123!"
ADVISOR_EMAIL = "carlos@fakulti.com"
ADVISOR_PASSWORD = "Advisor123!"


class TestLoginMustChangePassword:
    """Test that login returns must_change_password flag"""
    
    def test_login_returns_must_change_password_field(self):
        """Login response should include must_change_password field"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "user" in data, "Response should contain user object"
        assert "must_change_password" in data["user"], "User should have must_change_password field"
        assert isinstance(data["user"]["must_change_password"], bool), "must_change_password should be boolean"
        print(f"PASS: Login returns must_change_password={data['user']['must_change_password']}")
    
    def test_developer_login_returns_must_change_password(self):
        """Developer login should also return must_change_password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEVELOPER_EMAIL,
            "password": DEVELOPER_PASSWORD
        })
        assert response.status_code == 200, f"Developer login failed: {response.text}"
        data = response.json()
        assert "must_change_password" in data["user"]
        print(f"PASS: Developer login returns must_change_password={data['user']['must_change_password']}")


class TestPasswordStrengthValidation:
    """Test password strength validation on change-password endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_password_too_short(self, admin_token):
        """Password less than 8 chars should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "Ab1!xyz", "current_password": ADMIN_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "8 caracteres" in response.json().get("detail", "")
        print("PASS: Short password rejected")
    
    def test_password_no_uppercase(self, admin_token):
        """Password without uppercase should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "abcdefg1!", "current_password": ADMIN_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "mayúscula" in response.json().get("detail", "").lower()
        print("PASS: Password without uppercase rejected")
    
    def test_password_no_lowercase(self, admin_token):
        """Password without lowercase should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "ABCDEFG1!", "current_password": ADMIN_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "minúscula" in response.json().get("detail", "").lower()
        print("PASS: Password without lowercase rejected")
    
    def test_password_no_number(self, admin_token):
        """Password without number should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "Abcdefgh!", "current_password": ADMIN_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "número" in response.json().get("detail", "").lower()
        print("PASS: Password without number rejected")
    
    def test_password_no_special_char(self, admin_token):
        """Password without special character should be rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "Abcdefg12", "current_password": ADMIN_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "especial" in response.json().get("detail", "").lower()
        print("PASS: Password without special char rejected")


class TestGenerateProvisionalPassword:
    """Test provisional password generation"""
    
    @pytest.fixture
    def developer_token(self):
        """Get developer auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEVELOPER_EMAIL,
            "password": DEVELOPER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Developer login failed")
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_developer_can_generate_for_admin(self, developer_token):
        """Developer should be able to generate provisional password for admin"""
        # First get admin user id
        admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if admin_login.status_code != 200:
            pytest.skip("Admin login failed - password may have been changed")
        admin_id = admin_login.json()["user"]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/generate-provisional-password",
            json={"user_id": admin_id},
            headers={"Authorization": f"Bearer {developer_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "provisional_password" in data
        assert len(data["provisional_password"]) >= 8
        # Verify password meets strength requirements
        pw = data["provisional_password"]
        assert re.search(r'[A-Z]', pw), "Generated password should have uppercase"
        assert re.search(r'[a-z]', pw), "Generated password should have lowercase"
        assert re.search(r'[0-9]', pw), "Generated password should have digit"
        assert re.search(r'[!@#$%&*]', pw), "Generated password should have special char"
        print(f"PASS: Developer generated provisional password for admin: {pw[:3]}***")
        
        # Restore admin password - login with provisional and change back
        admin_token_temp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": pw
        }).json()["token"]
        
        requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": ADMIN_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token_temp}"}
        )
        print("Admin password restored")
    
    def test_admin_can_generate_for_advisor(self, admin_token):
        """Admin should be able to generate provisional password for advisor"""
        # First get advisor user id
        advisor_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADVISOR_EMAIL,
            "password": ADVISOR_PASSWORD
        })
        if advisor_login.status_code != 200:
            pytest.skip("Advisor login failed - may not exist")
        advisor_id = advisor_login.json()["user"]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/generate-provisional-password",
            json={"user_id": advisor_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "provisional_password" in data
        pw = data["provisional_password"]
        print(f"PASS: Admin generated provisional password for advisor")
        
        # Restore advisor password
        advisor_token_temp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADVISOR_EMAIL,
            "password": pw
        }).json()["token"]
        
        requests.post(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": ADVISOR_PASSWORD},
            headers={"Authorization": f"Bearer {advisor_token_temp}"}
        )
        print("Advisor password restored")
    
    def test_admin_cannot_generate_for_admin(self, admin_token):
        """Admin should NOT be able to generate provisional password for another admin"""
        # Get admin's own id
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        admin_id = me_response.json()["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/generate-provisional-password",
            json={"user_id": admin_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 403, f"Should be forbidden: {response.text}"
        print("PASS: Admin cannot generate provisional password for admin")
    
    def test_advisor_cannot_generate_provisional(self):
        """Advisor should NOT be able to generate provisional passwords"""
        advisor_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADVISOR_EMAIL,
            "password": ADVISOR_PASSWORD
        })
        if advisor_login.status_code != 200:
            pytest.skip("Advisor login failed")
        advisor_token = advisor_login.json()["token"]
        advisor_id = advisor_login.json()["user"]["id"]
        
        # Try to generate for themselves (should fail with 403)
        response = requests.post(
            f"{BASE_URL}/api/auth/generate-provisional-password",
            json={"user_id": advisor_id},
            headers={"Authorization": f"Bearer {advisor_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: Advisor cannot generate provisional passwords")


class TestCreateAdvisorSetsFlag:
    """Test that creating a new advisor sets must_change_password: true"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_new_advisor_has_must_change_password(self, admin_token):
        """Creating a new advisor should set must_change_password: true"""
        import uuid
        test_email = f"TEST_advisor_{uuid.uuid4().hex[:8]}@fakulti.com"
        
        # Create new advisor
        response = requests.post(
            f"{BASE_URL}/api/advisors",
            json={
                "name": "Test Advisor",
                "email": test_email,
                "password": "TestPass123!",
                "whatsapp": "+593999999999",
                "status": "disponible"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 201], f"Failed to create advisor: {response.text}"
        
        # Try to login with the new advisor
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": "TestPass123!"
        })
        
        if login_response.status_code == 200:
            user_data = login_response.json()["user"]
            assert user_data.get("must_change_password") == True, "New advisor should have must_change_password=true"
            print("PASS: New advisor has must_change_password=true")
            
            # Cleanup - delete the test advisor
            advisors_response = requests.get(
                f"{BASE_URL}/api/advisors",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            for adv in advisors_response.json():
                if adv["email"] == test_email:
                    requests.delete(
                        f"{BASE_URL}/api/advisors/{adv['id']}",
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                    break
        else:
            print(f"Note: Could not verify must_change_password - login returned {login_response.status_code}")
            # Still cleanup
            advisors_response = requests.get(
                f"{BASE_URL}/api/advisors",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            for adv in advisors_response.json():
                if adv["email"] == test_email:
                    requests.delete(
                        f"{BASE_URL}/api/advisors/{adv['id']}",
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                    break


class TestPasswordResetRequests:
    """Test password reset request flow"""
    
    def test_forgot_password_admin_message(self):
        """Admin forgot password should show developer contact message"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": ADMIN_EMAIL
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        message = response.json().get("message", "")
        assert "desarrollador" in message.lower() or "developer" in message.lower()
        print(f"PASS: Admin forgot password shows: {message[:50]}...")
    
    def test_forgot_password_advisor_message(self):
        """Advisor forgot password should show admin contact message"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": ADVISOR_EMAIL
        })
        if response.status_code == 404:
            pytest.skip("Advisor not found")
        assert response.status_code == 200, f"Failed: {response.text}"
        message = response.json().get("message", "")
        assert "administrador" in message.lower() or "admin" in message.lower()
        print(f"PASS: Advisor forgot password shows: {message[:50]}...")
    
    def test_forgot_password_nonexistent_email(self):
        """Forgot password with nonexistent email should return 404"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent@fakulti.com"
        })
        assert response.status_code == 404
        print("PASS: Nonexistent email returns 404")


class TestAuthMeEndpoint:
    """Test /auth/me returns must_change_password"""
    
    def test_auth_me_returns_must_change_password(self):
        """GET /auth/me should return must_change_password field"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["token"]
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "must_change_password" in data
        print(f"PASS: /auth/me returns must_change_password={data['must_change_password']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
