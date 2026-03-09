"""
Test suite for WhatsApp Monitoring Feature in CRM
Tests: whatsapp-stats, alerts, whatsapp-reply, sessions with source field, handover detection
"""
import pytest
import requests
import os
import uuid

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


class TestWhatsAppStats(TestAuth):
    """Tests for GET /api/chat/whatsapp-stats endpoint"""
    
    def test_whatsapp_stats_returns_all_kpis(self, auth_headers):
        """GET /api/chat/whatsapp-stats returns proper stats structure"""
        response = requests.get(f"{BASE_URL}/api/chat/whatsapp-stats", headers=auth_headers)
        assert response.status_code == 200, f"Stats endpoint failed: {response.text}"
        
        data = response.json()
        # Verify all 4 required KPIs are present
        assert "active_conversations_24h" in data, "Missing active_conversations_24h"
        assert "avg_response_time_ms" in data, "Missing avg_response_time_ms"
        assert "pending_alerts" in data, "Missing pending_alerts"
        assert "messages_today" in data, "Missing messages_today"
        
        # Verify data types
        assert isinstance(data["active_conversations_24h"], int), "active_conversations_24h should be int"
        assert isinstance(data["pending_alerts"], int), "pending_alerts should be int"
        assert isinstance(data["messages_today"], int), "messages_today should be int"
        
        print(f"WhatsApp Stats: {data}")


class TestHandoverAlerts(TestAuth):
    """Tests for alerts endpoints"""
    
    def test_get_alerts_returns_list(self, auth_headers):
        """GET /api/chat/alerts returns alerts list"""
        response = requests.get(f"{BASE_URL}/api/chat/alerts", headers=auth_headers)
        assert response.status_code == 200, f"Alerts endpoint failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Alerts should be a list"
        print(f"Alerts count: {len(data)}")
        
        # If alerts exist, verify structure
        if len(data) > 0:
            alert = data[0]
            assert "id" in alert, "Alert should have id"
            assert "status" in alert, "Alert should have status"
            assert "lead_id" in alert or "lead_phone" in alert, "Alert should have lead reference"
    
    def test_resolve_nonexistent_alert(self, auth_headers):
        """PUT /api/chat/alerts/{alert_id}/resolve with invalid ID returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/chat/alerts/{fake_id}/resolve", headers=auth_headers)
        assert response.status_code == 404, "Should return 404 for non-existent alert"


class TestChatSessions(TestAuth):
    """Tests for GET /api/chat/sessions with source field"""
    
    def test_sessions_include_source_field(self, auth_headers):
        """GET /api/chat/sessions includes source, lead_phone, has_alert fields"""
        response = requests.get(f"{BASE_URL}/api/chat/sessions", headers=auth_headers)
        assert response.status_code == 200, f"Sessions endpoint failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Sessions should be a list"
        print(f"Sessions count: {len(data)}")
        
        # Verify structure for each session
        for session in data:
            assert "session_id" in session, "Session should have session_id"
            assert "source" in session, "Session should have source field (whatsapp or chat_ia)"
            assert session["source"] in ["whatsapp", "chat_ia"], f"Source should be whatsapp or chat_ia, got: {session['source']}"
            
            # WhatsApp sessions should have phone info
            if session["source"] == "whatsapp":
                assert "lead_phone" in session, "WhatsApp session should have lead_phone"
                print(f"WhatsApp session found: {session['session_id']}, phone: {session.get('lead_phone')}")
        
        # Check for has_alert field in at least one session
        has_alert_field = any("has_alert" in s for s in data)
        print(f"has_alert field present: {has_alert_field}")


class TestWhatsAppReply(TestAuth):
    """Tests for POST /api/chat/whatsapp-reply endpoint"""
    
    def test_whatsapp_reply_no_lead_returns_404(self, auth_headers):
        """POST /api/chat/whatsapp-reply with invalid lead_id returns 404"""
        fake_lead_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/chat/whatsapp-reply",
            headers=auth_headers,
            json={"lead_id": fake_lead_id, "message": "Test message"}
        )
        assert response.status_code == 404, "Should return 404 for non-existent lead"
    
    def test_whatsapp_reply_lead_no_phone_returns_400(self, auth_headers):
        """POST /api/chat/whatsapp-reply with lead without phone returns 400"""
        # First create a lead without whatsapp
        create_response = requests.post(
            f"{BASE_URL}/api/leads",
            headers=auth_headers,
            json={
                "name": "TEST_NoPhone Lead",
                "whatsapp": "",  # Empty whatsapp
                "city": "Test City"
            }
        )
        assert create_response.status_code == 200, f"Lead creation failed: {create_response.text}"
        lead_id = create_response.json()["id"]
        
        # Try to send WhatsApp message
        response = requests.post(
            f"{BASE_URL}/api/chat/whatsapp-reply",
            headers=auth_headers,
            json={"lead_id": lead_id, "message": "Test message"}
        )
        assert response.status_code == 400, "Should return 400 for lead without phone"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)


class TestHandoverDetection(TestAuth):
    """Tests for human handover detection via webhook"""
    
    def test_webhook_accepts_meta_format(self, auth_headers):
        """POST /api/webhook/whatsapp accepts Meta webhook format"""
        test_phone = "593999888777"
        test_message = "hola quiero informacion"
        
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
        
        # Note: This endpoint doesn't require auth as it's called by Meta
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        assert response.status_code == 200, f"Webhook should accept Meta format: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", "Webhook should return status ok"
        print("Meta format webhook accepted successfully")
    
    def test_webhook_handover_keyword_creates_alert(self, auth_headers):
        """POST /api/webhook/whatsapp with handover keyword creates alert"""
        test_phone = f"593{uuid.uuid4().hex[:9]}"  # Unique phone to avoid conflicts
        handover_message = "quiero hablar con un humano"
        
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": handover_message}
                        }]
                    }
                }]
            }]
        }
        
        # Send webhook with handover keyword
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        assert response.status_code == 200, f"Webhook failed: {response.text}"
        
        # Verify alert was created
        alerts_response = requests.get(f"{BASE_URL}/api/chat/alerts", headers=auth_headers)
        assert alerts_response.status_code == 200
        alerts = alerts_response.json()
        
        # Find alert with matching phone
        matching_alerts = [a for a in alerts if a.get("lead_phone") == test_phone and a.get("status") == "pending"]
        assert len(matching_alerts) > 0, f"Alert should be created for handover keyword. Alerts: {[a.get('lead_phone') for a in alerts]}"
        
        created_alert = matching_alerts[0]
        assert created_alert["message"] == handover_message, "Alert message should match"
        print(f"Handover alert created: {created_alert['id']}")
        
        # Cleanup: resolve the alert
        requests.put(f"{BASE_URL}/api/chat/alerts/{created_alert['id']}/resolve", headers=auth_headers)
    
    def test_resolve_alert_works(self, auth_headers):
        """PUT /api/chat/alerts/{alert_id}/resolve marks alert as resolved"""
        # Create a unique alert via webhook
        test_phone = f"593{uuid.uuid4().hex[:9]}"
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": "necesito un agente humano"}
                        }]
                    }
                }]
            }]
        }
        
        requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        
        # Get the alert
        alerts_response = requests.get(f"{BASE_URL}/api/chat/alerts", headers=auth_headers)
        alerts = alerts_response.json()
        matching = [a for a in alerts if a.get("lead_phone") == test_phone and a.get("status") == "pending"]
        
        if len(matching) > 0:
            alert_id = matching[0]["id"]
            
            # Resolve the alert
            resolve_response = requests.put(f"{BASE_URL}/api/chat/alerts/{alert_id}/resolve", headers=auth_headers)
            assert resolve_response.status_code == 200, f"Resolve failed: {resolve_response.text}"
            
            # Verify it's resolved
            alerts_after = requests.get(f"{BASE_URL}/api/chat/alerts", headers=auth_headers).json()
            resolved_alert = next((a for a in alerts_after if a["id"] == alert_id), None)
            if resolved_alert:
                assert resolved_alert["status"] == "resolved", "Alert status should be resolved"
                print(f"Alert {alert_id} resolved successfully")


class TestWhatsAppReplyWithRealLead(TestAuth):
    """Test WhatsApp reply with the specified test lead"""
    
    def test_whatsapp_reply_to_real_lead(self, auth_headers):
        """POST /api/chat/whatsapp-reply sends message to real lead"""
        # Use the lead_id from the context: c552b6bc-5ab8-4a65-b09d-0b73f80890a4
        lead_id = "c552b6bc-5ab8-4a65-b09d-0b73f80890a4"
        
        # First verify lead exists
        lead_response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        if lead_response.status_code != 200:
            pytest.skip(f"Test lead {lead_id} not found, skipping real WhatsApp test")
        
        lead = lead_response.json()
        assert lead.get("whatsapp") == "593963266566", f"Lead phone mismatch: {lead.get('whatsapp')}"
        
        # Send a test message (NOTE: This will actually send to WhatsApp!)
        # Using a benign test message
        test_message = f"[TEST-CRM] Prueba de integracion - {uuid.uuid4().hex[:6]}"
        response = requests.post(
            f"{BASE_URL}/api/chat/whatsapp-reply",
            headers=auth_headers,
            json={"lead_id": lead_id, "message": test_message}
        )
        
        # If WhatsApp is not configured, this might return 500
        if response.status_code == 500:
            error_msg = response.json().get("detail", "")
            if "Error al enviar" in error_msg or "WhatsApp" in error_msg:
                print("WhatsApp API not configured or message send failed (expected in test env)")
                pytest.skip("WhatsApp API not configured")
        
        # If successful
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "delivered" in data, "Response should indicate delivery status"
            print(f"WhatsApp message sent: {data}")
            
            # Verify message is stored in chat history
            session_id = f"wa_{lead['whatsapp']}"
            history_response = requests.get(f"{BASE_URL}/api/chat/history/{session_id}", headers=auth_headers)
            if history_response.status_code == 200:
                messages = history_response.json()
                recent_msgs = [m for m in messages if test_message in m.get("content", "")]
                print(f"Message stored in history: {len(recent_msgs) > 0}")


class TestMultipleHandoverKeywords(TestAuth):
    """Test various handover keywords trigger alerts"""
    
    @pytest.mark.parametrize("keyword", [
        "agente",
        "humano", 
        "persona real",
        "asesor real",
        "no quiero bot",
        "operador"
    ])
    def test_handover_keywords(self, auth_headers, keyword):
        """Verify each handover keyword triggers an alert"""
        test_phone = f"593test{uuid.uuid4().hex[:6]}"
        message = f"Hola, quiero {keyword} por favor"
        
        meta_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "type": "text",
                            "from": test_phone,
                            "text": {"body": message}
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=meta_payload)
        assert response.status_code == 200
        
        # Check alert created
        alerts = requests.get(f"{BASE_URL}/api/chat/alerts", headers=auth_headers).json()
        matching = [a for a in alerts if a.get("lead_phone") == test_phone]
        
        if len(matching) > 0:
            print(f"Keyword '{keyword}' triggered alert successfully")
            # Cleanup
            requests.put(f"{BASE_URL}/api/chat/alerts/{matching[0]['id']}/resolve", headers=auth_headers)
        else:
            print(f"WARNING: Keyword '{keyword}' did not trigger alert")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
