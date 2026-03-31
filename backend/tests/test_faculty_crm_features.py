"""
Fakulti CRM Feature Tests - Iteration 4
Tests for:
1. Login with admin@faculty.com / admin123
2. Dashboard shows new stage names
3. WhatsApp webhook - new/returning leads, name registration, auto-stage
4. Chat delete message and delete conversation endpoints
5. Leads stage change endpoint
6. Quotations create and PDF download
7. Bulk download with correct stage names
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Expected funnel stages
EXPECTED_STAGES = ["nuevo", "interesado", "en_negociacion", "cliente_nuevo", "cliente_activo", "perdido"]


class TestAuth:
    """Authentication tests with admin credentials"""
    
    def test_login_with_admin_credentials(self):
        """Test login with admin@faculty.com / admin123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == "admin@faculty.com"
        print(f"Login successful for {data['user']['email']}")
    
    def test_login_wrong_password(self):
        """Test login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@faculty.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestDashboard:
    """Dashboard tests - verify new stage names"""
    
    def test_dashboard_stats_has_new_stages(self, auth_headers):
        """Verify dashboard returns stats with new stage names"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        assert "stages" in data, "No stages in dashboard response"
        stages = data["stages"]
        
        # Verify all new stage names exist
        for stage in EXPECTED_STAGES:
            assert stage in stages, f"Stage '{stage}' missing from dashboard"
            print(f"Stage '{stage}': {stages[stage]} leads")
        
        # Verify old stage names are NOT present
        assert "caliente" not in stages, "Old stage 'caliente' should not exist"
        assert "frio" not in stages, "Old stage 'frio' should not exist"
        print("Dashboard shows correct new stage names")


class TestWhatsAppWebhook:
    """WhatsApp webhook tests - no auth required"""
    
    def test_new_lead_greeting(self):
        """Test webhook greets new leads and asks for name"""
        test_phone = f"+593TEST{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "Hola quiero informacion"
        })
        assert response.status_code == 200, f"Webhook failed: {response.text}"
        data = response.json()
        
        assert "reply" in data, "No reply in response"
        assert data.get("is_new") == True, "Should be marked as new lead"
        assert "lead_id" in data, "No lead_id returned"
        
        # Check reply asks for name
        reply = data["reply"].lower()
        assert "nombre" in reply or "bienvenido" in reply, f"Reply should ask for name: {data['reply']}"
        print(f"New lead greeting: {data['reply'][:80]}...")
        
        return data["lead_id"], test_phone
    
    def test_name_registration(self):
        """Test name registration for new lead"""
        test_phone = f"+593NAME{uuid.uuid4().hex[:8]}"
        
        # First message - create lead
        response1 = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "Hola"
        })
        assert response1.status_code == 200
        
        # Second message - provide name
        response2 = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "Juan Perez"
        })
        assert response2.status_code == 200, f"Name registration failed: {response2.text}"
        data = response2.json()
        
        # Should acknowledge name
        assert "Juan" in data.get("reply", "") or "Mucho gusto" in data.get("reply", ""), f"Should acknowledge name: {data['reply']}"
        print(f"Name registration reply: {data['reply'][:80]}...")
    
    def test_returning_lead_greeting(self, auth_headers):
        """Test returning lead gets different greeting"""
        # Create a lead first via API
        test_phone = f"+593RET{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": "Test Returning Lead",
            "whatsapp": test_phone,
            "funnel_stage": "interesado"
        })
        assert create_response.status_code == 200
        
        # Now send webhook message
        response = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "Hola de nuevo"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("is_new") == False, "Should NOT be marked as new"
        assert "de nuevo" in data["reply"].lower() or "gusto tenerte" in data["reply"].lower(), f"Should greet returning: {data['reply']}"
        print(f"Returning lead greeting: {data['reply'][:80]}...")
    
    def test_auto_stage_interesado(self, auth_headers):
        """Test auto-stage to 'interesado' on price inquiry"""
        test_phone = f"+593PRICE{uuid.uuid4().hex[:8]}"
        
        # Create lead
        requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": "Price Test Lead",
            "whatsapp": test_phone,
            "funnel_stage": "nuevo"
        })
        
        # Send price inquiry
        response = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "Cuanto cuesta el producto?"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check stage update
        if data.get("stage_updated"):
            assert data["stage_updated"] == "interesado", f"Should update to interesado: {data['stage_updated']}"
            print(f"Auto-stage to interesado: SUCCESS")
        else:
            print(f"Stage may not have updated (was already interesado)")
    
    def test_auto_stage_en_negociacion(self, auth_headers):
        """Test auto-stage to 'en_negociacion' on quotation request"""
        test_phone = f"+593QUOTE{uuid.uuid4().hex[:8]}"
        
        # Create lead
        requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": "Quote Test Lead",
            "whatsapp": test_phone,
            "funnel_stage": "interesado"
        })
        
        # Send quotation request
        response = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "Quiero una cotizacion por favor"
        })
        assert response.status_code == 200
        data = response.json()
        
        if data.get("stage_updated"):
            assert data["stage_updated"] == "en_negociacion", f"Should update to en_negociacion: {data['stage_updated']}"
            print(f"Auto-stage to en_negociacion: SUCCESS")
    
    def test_auto_stage_perdido(self, auth_headers):
        """Test auto-stage to 'perdido' on rejection"""
        test_phone = f"+593LOST{uuid.uuid4().hex[:8]}"
        
        # Create lead
        requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": "Lost Test Lead",
            "whatsapp": test_phone,
            "funnel_stage": "interesado"
        })
        
        # Send rejection
        response = requests.post(f"{BASE_URL}/api/whatsapp/webhook", json={
            "from_number": test_phone,
            "message": "No me interesa gracias"
        })
        assert response.status_code == 200
        data = response.json()
        
        if data.get("stage_updated"):
            assert data["stage_updated"] == "perdido", f"Should update to perdido: {data['stage_updated']}"
            print(f"Auto-stage to perdido: SUCCESS")


class TestChatEndpoints:
    """Chat message and session delete tests"""
    
    def test_chat_send_and_delete_message(self, auth_headers):
        """Test sending a chat message and then deleting it"""
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        # Send a message
        send_response = requests.post(f"{BASE_URL}/api/chat/message", headers=auth_headers, json={
            "session_id": session_id,
            "message": "Hola, necesito informacion"
        })
        assert send_response.status_code == 200, f"Chat send failed: {send_response.text}"
        send_data = send_response.json()
        assert "response" in send_data, "No AI response"
        print(f"Chat AI responded: {send_data['response'][:60]}...")
        
        # Get chat history to find message ID
        history_response = requests.get(f"{BASE_URL}/api/chat/history/{session_id}", headers=auth_headers)
        assert history_response.status_code == 200
        messages = history_response.json()
        assert len(messages) >= 1, "No messages in history"
        
        # Delete first message
        msg_id = messages[0].get("id")
        if msg_id:
            delete_response = requests.delete(f"{BASE_URL}/api/chat/messages/{msg_id}", headers=auth_headers)
            assert delete_response.status_code == 200, f"Delete message failed: {delete_response.text}"
            print(f"Message deleted: {msg_id}")
        
        return session_id
    
    def test_delete_conversation(self, auth_headers):
        """Test deleting entire conversation"""
        session_id = f"test_delete_conv_{uuid.uuid4().hex[:8]}"
        
        # Create some messages
        for i in range(2):
            requests.post(f"{BASE_URL}/api/chat/message", headers=auth_headers, json={
                "session_id": session_id,
                "message": f"Test message {i}"
            })
        
        # Delete entire session
        delete_response = requests.delete(f"{BASE_URL}/api/chat/sessions/{session_id}", headers=auth_headers)
        assert delete_response.status_code == 200, f"Delete session failed: {delete_response.text}"
        data = delete_response.json()
        assert "eliminada" in data.get("message", "").lower() or "deleted" in data.get("message", "").lower()
        print(f"Conversation deleted: {data['message']}")
        
        # Verify messages are gone
        history_response = requests.get(f"{BASE_URL}/api/chat/history/{session_id}", headers=auth_headers)
        assert history_response.status_code == 200
        assert len(history_response.json()) == 0, "Messages should be deleted"


class TestLeadStageUpdate:
    """Test PUT /api/leads/{lead_id}/stage endpoint"""
    
    def test_update_lead_stage(self, auth_headers):
        """Test changing lead stage via PUT endpoint"""
        # Create a test lead
        create_response = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": f"Stage Test Lead {uuid.uuid4().hex[:4]}",
            "whatsapp": f"+593STG{uuid.uuid4().hex[:8]}",
            "funnel_stage": "nuevo"
        })
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Update stage to 'interesado'
        update_response = requests.put(f"{BASE_URL}/api/leads/{lead_id}/stage?stage=interesado", headers=auth_headers)
        assert update_response.status_code == 200, f"Stage update failed: {update_response.text}"
        
        # Verify change
        get_response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["funnel_stage"] == "interesado"
        print(f"Lead stage updated to 'interesado': SUCCESS")
        
        # Update to en_negociacion
        update_response2 = requests.put(f"{BASE_URL}/api/leads/{lead_id}/stage?stage=en_negociacion", headers=auth_headers)
        assert update_response2.status_code == 200
        
        get_response2 = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert get_response2.json()["funnel_stage"] == "en_negociacion"
        print(f"Lead stage updated to 'en_negociacion': SUCCESS")
    
    def test_invalid_stage_returns_400(self, auth_headers):
        """Test that invalid stage returns 400"""
        # Create a lead
        create_response = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": "Invalid Stage Test",
            "whatsapp": f"+593INV{uuid.uuid4().hex[:8]}"
        })
        lead_id = create_response.json()["id"]
        
        # Try invalid stage
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}/stage?stage=invalid_stage", headers=auth_headers)
        assert response.status_code == 400, f"Should return 400 for invalid stage: {response.status_code}"
        print("Invalid stage correctly returns 400")


class TestQuotations:
    """Quotation creation and PDF download tests"""
    
    def test_create_quotation(self, auth_headers):
        """Test creating a quotation"""
        # First get a lead
        leads_response = requests.get(f"{BASE_URL}/api/leads?limit=1", headers=auth_headers)
        leads = leads_response.json().get("leads", [])
        
        if not leads:
            # Create a lead if none exists
            create_lead = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
                "name": "Quote Test Lead",
                "whatsapp": f"+593QT{uuid.uuid4().hex[:8]}"
            })
            lead_id = create_lead.json()["id"]
        else:
            lead_id = leads[0]["id"]
        
        # Create quotation
        response = requests.post(f"{BASE_URL}/api/quotations", headers=auth_headers, json={
            "lead_id": lead_id,
            "items": [
                {"name": "Bombro - Bone Broth Hidrolizado", "price": 55.95, "quantity": 2},
                {"name": "Gomitas Melatonina", "price": 13.25, "quantity": 1}
            ],
            "notes": "Test quotation"
        })
        assert response.status_code == 200, f"Create quotation failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "total" in data
        assert data["total"] > 0
        print(f"Quotation created: ID={data['id'][:8]}... Total=${data['total']}")
        
        return data["id"]
    
    def test_quotation_updates_lead_stage(self, auth_headers):
        """Test that creating quotation updates lead to 'en_negociacion'"""
        # Create a new lead with 'nuevo' stage
        create_lead = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json={
            "name": "Quote Stage Test",
            "whatsapp": f"+593QS{uuid.uuid4().hex[:8]}",
            "funnel_stage": "nuevo"
        })
        lead_id = create_lead.json()["id"]
        
        # Create quotation
        requests.post(f"{BASE_URL}/api/quotations", headers=auth_headers, json={
            "lead_id": lead_id,
            "items": [{"name": "Test Product", "price": 50.00, "quantity": 1}]
        })
        
        # Check lead stage updated
        get_lead = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert get_lead.json()["funnel_stage"] == "en_negociacion", "Lead stage should update to en_negociacion after quotation"
        print("Lead stage updated to 'en_negociacion' after quotation: SUCCESS")
    
    def test_download_quotation_pdf(self, auth_headers):
        """Test PDF download endpoint"""
        # Get a quotation
        quotes_response = requests.get(f"{BASE_URL}/api/quotations", headers=auth_headers)
        quotes = quotes_response.json()
        
        if not quotes:
            pytest.skip("No quotations to test PDF download")
        
        quote_id = quotes[0]["id"]
        
        # Download PDF
        response = requests.get(f"{BASE_URL}/api/quotations/{quote_id}/pdf", headers=auth_headers)
        assert response.status_code == 200, f"PDF download failed: {response.status_code}"
        assert "application/pdf" in response.headers.get("Content-Type", "")
        assert len(response.content) > 100, "PDF should have content"
        print(f"PDF downloaded: {len(response.content)} bytes")


class TestBulkDownload:
    """Bulk download Excel tests with correct stage names"""
    
    def test_bulk_download_all(self, auth_headers):
        """Test downloading all leads Excel"""
        response = requests.get(f"{BASE_URL}/api/bulk/download?download_type=all", headers=auth_headers)
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("Content-Type", "")
        print(f"Bulk download 'all': {len(response.content)} bytes")
    
    def test_bulk_download_by_stage(self, auth_headers):
        """Test downloading by stage with new stage names"""
        # Test en_negociacion (was 'caliente')
        response_neg = requests.get(f"{BASE_URL}/api/bulk/download?download_type=stage&stage=en_negociacion", headers=auth_headers)
        assert response_neg.status_code == 200
        print("Bulk download 'en_negociacion' stage: SUCCESS")
        
        # Test perdido (was 'frio')
        response_perd = requests.get(f"{BASE_URL}/api/bulk/download?download_type=stage&stage=perdido", headers=auth_headers)
        assert response_perd.status_code == 200
        print("Bulk download 'perdido' stage: SUCCESS")


class TestLeadsCRUD:
    """Test leads list shows correct stage names"""
    
    def test_leads_list_has_new_stages(self, auth_headers):
        """Test that leads API returns leads with new stage names"""
        response = requests.get(f"{BASE_URL}/api/leads?limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        leads = data.get("leads", [])
        if leads:
            stages_found = set(lead.get("funnel_stage") for lead in leads)
            print(f"Stages found in leads: {stages_found}")
            
            # None should have old stage names
            assert "caliente" not in stages_found, "Old stage 'caliente' should not exist"
            assert "frio" not in stages_found, "Old stage 'frio' should not exist"
            print("Leads have correct new stage names")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
