"""
Test cases for Blocks 9-13:
- Block 9: Loyalty auto-enrollment config
- Block 10: Campaigns CRUD + send
- Block 11: Reminders CRUD + execute
- Block 12: Dashboard advisor stats
- Block 13: AI conversation analysis
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# ========== FIXTURES ==========

@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="session")
def auth_token(api_client):
    """Get authentication token for admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@fakulti.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "token" in data
    return data["token"]

@pytest.fixture(scope="session")
def authenticated_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ========== BLOCK 9: AUTO-ENROLLMENT CONFIG ==========

class TestBlock9AutoEnrollConfig:
    """Block 9: Loyalty auto-enrollment configuration tests"""
    
    def test_get_auto_enroll_config(self, authenticated_client):
        """GET /api/loyalty/auto-enroll-config returns config"""
        response = authenticated_client.get(f"{BASE_URL}/api/loyalty/auto-enroll-config")
        assert response.status_code == 200
        data = response.json()
        # Verify structure
        assert "enabled" in data
        assert "target_stage" in data
        assert "default_sequence_id" in data
        print(f"Auto-enroll config: enabled={data.get('enabled')}, target_stage={data.get('target_stage')}")
    
    def test_post_auto_enroll_config(self, authenticated_client):
        """POST /api/loyalty/auto-enroll-config saves config"""
        config_payload = {
            "enabled": True,
            "target_stage": "cliente_nuevo",
            "default_sequence_id": ""
        }
        response = authenticated_client.post(f"{BASE_URL}/api/loyalty/auto-enroll-config", json=config_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == True
        assert data["target_stage"] == "cliente_nuevo"
        print(f"Auto-enroll config saved: {data}")
        
        # Verify persistence via GET
        get_response = authenticated_client.get(f"{BASE_URL}/api/loyalty/auto-enroll-config")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["enabled"] == True
        assert fetched["target_stage"] == "cliente_nuevo"
        print("Config persistence verified")


# ========== BLOCK 10: CAMPAIGNS ==========

class TestBlock10Campaigns:
    """Block 10: Campaigns CRUD and send tests"""
    
    created_campaign_id = None
    
    def test_get_campaigns_list(self, authenticated_client):
        """GET /api/campaigns returns list"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Campaigns count: {len(data)}")
    
    def test_create_campaign(self, authenticated_client):
        """POST /api/campaigns creates campaign with target_count"""
        campaign_payload = {
            "name": "TEST_Promo Test 2026",
            "description": "Test campaign for testing",
            "campaign_type": "promo",
            "target_stage": "",
            "target_product": "",
            "target_channel": "",
            "target_season": "",
            "message_template": "Hola {nombre}, tenemos una promoción especial para ti.",
            "image_url": "",
            "active": True
        }
        response = authenticated_client.post(f"{BASE_URL}/api/campaigns", json=campaign_payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == "TEST_Promo Test 2026"
        assert "target_count" in data
        assert "sent_count" in data
        assert "status" in data
        assert data["status"] == "draft"
        
        TestBlock10Campaigns.created_campaign_id = data["id"]
        print(f"Campaign created: id={data['id']}, target_count={data['target_count']}")
        
        # Verify persistence
        get_resp = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert get_resp.status_code == 200
        campaigns = get_resp.json()
        found = any(c["id"] == data["id"] for c in campaigns)
        assert found, "Created campaign not found in list"
        print("Campaign persistence verified")
    
    def test_send_campaign(self, authenticated_client):
        """POST /api/campaigns/{id}/send sends campaign (preview mode)"""
        if not TestBlock10Campaigns.created_campaign_id:
            pytest.skip("No campaign created")
        
        campaign_id = TestBlock10Campaigns.created_campaign_id
        response = authenticated_client.post(f"{BASE_URL}/api/campaigns/{campaign_id}/send", json={"batch_size": 5})
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "sent" in data
        assert "failed" in data
        print(f"Campaign send result: sent={data['sent']}, failed={data['failed']}")
    
    def test_delete_campaign(self, authenticated_client):
        """DELETE /api/campaigns/{id} deletes campaign"""
        if not TestBlock10Campaigns.created_campaign_id:
            pytest.skip("No campaign created")
        
        campaign_id = TestBlock10Campaigns.created_campaign_id
        response = authenticated_client.delete(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Campaign deleted: {data['message']}")
        
        # Verify deletion
        get_resp = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert get_resp.status_code == 200
        campaigns = get_resp.json()
        found = any(c["id"] == campaign_id for c in campaigns)
        assert not found, "Campaign still exists after deletion"
        print("Campaign deletion verified")


# ========== BLOCK 11: REMINDERS ==========

class TestBlock11Reminders:
    """Block 11: Reminders CRUD and execute tests"""
    
    created_reminder_id = None
    
    def test_get_reminders_list(self, authenticated_client):
        """GET /api/reminders returns list"""
        response = authenticated_client.get(f"{BASE_URL}/api/reminders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Reminders count: {len(data)}")
    
    def test_create_reminder(self, authenticated_client):
        """POST /api/reminders creates reminder"""
        reminder_payload = {
            "name": "TEST_Reminder Weekly",
            "message_template": "Hola {nombre}, te extrañamos en Fakulti.",
            "target_stage": "",
            "target_product": "",
            "days_since_last_interaction": 7,
            "batch_size": 10,
            "active": True
        }
        response = authenticated_client.post(f"{BASE_URL}/api/reminders", json=reminder_payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == "TEST_Reminder Weekly"
        assert "total_sent" in data
        assert data["total_sent"] == 0
        
        TestBlock11Reminders.created_reminder_id = data["id"]
        print(f"Reminder created: id={data['id']}, name={data['name']}")
        
        # Verify persistence
        get_resp = authenticated_client.get(f"{BASE_URL}/api/reminders")
        assert get_resp.status_code == 200
        reminders = get_resp.json()
        found = any(r["id"] == data["id"] for r in reminders)
        assert found, "Created reminder not found in list"
        print("Reminder persistence verified")
    
    def test_execute_reminder(self, authenticated_client):
        """POST /api/reminders/{id}/execute executes reminder"""
        if not TestBlock11Reminders.created_reminder_id:
            pytest.skip("No reminder created")
        
        reminder_id = TestBlock11Reminders.created_reminder_id
        response = authenticated_client.post(f"{BASE_URL}/api/reminders/{reminder_id}/execute")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "sent" in data
        print(f"Reminder execute result: sent={data['sent']}")
    
    def test_delete_reminder(self, authenticated_client):
        """DELETE /api/reminders/{id} deletes reminder"""
        if not TestBlock11Reminders.created_reminder_id:
            pytest.skip("No reminder created")
        
        reminder_id = TestBlock11Reminders.created_reminder_id
        response = authenticated_client.delete(f"{BASE_URL}/api/reminders/{reminder_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Reminder deleted: {data['message']}")
        
        # Verify deletion
        get_resp = authenticated_client.get(f"{BASE_URL}/api/reminders")
        assert get_resp.status_code == 200
        reminders = get_resp.json()
        found = any(r["id"] == reminder_id for r in reminders)
        assert not found, "Reminder still exists after deletion"
        print("Reminder deletion verified")


# ========== BLOCK 12: DASHBOARD ADVISOR STATS ==========

class TestBlock12AdvisorStats:
    """Block 12: Dashboard advisor stats tests"""
    
    def test_get_advisor_stats(self, authenticated_client):
        """GET /api/dashboard/advisor-stats returns advisors array with metrics and summary"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/advisor-stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "advisors" in data
        assert "summary" in data
        assert isinstance(data["advisors"], list)
        
        # Verify summary fields
        summary = data["summary"]
        assert "total_assigned" in summary
        assert "total_unassigned" in summary
        assert "total_advisors" in summary
        assert "total_revenue_by_advisors" in summary
        
        print(f"Advisor stats: {len(data['advisors'])} advisors")
        print(f"Summary: assigned={summary['total_assigned']}, unassigned={summary['total_unassigned']}, revenue=${summary['total_revenue_by_advisors']}")
        
        # Verify advisor metrics if advisors exist
        if data["advisors"]:
            advisor = data["advisors"][0]
            assert "id" in advisor
            assert "name" in advisor
            assert "total_leads" in advisor
            assert "won_leads" in advisor
            assert "revenue" in advisor
            assert "conversion_rate" in advisor
            print(f"Sample advisor: {advisor['name']} - leads={advisor['total_leads']}, won={advisor['won_leads']}, revenue=${advisor['revenue']}, conversion={advisor['conversion_rate']}%")


# ========== BLOCK 13: AI CONVERSATION ANALYSIS ==========

class TestBlock13AIAnalysis:
    """Block 13: AI conversation analysis tests"""
    
    def test_analyze_conversation_requires_session(self, authenticated_client):
        """POST /api/chat/analyze/{session_id} requires valid session"""
        # Try with invalid session ID
        response = authenticated_client.post(f"{BASE_URL}/api/chat/analyze/invalid_session_123")
        assert response.status_code == 404
        print("Analysis correctly rejects invalid session")
    
    def test_analyze_conversation_with_valid_session(self, authenticated_client):
        """POST /api/chat/analyze/{session_id} returns analysis with valid session"""
        # First, get a valid session from chat/sessions
        sessions_resp = authenticated_client.get(f"{BASE_URL}/api/chat/sessions")
        assert sessions_resp.status_code == 200
        sessions = sessions_resp.json()
        
        if not sessions:
            pytest.skip("No chat sessions available for analysis")
        
        # Find a session with messages (preferably WhatsApp)
        valid_session = None
        for s in sessions:
            if s.get("source") == "whatsapp" or s.get("message_count", 0) > 0:
                valid_session = s["session_id"]
                break
        
        if not valid_session and sessions:
            valid_session = sessions[0]["session_id"]
        
        if not valid_session:
            pytest.skip("No valid sessions with messages")
        
        print(f"Testing analysis with session: {valid_session}")
        
        # Call analyze endpoint - this calls GPT-5.2 via Emergent LLM Key, may take a few seconds
        response = authenticated_client.post(f"{BASE_URL}/api/chat/analyze/{valid_session}", timeout=30)
        
        # Can be 404 if no messages or 200 with analysis
        if response.status_code == 404:
            print("Session has no messages to analyze")
            return
        
        assert response.status_code == 200, f"Analysis failed: {response.text}"
        data = response.json()
        
        # Verify analysis structure
        assert "resumen" in data
        assert "sentimiento" in data
        
        print(f"AI Analysis result:")
        print(f"  - Resumen: {data.get('resumen', 'N/A')[:100]}...")
        print(f"  - Sentimiento: {data.get('sentimiento', 'N/A')}")
        print(f"  - Respuestas sugeridas: {len(data.get('respuestas_sugeridas', []))} suggestions")
        if data.get("respuestas_sugeridas"):
            print(f"    - Sample: {data['respuestas_sugeridas'][0][:80]}...")


# ========== CLEANUP TEST DATA ==========

class TestCleanup:
    """Cleanup test-created data"""
    
    def test_cleanup_test_campaigns(self, authenticated_client):
        """Clean up TEST_ prefixed campaigns"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        if response.status_code == 200:
            campaigns = response.json()
            test_campaigns = [c for c in campaigns if c.get("name", "").startswith("TEST_")]
            for c in test_campaigns:
                authenticated_client.delete(f"{BASE_URL}/api/campaigns/{c['id']}")
            print(f"Cleaned up {len(test_campaigns)} test campaigns")
    
    def test_cleanup_test_reminders(self, authenticated_client):
        """Clean up TEST_ prefixed reminders"""
        response = authenticated_client.get(f"{BASE_URL}/api/reminders")
        if response.status_code == 200:
            reminders = response.json()
            test_reminders = [r for r in reminders if r.get("name", "").startswith("TEST_")]
            for r in test_reminders:
                authenticated_client.delete(f"{BASE_URL}/api/reminders/{r['id']}")
            print(f"Cleaned up {len(test_reminders)} test reminders")
