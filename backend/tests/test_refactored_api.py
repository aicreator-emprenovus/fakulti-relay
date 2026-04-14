"""
Comprehensive API tests for CRM Fakulti after refactoring.
Tests all major endpoints to ensure the refactoring from 4647 lines to modular files works correctly.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@fakulti.com"
ADMIN_PASSWORD = "Admin123!"
DEVELOPER_EMAIL = "aicreator@emprenovus.com"
DEVELOPER_PASSWORD = "Jlsb*1082"


class TestHealthAndBasics:
    """Basic health check and connectivity tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health endpoint working")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login(self):
        """Login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['name']}")
        return data["token"]
    
    def test_developer_login(self):
        """Login with developer credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEVELOPER_EMAIL,
            "password": DEVELOPER_PASSWORD
        })
        assert response.status_code == 200, f"Developer login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "developer"
        print(f"✓ Developer login successful: {data['user']['name']}")
        return data["token"]
    
    def test_invalid_login(self):
        """Login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")
    
    def test_auth_me_endpoint(self):
        """GET /api/auth/me returns current user info"""
        token = self.test_admin_login()
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert "must_change_password" in data
        print(f"✓ Auth me endpoint working: {data['name']}")
    
    def test_password_reset_requests(self):
        """GET /api/auth/password-reset-requests returns list"""
        token = self.test_developer_login()
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/password-reset-requests", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Password reset requests endpoint working: {len(data)} requests")
    
    def test_change_password_validation(self):
        """POST /api/auth/change-password validates strong password"""
        token = self.test_admin_login()
        headers = {"Authorization": f"Bearer {token}"}
        # Test weak password rejection
        response = requests.post(f"{BASE_URL}/api/auth/change-password", 
            headers=headers,
            json={"current_password": ADMIN_PASSWORD, "new_password": "weak"})
        assert response.status_code == 400
        print("✓ Weak password correctly rejected")


class TestDashboard:
    """Dashboard endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_dashboard_stats(self, auth_token):
        """GET /api/dashboard/stats returns total_leads, stages, total_sales"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "stages" in data
        assert "total_sales" in data
        assert isinstance(data["stages"], dict)
        print(f"✓ Dashboard stats: {data['total_leads']} leads, ${data['total_sales']} sales")
    
    def test_advisor_stats(self, auth_token):
        """GET /api/dashboard/advisor-stats returns advisor dashboard data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/advisor-stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "advisors" in data
        assert "summary" in data
        print(f"✓ Advisor stats: {len(data['advisors'])} advisors")


class TestLeads:
    """Leads CRUD endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_leads(self, auth_token):
        """GET /api/leads returns object with leads array and total"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/leads", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        assert isinstance(data["leads"], list)
        print(f"✓ Leads endpoint: {data['total']} leads returned")
    
    def test_create_lead(self, auth_token):
        """POST /api/leads creates a lead"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        lead_data = {
            "name": "TEST_Lead Pytest",
            "whatsapp": "0999999999",
            "city": "Quito",
            "email": "test@pytest.com",
            "product_interest": "Bombro",
            "source": "pytest",
            "funnel_stage": "nuevo",
            "notes": "Created by pytest"
        }
        response = requests.post(f"{BASE_URL}/api/leads", headers=headers, json=lead_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Lead Pytest"
        assert "id" in data
        print(f"✓ Lead created: {data['id']}")
        
        # Cleanup - delete the test lead
        requests.delete(f"{BASE_URL}/api/leads/{data['id']}", headers=headers)
        return data["id"]


class TestProducts:
    """Products endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_products(self, auth_token):
        """GET /api/products returns 5 products"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5, f"Expected at least 5 products, got {len(data)}"
        print(f"✓ Products endpoint: {len(data)} products returned")
        # Verify product structure
        if data:
            product = data[0]
            assert "id" in product
            assert "name" in product
            assert "price" in product


class TestAdvisors:
    """Advisors endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_advisors(self, auth_token):
        """GET /api/advisors returns advisors list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/advisors", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Advisors endpoint: {len(data)} advisors returned")
    
    def test_advisor_notifications(self, auth_token):
        """GET /api/advisors/notifications returns advisor notifications"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/advisors/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Advisor notifications: {len(data)} notifications")


class TestAutomation:
    """Automation rules endpoint tests - READ ONLY to avoid data loss"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_automation_rules(self, auth_token):
        """GET /api/automation/rules returns 10 rules"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/automation/rules", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 10, f"Expected at least 10 rules, got {len(data)}"
        print(f"✓ Automation rules: {len(data)} rules returned")
    
    def test_export_automation_rules(self, auth_token):
        """GET /api/automation/rules/export returns all rules as JSON array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/automation/rules/export", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Automation rules export: {len(data)} rules")


class TestConfig:
    """Configuration endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_whatsapp_config(self, auth_token):
        """GET /api/config/whatsapp returns WA config with business_name"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/config/whatsapp", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "business_name" in data
        print(f"✓ WhatsApp config: {data.get('business_name', 'N/A')}")
    
    def test_ai_config(self, auth_token):
        """GET /api/config/ai returns AI config"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/config/ai", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "intent_analysis" in data
        print(f"✓ AI config: intent_analysis={data.get('intent_analysis')}")


class TestCampaigns:
    """Campaigns endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_campaigns(self, auth_token):
        """GET /api/campaigns returns campaigns array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Campaigns: {len(data)} campaigns returned")
    
    def test_get_qr_campaigns(self, auth_token):
        """GET /api/qr-campaigns returns QR campaigns"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ QR Campaigns: {len(data)} QR campaigns returned")
    
    def test_get_reminders(self, auth_token):
        """GET /api/reminders returns reminders array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/reminders", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Reminders: {len(data)} reminders returned")


class TestChat:
    """Chat endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_chat_sessions(self, auth_token):
        """GET /api/chat/sessions returns sessions"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/chat/sessions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Chat sessions: {len(data)} sessions returned")
    
    def test_whatsapp_stats(self, auth_token):
        """GET /api/chat/whatsapp-stats returns WA stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/chat/whatsapp-stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "active_conversations_24h" in data
        assert "total_conversations" in data
        print(f"✓ WhatsApp stats: {data['total_conversations']} total conversations")


class TestLoyalty:
    """Loyalty endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_loyalty_sequences(self, auth_token):
        """GET /api/loyalty/sequences returns sequences"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/loyalty/sequences", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Loyalty sequences: {len(data)} sequences returned")
    
    def test_get_loyalty_metrics(self, auth_token):
        """GET /api/loyalty/metrics returns metrics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_enrollments" in data
        assert "active_enrollments" in data
        print(f"✓ Loyalty metrics: {data['total_enrollments']} enrollments")


class TestNotifications:
    """Notifications endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_notifications(self, auth_token):
        """GET /api/notifications returns notifications array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Notifications: {len(data)} notifications returned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
