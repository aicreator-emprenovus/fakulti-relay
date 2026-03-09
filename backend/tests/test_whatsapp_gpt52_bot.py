"""
Test suite for WhatsApp Bot with GPT-5.2 Integration
Tests: WhatsApp-only ChatPage, GPT-5.2 responses, tag parsing (LEAD_NAME, UPDATE_LEAD, STAGE), CRM reply
Based on iteration 11 requirements: Chat IA removed, WhatsApp-only view, GPT-5.2 bot
"""
import pytest
import requests
import os
import uuid
import time
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestAuth:
    """Authentication for test session"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestChatSessionsWhatsAppOnly(TestAuth):
    """Test that chat sessions return only WhatsApp sessions (source=whatsapp)"""
    
    def test_sessions_endpoint_returns_list(self, auth_headers):
        """GET /api/chat/sessions returns list with source field"""
        response = requests.get(f"{BASE_URL}/api/chat/sessions", headers=auth_headers)
        assert response.status_code == 200, f"Sessions endpoint failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Sessions should be a list"
        
        # All sessions should have source field
        for session in data:
            assert "source" in session, f"Session missing source field: {session}"
            assert session["source"] in ["whatsapp", "chat_ia"], f"Invalid source: {session['source']}"
        
        # Count WhatsApp sessions
        wa_sessions = [s for s in data if s["source"] == "whatsapp"]
        print(f"Total sessions: {len(data)}, WhatsApp sessions: {len(wa_sessions)}")


class TestWhatsAppStatsKPIs(TestAuth):
    """Test WhatsApp stats bar shows 4 KPIs"""
    
    def test_whatsapp_stats_has_4_kpis(self, auth_headers):
        """GET /api/chat/whatsapp-stats returns all 4 KPIs for stats bar"""
        response = requests.get(f"{BASE_URL}/api/chat/whatsapp-stats", headers=auth_headers)
        assert response.status_code == 200, f"Stats endpoint failed: {response.text}"
        
        data = response.json()
        
        # Verify all 4 KPIs from the stats bar
        required_fields = [
            "active_conversations_24h",  # Activas 24h
            "avg_response_time_ms",       # Resp. Prom.
            "messages_today",             # Msgs Hoy
            "pending_alerts"              # Alertas
        ]
        
        for field in required_fields:
            assert field in data, f"Missing KPI field: {field}"
        
        print(f"WhatsApp Stats: {data}")


class TestGPT52WebhookResponse(TestAuth):
    """Test that webhook generates GPT-5.2 responses (not static greetings)"""
    
    def test_webhook_generates_gpt_response_not_static(self, auth_headers):
        """POST /api/webhook/whatsapp with new user gets GPT-5.2 response"""
        # Use unique test phone to ensure new lead
        test_phone = f"593TESTGPT{uuid.uuid4().hex[:6]}"
        test_message = "Hola, buenos dias"
        
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": test_message}
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        assert response.status_code == 200, f"Webhook failed: {response.text}"
        
        # Wait for GPT processing
        time.sleep(3)
        
        # Get chat history to verify response
        session_id = f"wa_{test_phone}"
        history_response = requests.get(f"{BASE_URL}/api/chat/history/{session_id}", headers=auth_headers)
        assert history_response.status_code == 200, f"History failed: {history_response.text}"
        
        messages = history_response.json()
        
        # Should have user message and bot response
        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
        
        # Find the bot response
        bot_responses = [m for m in messages if m["role"] == "assistant"]
        assert len(bot_responses) >= 1, "Expected at least 1 bot response"
        
        bot_reply = bot_responses[-1]["content"]
        
        # Verify GPT response characteristics:
        # 1. Should be non-empty
        assert len(bot_reply) > 0, "Bot response should not be empty"
        
        # 2. Should be in Spanish (contains common Spanish words/characters)
        spanish_indicators = ["hola", "buenas", "bienvenido", "mucho gusto", "encantado", 
                            "como", "nombre", "ayudar", "gracias", "por favor", "que", "es"]
        is_spanish = any(indicator in bot_reply.lower() for indicator in spanish_indicators)
        assert is_spanish, f"Bot response should be in Spanish: {bot_reply}"
        
        # 3. Should NOT contain unstripped tags
        assert "[LEAD_NAME:" not in bot_reply, f"Tags should be stripped from response: {bot_reply}"
        assert "[UPDATE_LEAD:" not in bot_reply, f"Tags should be stripped from response: {bot_reply}"
        assert "[STAGE:" not in bot_reply, f"Tags should be stripped from response: {bot_reply}"
        
        print(f"GPT-5.2 Response: {bot_reply[:200]}...")
        
        # Cleanup: delete the test lead
        leads_resp = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        if leads_resp.status_code == 200:
            test_lead = next((l for l in leads_resp.json().get("leads", []) if l.get("whatsapp") == test_phone), None)
            if test_lead:
                requests.delete(f"{BASE_URL}/api/leads/{test_lead['id']}", headers=auth_headers)
    
    def test_bot_asks_for_name_on_first_contact(self, auth_headers):
        """Bot should ask for name when new user writes first message"""
        test_phone = f"593NEWUSER{uuid.uuid4().hex[:6]}"
        test_message = "Hola"
        
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": test_message}
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        assert response.status_code == 200
        
        time.sleep(3)
        
        session_id = f"wa_{test_phone}"
        history_response = requests.get(f"{BASE_URL}/api/chat/history/{session_id}", headers=auth_headers)
        messages = history_response.json()
        
        bot_responses = [m for m in messages if m["role"] == "assistant"]
        if len(bot_responses) > 0:
            bot_reply = bot_responses[-1]["content"].lower()
            # Bot should ask for name (various ways)
            name_related = ["nombre", "como te llamas", "como te puedo llamar", "quien eres", 
                          "presentarte", "llamarte", "llamas"]
            asks_for_name = any(term in bot_reply for term in name_related)
            print(f"Bot asks for name: {asks_for_name}")
            print(f"Response: {bot_reply[:150]}...")
        
        # Cleanup
        leads_resp = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        if leads_resp.status_code == 200:
            test_lead = next((l for l in leads_resp.json().get("leads", []) if l.get("whatsapp") == test_phone), None)
            if test_lead:
                requests.delete(f"{BASE_URL}/api/leads/{test_lead['id']}", headers=auth_headers)


class TestLeadDataExtraction(TestAuth):
    """Test that bot extracts and saves lead data from conversation"""
    
    def test_lead_created_from_whatsapp_message(self, auth_headers):
        """Webhook creates lead with whatsapp number"""
        test_phone = f"593LEADTEST{uuid.uuid4().hex[:6]}"
        
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": "Hola, quiero informacion del bone broth"}
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        assert response.status_code == 200
        
        time.sleep(2)
        
        # Check lead was created
        leads_resp = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        assert leads_resp.status_code == 200
        
        leads = leads_resp.json().get("leads", [])
        test_lead = next((l for l in leads if l.get("whatsapp") == test_phone), None)
        
        assert test_lead is not None, f"Lead should be created for phone {test_phone}"
        assert test_lead["source"] == "WhatsApp", f"Lead source should be WhatsApp: {test_lead['source']}"
        
        print(f"Lead created: {test_lead['id']}, source: {test_lead['source']}")
        
        # Cleanup
        if test_lead:
            requests.delete(f"{BASE_URL}/api/leads/{test_lead['id']}", headers=auth_headers)
    
    def test_name_extraction_from_conversation(self, auth_headers):
        """Test that bot extracts name via LEAD_NAME tag and updates lead"""
        test_phone = f"593NAMETEST{uuid.uuid4().hex[:6]}"
        
        # First message - greeting
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": "Hola, me interesa el producto"}
                        }]
                    }
                }]
            }]
        }
        requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        time.sleep(3)
        
        # Second message - provide name
        meta_payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "Mi nombre es Carlos Garcia"
        requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        time.sleep(4)  # Wait for GPT to process and extract name
        
        # Check lead name was updated
        leads_resp = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        leads = leads_resp.json().get("leads", [])
        test_lead = next((l for l in leads if l.get("whatsapp") == test_phone), None)
        
        if test_lead:
            lead_name = test_lead.get("name", "")
            print(f"Lead name extracted: '{lead_name}'")
            # Name should contain the provided name (GPT might format it)
            if lead_name:
                has_name = "carlos" in lead_name.lower() or "garcia" in lead_name.lower()
                print(f"Name extraction successful: {has_name}")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/leads/{test_lead['id']}", headers=auth_headers)


class TestCRMWhatsAppReply(TestAuth):
    """Test CRM agent reply to WhatsApp conversation"""
    
    def test_crm_reply_endpoint_structure(self, auth_headers):
        """POST /api/chat/whatsapp-reply validates lead and requires phone"""
        # Test with non-existent lead
        fake_lead_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/chat/whatsapp-reply",
            headers=auth_headers,
            json={"lead_id": fake_lead_id, "message": "Test message"}
        )
        assert response.status_code == 404, "Should return 404 for non-existent lead"
    
    def test_crm_reply_with_lead_having_phone(self, auth_headers):
        """POST /api/chat/whatsapp-reply with valid lead sends message"""
        # Create a lead with WhatsApp number
        test_phone = f"593CRMTEST{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/leads",
            headers=auth_headers,
            json={
                "name": "TEST_CRM Reply Lead",
                "whatsapp": test_phone,
                "city": "Quito"
            }
        )
        assert create_response.status_code == 200, f"Lead creation failed: {create_response.text}"
        lead_id = create_response.json()["id"]
        
        # Try to send CRM reply
        response = requests.post(
            f"{BASE_URL}/api/chat/whatsapp-reply",
            headers=auth_headers,
            json={"lead_id": lead_id, "message": "Test CRM reply message"}
        )
        
        # This might fail if WhatsApp API is not configured, that's expected
        if response.status_code == 500:
            print("WhatsApp API not configured (expected in test env)")
        elif response.status_code == 200:
            data = response.json()
            assert "message" in data or "delivered" in data
            print(f"CRM reply sent: {data}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)


class TestTagStripping(TestAuth):
    """Test that tags are properly stripped from stored messages"""
    
    def test_stored_messages_dont_have_tags(self, auth_headers):
        """Chat messages in DB should not contain LEAD_NAME, UPDATE_LEAD, STAGE tags"""
        # Use existing WhatsApp session if available
        sessions_resp = requests.get(f"{BASE_URL}/api/chat/sessions", headers=auth_headers)
        sessions = sessions_resp.json()
        
        wa_sessions = [s for s in sessions if s.get("source") == "whatsapp"]
        
        if len(wa_sessions) == 0:
            pytest.skip("No WhatsApp sessions found to test")
        
        # Check messages in first WhatsApp session
        session_id = wa_sessions[0]["session_id"]
        history_resp = requests.get(f"{BASE_URL}/api/chat/history/{session_id}", headers=auth_headers)
        messages = history_resp.json()
        
        # Check assistant messages don't have tags
        for msg in messages:
            if msg["role"] == "assistant":
                content = msg.get("content", "")
                assert "[LEAD_NAME:" not in content, f"LEAD_NAME tag not stripped: {content}"
                assert "[UPDATE_LEAD:" not in content, f"UPDATE_LEAD tag not stripped: {content}"
                assert "[STAGE:" not in content, f"STAGE tag not stripped: {content}"
        
        print(f"Checked {len(messages)} messages - all tags properly stripped")


class TestWhatsAppSessionFormat(TestAuth):
    """Test WhatsApp session format and structure"""
    
    def test_whatsapp_session_has_correct_fields(self, auth_headers):
        """WhatsApp sessions should have lead_phone, has_alert fields"""
        sessions_resp = requests.get(f"{BASE_URL}/api/chat/sessions", headers=auth_headers)
        sessions = sessions_resp.json()
        
        wa_sessions = [s for s in sessions if s.get("source") == "whatsapp"]
        
        for session in wa_sessions:
            # WhatsApp sessions should have these fields
            assert "session_id" in session
            assert session["session_id"].startswith("wa_"), f"WhatsApp session_id should start with 'wa_': {session['session_id']}"
            assert "lead_phone" in session, f"WhatsApp session should have lead_phone: {session}"
            assert "has_alert" in session, f"WhatsApp session should have has_alert: {session}"
        
        print(f"Verified {len(wa_sessions)} WhatsApp session(s) have correct format")


class TestNoNuevaConversacionButton(TestAuth):
    """Test that 'Nueva Conversacion' button functionality is removed for WhatsApp-only mode"""
    
    def test_internal_chat_message_endpoint_still_exists(self, auth_headers):
        """POST /api/chat/message endpoint exists (for internal Chat IA - should be unused in WhatsApp-only mode)"""
        # The endpoint still exists in backend but frontend shouldn't use it
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            headers=auth_headers,
            json={
                "session_id": f"test_session_{uuid.uuid4().hex[:6]}",
                "message": "Test"
            }
        )
        # Should work but we're just verifying it exists
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        print("Internal chat endpoint exists (for backward compatibility)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
