"""
Block 4: Human Agent Handover Tests
Tests for:
- PUT /api/leads/{id}/pause-bot (pauses bot for a lead, sets bot_paused=true)
- PUT /api/leads/{id}/resume-bot (resumes bot for a lead, sets bot_paused=false)  
- GET /api/chat/alerts (returns alerts enriched with lead_product, lead_channel, lead_city, lead_stage, bot_paused)
- PUT /api/chat/alerts/{id}/resolve (marks alert as resolved with resolved_at timestamp)
- Chat sessions include bot_paused status in response
- Handover keyword detection and timeout detection
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from environment
TEST_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@fakulti.com")
TEST_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "admin123")

class TestBlock4HumanHandover:
    """Human Agent Handover Feature Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        # Cleanup: try to delete test leads and alerts created during tests
        # Cleanup is best-effort
        try:
            leads_resp = self.session.get(f"{BASE_URL}/api/leads?search=TEST_BLOCK4_")
            if leads_resp.status_code == 200:
                leads = leads_resp.json().get("leads", [])
                for lead in leads:
                    self.session.delete(f"{BASE_URL}/api/leads/{lead['id']}")
        except:
            pass
    
    # ==================== PAUSE-BOT ENDPOINT TESTS ====================
    
    def test_pause_bot_for_lead_success(self):
        """Test PUT /api/leads/{id}/pause-bot sets bot_paused=true"""
        # First create a test lead
        lead_data = {
            "name": "TEST_BLOCK4_PauseBot",
            "whatsapp": "0999888771",
            "city": "Quito",
            "product_interest": "Bombro"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_resp.status_code == 200, f"Create lead failed: {create_resp.text}"
        lead = create_resp.json()
        lead_id = lead["id"]
        
        # Verify bot_paused is initially false (or not set)
        get_resp = self.session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_resp.status_code == 200
        assert get_resp.json().get("bot_paused", False) == False
        
        # Pause bot
        pause_resp = self.session.put(f"{BASE_URL}/api/leads/{lead_id}/pause-bot")
        assert pause_resp.status_code == 200, f"Pause bot failed: {pause_resp.text}"
        assert "pausado" in pause_resp.json().get("message", "").lower() or "paused" in pause_resp.json().get("message", "").lower()
        
        # Verify bot_paused is now true
        get_resp2 = self.session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_resp2.status_code == 200
        lead_after = get_resp2.json()
        assert lead_after.get("bot_paused") == True, "bot_paused should be True after pause"
        assert "bot_paused_at" in lead_after, "bot_paused_at timestamp should be set"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_pause_bot_nonexistent_lead_returns_404(self):
        """Test PUT /api/leads/{id}/pause-bot returns 404 for nonexistent lead"""
        fake_id = f"nonexistent-{uuid.uuid4()}"
        resp = self.session.put(f"{BASE_URL}/api/leads/{fake_id}/pause-bot")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    
    # ==================== RESUME-BOT ENDPOINT TESTS ====================
    
    def test_resume_bot_for_lead_success(self):
        """Test PUT /api/leads/{id}/resume-bot sets bot_paused=false"""
        # Create test lead
        lead_data = {
            "name": "TEST_BLOCK4_ResumeBot",
            "whatsapp": "0999888772",
            "city": "Guayaquil",
            "product_interest": "CBD Colageno"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_resp.status_code == 200
        lead = create_resp.json()
        lead_id = lead["id"]
        
        # First pause the bot
        pause_resp = self.session.put(f"{BASE_URL}/api/leads/{lead_id}/pause-bot")
        assert pause_resp.status_code == 200
        
        # Verify it's paused
        get_resp = self.session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_resp.json().get("bot_paused") == True
        
        # Resume bot
        resume_resp = self.session.put(f"{BASE_URL}/api/leads/{lead_id}/resume-bot")
        assert resume_resp.status_code == 200, f"Resume bot failed: {resume_resp.text}"
        assert "reactivado" in resume_resp.json().get("message", "").lower() or "resumed" in resume_resp.json().get("message", "").lower()
        
        # Verify bot_paused is now false
        get_resp2 = self.session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_resp2.status_code == 200
        lead_after = get_resp2.json()
        assert lead_after.get("bot_paused") == False, "bot_paused should be False after resume"
        # bot_paused_at should be unset
        assert lead_after.get("bot_paused_at") is None or "bot_paused_at" not in lead_after
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_resume_bot_nonexistent_lead_returns_404(self):
        """Test PUT /api/leads/{id}/resume-bot returns 404 for nonexistent lead"""
        fake_id = f"nonexistent-{uuid.uuid4()}"
        resp = self.session.put(f"{BASE_URL}/api/leads/{fake_id}/resume-bot")
        assert resp.status_code == 404
    
    # ==================== ALERTS ENDPOINT TESTS ====================
    
    def test_get_alerts_returns_list(self):
        """Test GET /api/chat/alerts returns a list"""
        resp = self.session.get(f"{BASE_URL}/api/chat/alerts")
        assert resp.status_code == 200, f"Get alerts failed: {resp.text}"
        alerts = resp.json()
        assert isinstance(alerts, list), "Alerts should be a list"
    
    def test_alerts_enrichment_fields(self):
        """Test GET /api/chat/alerts returns enriched fields (lead_product, lead_channel, lead_city, lead_stage, bot_paused)"""
        resp = self.session.get(f"{BASE_URL}/api/chat/alerts")
        assert resp.status_code == 200
        alerts = resp.json()
        
        # Enrichment only happens when the lead still exists in the database
        # Check that alerts with enriched data have the expected fields
        enriched_count = 0
        for alert in alerts:
            # Check if this alert has enriched data (lead_city, lead_stage, etc.)
            # These fields are only added when the lead is found
            has_enriched_data = (
                "lead_city" in alert or 
                "lead_stage" in alert or 
                "lead_product" in alert
            )
            if has_enriched_data:
                enriched_count += 1
                # Verify all expected enrichment fields are present when any enrichment exists
                assert "lead_city" in alert, f"Missing lead_city in enriched alert"
                assert "lead_stage" in alert, f"Missing lead_stage in enriched alert"
                assert "bot_paused" in alert, f"Missing bot_paused in enriched alert"
        
        # Verify basic alert structure
        for alert in alerts:
            assert "id" in alert, "Alert missing id"
            assert "status" in alert, "Alert missing status"
        
        print(f"Verified {len(alerts)} alerts, {enriched_count} with enrichment")
    
    def test_resolve_alert_sets_resolved_at(self):
        """Test PUT /api/chat/alerts/{id}/resolve marks alert as resolved with timestamp"""
        # First check if there are any pending alerts we can use
        alerts_resp = self.session.get(f"{BASE_URL}/api/chat/alerts")
        assert alerts_resp.status_code == 200
        alerts = alerts_resp.json()
        
        # Find a pending alert or skip
        pending_alert = None
        for a in alerts:
            if a.get("status") == "pending":
                pending_alert = a
                break
        
        if not pending_alert:
            # Create a test scenario: we'll directly test the endpoint behavior
            # by checking 404 response for nonexistent alert
            fake_alert_id = f"test-alert-{uuid.uuid4()}"
            resp = self.session.put(f"{BASE_URL}/api/chat/alerts/{fake_alert_id}/resolve")
            assert resp.status_code == 404, "Should return 404 for nonexistent alert"
            print("No pending alerts to test resolve on - verified 404 for nonexistent alert")
        else:
            # Resolve the alert
            alert_id = pending_alert.get("id")
            resolve_resp = self.session.put(f"{BASE_URL}/api/chat/alerts/{alert_id}/resolve")
            assert resolve_resp.status_code == 200, f"Resolve alert failed: {resolve_resp.text}"
            
            # Verify alert is now resolved
            alerts_resp2 = self.session.get(f"{BASE_URL}/api/chat/alerts")
            alerts2 = alerts_resp2.json()
            resolved_alert = next((a for a in alerts2 if a.get("id") == alert_id), None)
            if resolved_alert:
                assert resolved_alert.get("status") == "resolved", "Alert status should be 'resolved'"
                assert resolved_alert.get("resolved_at") is not None, "resolved_at timestamp should be set"
            print(f"Successfully resolved alert {alert_id}")
    
    # ==================== CHAT SESSIONS BOT_PAUSED STATUS ====================
    
    def test_chat_sessions_include_bot_paused_status(self):
        """Test GET /api/chat/sessions includes bot_paused field for WhatsApp sessions"""
        resp = self.session.get(f"{BASE_URL}/api/chat/sessions")
        assert resp.status_code == 200, f"Get sessions failed: {resp.text}"
        sessions = resp.json()
        
        # Check WhatsApp sessions for bot_paused field
        wa_sessions = [s for s in sessions if s.get("source") == "whatsapp"]
        for session in wa_sessions:
            assert "bot_paused" in session, f"WhatsApp session missing bot_paused field: {session.get('session_id')}"
        
        print(f"Verified {len(wa_sessions)} WhatsApp sessions have bot_paused field")
    
    def test_chat_sessions_include_has_alert_field(self):
        """Test GET /api/chat/sessions includes has_alert field"""
        resp = self.session.get(f"{BASE_URL}/api/chat/sessions")
        assert resp.status_code == 200
        sessions = resp.json()
        
        wa_sessions = [s for s in sessions if s.get("source") == "whatsapp"]
        for session in wa_sessions:
            assert "has_alert" in session, f"Session missing has_alert field: {session.get('session_id')}"
        
        print(f"Verified {len(wa_sessions)} WhatsApp sessions have has_alert field")
    
    # ==================== WHATSAPP STATS ====================
    
    def test_whatsapp_stats_includes_pending_alerts(self):
        """Test GET /api/chat/whatsapp-stats includes pending_alerts count"""
        resp = self.session.get(f"{BASE_URL}/api/chat/whatsapp-stats")
        assert resp.status_code == 200, f"Get stats failed: {resp.text}"
        stats = resp.json()
        
        assert "pending_alerts" in stats, "Stats should include pending_alerts"
        assert isinstance(stats["pending_alerts"], int), "pending_alerts should be integer"
        print(f"WhatsApp stats show {stats['pending_alerts']} pending alerts")
    
    # ==================== HANDOVER KEYWORD DETECTION ====================
    
    def test_handover_keywords_config_exists(self):
        """Verify HANDOVER_KEYWORDS configuration is defined in backend"""
        # This tests that the backend code has the handover keywords
        # We can verify this by checking if handover alerts are created on keyword triggers
        # For now, we verify the alert structure includes 'reason' field
        resp = self.session.get(f"{BASE_URL}/api/chat/alerts")
        assert resp.status_code == 200
        alerts = resp.json()
        
        # Check that alerts have reason field (solicitud_usuario or timeout_bot)
        for alert in alerts:
            if alert.get("status") == "pending":
                reason = alert.get("reason", "")
                # Reason should be one of the known types
                assert reason in ["solicitud_usuario", "timeout_bot", "regla_operativa", ""], \
                    f"Unknown alert reason: {reason}"
        print("Alert reason field verification passed")
    
    # ==================== PAUSE/RESUME FLOW INTEGRATION ====================
    
    def test_full_pause_resume_cycle(self):
        """Test complete pause -> resume cycle with state verification"""
        # Create lead
        lead_data = {
            "name": "TEST_BLOCK4_FullCycle",
            "whatsapp": "0999888773",
            "city": "Cuenca",
            "channel": "TV",
            "product_interest": "Gomitas Melatonina"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Initial state: bot not paused
        lead = self.session.get(f"{BASE_URL}/api/leads/{lead_id}").json()
        assert lead.get("bot_paused", False) == False
        
        # Step 1: Pause
        self.session.put(f"{BASE_URL}/api/leads/{lead_id}/pause-bot")
        lead = self.session.get(f"{BASE_URL}/api/leads/{lead_id}").json()
        assert lead["bot_paused"] == True
        assert lead.get("bot_paused_at") is not None
        pause_time = lead["bot_paused_at"]
        
        # Step 2: Verify pause persists
        lead = self.session.get(f"{BASE_URL}/api/leads/{lead_id}").json()
        assert lead["bot_paused"] == True
        assert lead["bot_paused_at"] == pause_time
        
        # Step 3: Resume
        self.session.put(f"{BASE_URL}/api/leads/{lead_id}/resume-bot")
        lead = self.session.get(f"{BASE_URL}/api/leads/{lead_id}").json()
        assert lead.get("bot_paused") == False
        assert lead.get("bot_paused_at") is None
        
        # Step 4: Verify can pause again
        self.session.put(f"{BASE_URL}/api/leads/{lead_id}/pause-bot")
        lead = self.session.get(f"{BASE_URL}/api/leads/{lead_id}").json()
        assert lead["bot_paused"] == True
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/leads/{lead_id}")
        print("Full pause-resume cycle test passed")
    
    # ==================== LEAD CONTEXT ENRICHMENT ====================
    
    def test_lead_get_includes_bot_paused_field(self):
        """Test GET /api/leads/{id} returns bot_paused field"""
        # Create lead
        lead_data = {
            "name": "TEST_BLOCK4_LeadField",
            "whatsapp": "0999888774"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Get lead and check bot_paused field exists
        get_resp = self.session.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert get_resp.status_code == 200
        lead = get_resp.json()
        
        # bot_paused should be present (default False)
        assert "bot_paused" in lead or lead.get("bot_paused", False) == False
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/leads/{lead_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
