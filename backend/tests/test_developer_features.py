"""
Test Developer Role, Bot Training Center, and Password Reset Features
- Developer login and role verification
- Bot training global config (developer only)
- Knowledge base CRUD (developer only)
- Bot test console (developer only)
- Forgot password flow (admin vs advisor messages)
- Password reset management (developer resets admin, admin resets advisor)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEV_EMAIL = "dev@fakulti.com"
DEV_PASSWORD = "dev2026"
ADMIN_EMAIL = "admin@fakulti.com"
ADMIN_PASSWORD = "admin123"
ADVISOR_EMAIL = "carlos@fakulti.com"  # Existing advisor

class TestDeveloperLogin:
    """Test developer authentication"""
    
    def test_developer_login_success(self):
        """Developer can login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL,
            "password": DEV_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "developer"
        assert data["user"]["email"] == DEV_EMAIL
        print(f"Developer login successful: {data['user']['name']}")
    
    def test_admin_login_still_works(self):
        """Admin can still login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "admin"
        print(f"Admin login successful: {data['user']['name']}")


class TestBotTrainingGlobalConfig:
    """Test bot training global config endpoints (developer only)"""
    
    @pytest.fixture
    def dev_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL, "password": DEV_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Developer login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_get_global_config_developer(self, dev_token):
        """Developer can access global bot config"""
        response = requests.get(
            f"{BASE_URL}/api/bot-training/global-config",
            headers={"Authorization": f"Bearer {dev_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "bot_name" in data
        assert "tone" in data
        assert "brand_name" in data
        print(f"Bot config retrieved: bot_name={data['bot_name']}, brand={data['brand_name']}")
    
    def test_get_global_config_admin_blocked(self, admin_token):
        """Admin CANNOT access global bot config (403)"""
        response = requests.get(
            f"{BASE_URL}/api/bot-training/global-config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Admin correctly blocked from bot-training/global-config")
    
    def test_update_global_config_developer(self, dev_token):
        """Developer can update global bot config"""
        new_config = {
            "bot_name": "TEST_Bot Fakulti",
            "tone": "TEST_Amigable y profesional"
        }
        response = requests.put(
            f"{BASE_URL}/api/bot-training/global-config",
            headers={"Authorization": f"Bearer {dev_token}"},
            json=new_config
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["bot_name"] == "TEST_Bot Fakulti"
        print(f"Bot config updated: {data['bot_name']}")
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/bot-training/global-config",
            headers={"Authorization": f"Bearer {dev_token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["bot_name"] == "TEST_Bot Fakulti"
        print("Config persistence verified")
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/bot-training/global-config",
            headers={"Authorization": f"Bearer {dev_token}"},
            json={"bot_name": "Asesor Virtual Fakulti", "tone": "Cercano, experto, humano, confiable. Ciencia + natural = Biotecnología."}
        )


class TestKnowledgeBaseCRUD:
    """Test knowledge base CRUD (developer only)"""
    
    @pytest.fixture
    def dev_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL, "password": DEV_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Developer login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_knowledge_base_crud_flow(self, dev_token):
        """Full CRUD flow for knowledge base entries"""
        headers = {"Authorization": f"Bearer {dev_token}"}
        
        # CREATE
        create_response = requests.post(
            f"{BASE_URL}/api/bot-training/knowledge-base",
            headers=headers,
            json={
                "question": "TEST_¿Hacen envíos a Galápagos?",
                "answer": "TEST_Sí, hacemos envíos a todas las islas de Galápagos.",
                "category": "envios"
            }
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        entry = create_response.json()
        assert "id" in entry
        assert entry["question"] == "TEST_¿Hacen envíos a Galápagos?"
        entry_id = entry["id"]
        print(f"Knowledge entry created: {entry_id}")
        
        # READ (list)
        list_response = requests.get(
            f"{BASE_URL}/api/bot-training/knowledge-base",
            headers=headers
        )
        assert list_response.status_code == 200
        entries = list_response.json()
        assert any(e["id"] == entry_id for e in entries)
        print(f"Knowledge base has {len(entries)} entries")
        
        # UPDATE
        update_response = requests.put(
            f"{BASE_URL}/api/bot-training/knowledge-base/{entry_id}",
            headers=headers,
            json={"answer": "TEST_Sí, envíos a Galápagos con costo adicional."}
        )
        assert update_response.status_code == 200
        assert update_response.json()["answer"] == "TEST_Sí, envíos a Galápagos con costo adicional."
        print("Knowledge entry updated")
        
        # DELETE
        delete_response = requests.delete(
            f"{BASE_URL}/api/bot-training/knowledge-base/{entry_id}",
            headers=headers
        )
        assert delete_response.status_code == 200
        print("Knowledge entry deleted")
        
        # Verify deletion
        list_after = requests.get(
            f"{BASE_URL}/api/bot-training/knowledge-base",
            headers=headers
        )
        assert not any(e["id"] == entry_id for e in list_after.json())
        print("Deletion verified")
    
    def test_knowledge_base_admin_blocked(self, admin_token):
        """Admin CANNOT access knowledge base"""
        response = requests.get(
            f"{BASE_URL}/api/bot-training/knowledge-base",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Admin correctly blocked from knowledge base")


class TestBotTestConsole:
    """Test bot test console (developer only)"""
    
    @pytest.fixture
    def dev_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL, "password": DEV_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Developer login failed")
        return response.json()["token"]
    
    def test_bot_test_console(self, dev_token):
        """Developer can test bot responses"""
        response = requests.post(
            f"{BASE_URL}/api/bot-training/test",
            headers={"Authorization": f"Bearer {dev_token}"},
            json={"message": "Hola, quiero información sobre Bombro"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        print(f"Bot test reply: {data['reply'][:100]}...")


class TestForgotPasswordFlow:
    """Test forgot password flow with role-based messages"""
    
    def test_forgot_password_admin_message(self):
        """Admin forgot password shows developer message"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": ADMIN_EMAIL}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "desarrollador" in data["message"].lower()
        assert data["message"] == "La solicitud fue enviada al desarrollador del sistema"
        print(f"Admin forgot password message: {data['message']}")
    
    def test_forgot_password_advisor_message(self):
        """Advisor forgot password shows admin message"""
        # First check if advisor exists
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if admin_response.status_code != 200:
            pytest.skip("Admin login failed")
        admin_token = admin_response.json()["token"]
        
        # Get advisors list
        advisors_response = requests.get(
            f"{BASE_URL}/api/advisors",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if advisors_response.status_code != 200:
            pytest.skip("Could not get advisors")
        
        advisors = advisors_response.json()
        if not advisors:
            pytest.skip("No advisors found")
        
        advisor_email = advisors[0]["email"]
        
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": advisor_email}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "administrador" in data["message"].lower()
        assert data["message"] == "La solicitud fue enviada al Administrador del sistema"
        print(f"Advisor forgot password message: {data['message']}")
    
    def test_forgot_password_nonexistent_email(self):
        """Nonexistent email returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "nonexistent@fakulti.com"}
        )
        assert response.status_code == 404
        print("Nonexistent email correctly returns 404")


class TestPasswordResetRequests:
    """Test password reset request management"""
    
    @pytest.fixture
    def dev_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL, "password": DEV_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Developer login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_get_reset_requests_developer(self, dev_token):
        """Developer can see admin reset requests"""
        response = requests.get(
            f"{BASE_URL}/api/auth/password-reset-requests",
            headers={"Authorization": f"Bearer {dev_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Developer sees {len(data)} pending reset requests")
    
    def test_get_reset_requests_admin(self, admin_token):
        """Admin can see advisor reset requests"""
        response = requests.get(
            f"{BASE_URL}/api/auth/password-reset-requests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin sees {len(data)} pending reset requests")


class TestDirectPasswordReset:
    """Test direct password reset permissions"""
    
    @pytest.fixture
    def dev_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL, "password": DEV_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Developer login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_developer_can_reset_admin_password(self, dev_token):
        """Developer can reset admin password"""
        # Get admin user ID
        admins_response = requests.get(
            f"{BASE_URL}/api/bot-training/admins",
            headers={"Authorization": f"Bearer {dev_token}"}
        )
        assert admins_response.status_code == 200
        admins = admins_response.json()
        if not admins:
            pytest.skip("No admins found")
        
        admin_id = admins[0]["id"]
        
        # Reset password
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password-direct",
            headers={"Authorization": f"Bearer {dev_token}"},
            json={"user_id": admin_id, "new_password": "admin123"}  # Reset to same password
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"Developer reset admin password successfully")
    
    def test_admin_can_reset_advisor_password(self, admin_token):
        """Admin can reset advisor password"""
        # Get advisors
        advisors_response = requests.get(
            f"{BASE_URL}/api/advisors",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if advisors_response.status_code != 200:
            pytest.skip("Could not get advisors")
        
        advisors = advisors_response.json()
        if not advisors:
            pytest.skip("No advisors found")
        
        advisor_id = advisors[0]["id"]
        
        # Reset password
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password-direct",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": advisor_id, "new_password": "advisor123"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"Admin reset advisor password successfully")
    
    def test_admin_cannot_reset_admin_password(self, admin_token, dev_token):
        """Admin CANNOT reset another admin's password"""
        # Get admin user ID
        admins_response = requests.get(
            f"{BASE_URL}/api/bot-training/admins",
            headers={"Authorization": f"Bearer {dev_token}"}
        )
        if admins_response.status_code != 200:
            pytest.skip("Could not get admins")
        
        admins = admins_response.json()
        if not admins:
            pytest.skip("No admins found")
        
        admin_id = admins[0]["id"]
        
        # Try to reset admin password with admin token
        response = requests.post(
            f"{BASE_URL}/api/auth/reset-password-direct",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": admin_id, "new_password": "newpassword123"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("Admin correctly blocked from resetting admin password")


class TestDeveloperAdminsList:
    """Test developer can see admins list"""
    
    @pytest.fixture
    def dev_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEV_EMAIL, "password": DEV_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Developer login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_developer_can_see_admins(self, dev_token):
        """Developer can see list of admins"""
        response = requests.get(
            f"{BASE_URL}/api/bot-training/admins",
            headers={"Authorization": f"Bearer {dev_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        admins = response.json()
        assert isinstance(admins, list)
        # Verify no password_hash in response
        for admin in admins:
            assert "password_hash" not in admin
        print(f"Developer sees {len(admins)} admins")
    
    def test_admin_cannot_see_admins_list(self, admin_token):
        """Admin CANNOT access admins list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/bot-training/admins",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Admin correctly blocked from admins list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
