"""
Block 2 Testing: QR Campaigns, Initial Intents, Channel Detection
- QR Campaign CRUD endpoints
- Intent CRUD endpoints
- QR code generation
- WhatsApp link generation
- Channel field on leads
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Get auth token for protected endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Auth failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestQRCampaigns(TestAuth):
    """QR Campaign CRUD tests"""
    
    def test_get_qr_campaigns_returns_list(self, headers):
        """GET /api/qr-campaigns returns list with leads_count"""
        response = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=headers)
        assert response.status_code == 200
        campaigns = response.json()
        assert isinstance(campaigns, list)
        # Verify seed data exists (3 default campaigns)
        assert len(campaigns) >= 3, "Expected at least 3 default QR campaigns"
        # Verify structure
        first_campaign = campaigns[0]
        assert "id" in first_campaign
        assert "name" in first_campaign
        assert "channel" in first_campaign
        assert "source" in first_campaign
        assert "initial_message" in first_campaign
        assert "leads_count" in first_campaign, "Missing leads_count field"
        print(f"Found {len(campaigns)} QR campaigns")
    
    def test_create_qr_campaign(self, headers):
        """POST /api/qr-campaigns creates a new campaign"""
        payload = {
            "name": "TEST_QR_Campaign_Block2",
            "channel": "Evento",
            "source": "Evento",
            "product": "Bombro",
            "initial_message": "Hola desde TEST Block 2",
            "intent": "consulta_test",
            "description": "Test campaign for Block 2",
            "active": True
        }
        response = requests.post(f"{BASE_URL}/api/qr-campaigns", headers=headers, json=payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        campaign = response.json()
        assert campaign["name"] == payload["name"]
        assert campaign["channel"] == payload["channel"]
        assert campaign["source"] == payload["source"]
        assert campaign["initial_message"] == payload["initial_message"]
        assert "id" in campaign
        print(f"Created QR campaign: {campaign['id']}")
        return campaign["id"]
    
    def test_update_qr_campaign(self, headers):
        """PUT /api/qr-campaigns/{id} updates a campaign"""
        # First create
        create_payload = {
            "name": "TEST_QR_Update",
            "channel": "Web",
            "source": "web",
            "product": "",
            "initial_message": "Original message",
            "intent": "",
            "description": "",
            "active": True
        }
        create_res = requests.post(f"{BASE_URL}/api/qr-campaigns", headers=headers, json=create_payload)
        assert create_res.status_code == 200
        campaign_id = create_res.json()["id"]
        
        # Update
        update_payload = {
            "name": "TEST_QR_Update_Modified",
            "channel": "Pauta Digital",
            "source": "pauta_digital",
            "product": "Bombro Premium",
            "initial_message": "Updated message",
            "intent": "updated_intent",
            "description": "Updated description",
            "active": False
        }
        update_res = requests.put(f"{BASE_URL}/api/qr-campaigns/{campaign_id}", headers=headers, json=update_payload)
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["name"] == update_payload["name"]
        assert updated["channel"] == update_payload["channel"]
        assert updated["active"] == False
        print(f"Updated QR campaign: {campaign_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qr-campaigns/{campaign_id}", headers=headers)
    
    def test_delete_qr_campaign(self, headers):
        """DELETE /api/qr-campaigns/{id} deletes a campaign"""
        # Create to delete
        create_payload = {
            "name": "TEST_QR_Delete",
            "channel": "TV/QR",
            "source": "TV",
            "product": "",
            "initial_message": "To be deleted",
            "intent": "",
            "description": "",
            "active": True
        }
        create_res = requests.post(f"{BASE_URL}/api/qr-campaigns", headers=headers, json=create_payload)
        campaign_id = create_res.json()["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/qr-campaigns/{campaign_id}", headers=headers)
        assert delete_res.status_code == 200
        assert "eliminada" in delete_res.json().get("message", "").lower()
        
        # Verify deleted - should not appear in list
        list_res = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=headers)
        campaigns = list_res.json()
        assert not any(c["id"] == campaign_id for c in campaigns), "Campaign still exists after deletion"
        print(f"Deleted QR campaign: {campaign_id}")
    
    def test_qr_code_generation_returns_png(self, headers):
        """GET /api/qr-campaigns/{id}/qrcode returns PNG image"""
        # Get first campaign
        list_res = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=headers)
        campaigns = list_res.json()
        assert len(campaigns) > 0
        campaign_id = campaigns[0]["id"]
        
        # QR code endpoint is PUBLIC (no auth needed per main agent note)
        qr_res = requests.get(f"{BASE_URL}/api/qr-campaigns/{campaign_id}/qrcode")
        assert qr_res.status_code == 200, f"QR code failed: {qr_res.status_code}"
        assert qr_res.headers.get("content-type") == "image/png"
        assert len(qr_res.content) > 100, "QR image too small"
        print(f"QR code generated for campaign {campaign_id}, size: {len(qr_res.content)} bytes")
    
    def test_whatsapp_link_generation(self, headers):
        """GET /api/qr-campaigns/{id}/link returns WhatsApp link"""
        # Get first campaign
        list_res = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=headers)
        campaigns = list_res.json()
        campaign_id = campaigns[0]["id"]
        campaign_msg = campaigns[0]["initial_message"]
        
        link_res = requests.get(f"{BASE_URL}/api/qr-campaigns/{campaign_id}/link", headers=headers)
        assert link_res.status_code == 200
        data = link_res.json()
        assert "link" in data
        assert "wa.me" in data["link"], "Link should contain wa.me"
        assert "text=" in data["link"], "Link should contain pre-filled text"
        print(f"WhatsApp link: {data['link'][:80]}...")


class TestIntents(TestAuth):
    """Initial Intents CRUD tests"""
    
    def test_get_intents_returns_list(self, headers):
        """GET /api/intents returns list of intents"""
        response = requests.get(f"{BASE_URL}/api/intents", headers=headers)
        assert response.status_code == 200
        intents = response.json()
        assert isinstance(intents, list)
        assert len(intents) >= 5, "Expected at least 5 default intents"
        # Verify structure
        first_intent = intents[0]
        assert "id" in first_intent
        assert "name" in first_intent
        assert "keywords" in first_intent
        assert isinstance(first_intent["keywords"], list)
        print(f"Found {len(intents)} intents")
    
    def test_create_intent(self, headers):
        """POST /api/intents creates a new intent"""
        payload = {
            "name": "TEST_Intent_Block2",
            "keywords": ["test keyword", "prueba", "testing"],
            "channel": "Web",
            "source": "web",
            "product": "Bombro",
            "response_hint": "Guide to product info",
            "active": True
        }
        response = requests.post(f"{BASE_URL}/api/intents", headers=headers, json=payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        intent = response.json()
        assert intent["name"] == payload["name"]
        assert intent["keywords"] == payload["keywords"]
        assert intent["channel"] == payload["channel"]
        assert "id" in intent
        print(f"Created intent: {intent['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/intents/{intent['id']}", headers=headers)
    
    def test_update_intent(self, headers):
        """PUT /api/intents/{id} updates an intent"""
        # Create
        create_payload = {
            "name": "TEST_Intent_Update",
            "keywords": ["original", "keyword"],
            "channel": "",
            "source": "",
            "product": "",
            "response_hint": "",
            "active": True
        }
        create_res = requests.post(f"{BASE_URL}/api/intents", headers=headers, json=create_payload)
        intent_id = create_res.json()["id"]
        
        # Update
        update_payload = {
            "name": "TEST_Intent_Update_Modified",
            "keywords": ["new", "updated", "keywords"],
            "channel": "Fibeca",
            "source": "Fibeca",
            "product": "Bombro Premium",
            "response_hint": "New hint",
            "active": False
        }
        update_res = requests.put(f"{BASE_URL}/api/intents/{intent_id}", headers=headers, json=update_payload)
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["name"] == update_payload["name"]
        assert updated["keywords"] == update_payload["keywords"]
        assert updated["active"] == False
        print(f"Updated intent: {intent_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/intents/{intent_id}", headers=headers)
    
    def test_delete_intent(self, headers):
        """DELETE /api/intents/{id} deletes an intent"""
        # Create to delete
        create_payload = {
            "name": "TEST_Intent_Delete",
            "keywords": ["delete", "me"],
            "channel": "",
            "source": "",
            "product": "",
            "response_hint": "",
            "active": True
        }
        create_res = requests.post(f"{BASE_URL}/api/intents", headers=headers, json=create_payload)
        intent_id = create_res.json()["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/intents/{intent_id}", headers=headers)
        assert delete_res.status_code == 200
        assert "eliminada" in delete_res.json().get("message", "").lower()
        
        # Verify deleted
        list_res = requests.get(f"{BASE_URL}/api/intents", headers=headers)
        intents = list_res.json()
        assert not any(i["id"] == intent_id for i in intents), "Intent still exists after deletion"
        print(f"Deleted intent: {intent_id}")


class TestLeadChannelField(TestAuth):
    """Test channel field on leads"""
    
    def test_create_lead_with_channel(self, headers):
        """POST /api/leads with channel field"""
        payload = {
            "name": "TEST_Lead_Channel",
            "whatsapp": "0991111111",
            "channel": "TV/QR",
            "source": "TV",
            "season": "verano"
        }
        response = requests.post(f"{BASE_URL}/api/leads", headers=headers, json=payload)
        assert response.status_code == 200
        lead = response.json()
        assert lead["channel"] == "TV/QR"
        assert lead["source"] == "TV"
        print(f"Created lead with channel: {lead['id']}")
        
        # Verify GET returns channel
        get_res = requests.get(f"{BASE_URL}/api/leads/{lead['id']}", headers=headers)
        assert get_res.status_code == 200
        lead_data = get_res.json()
        assert lead_data["channel"] == "TV/QR"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead['id']}", headers=headers)
    
    def test_filter_leads_by_channel(self, headers):
        """GET /api/leads?channel= filters correctly"""
        # Create lead with specific channel
        payload = {
            "name": "TEST_Lead_Filter_Channel",
            "whatsapp": "0992222222",
            "channel": "Evento_Test_Unique",
            "source": "Evento"
        }
        create_res = requests.post(f"{BASE_URL}/api/leads", headers=headers, json=payload)
        lead_id = create_res.json()["id"]
        
        # Filter by channel
        filter_res = requests.get(f"{BASE_URL}/api/leads", headers=headers, params={"channel": "Evento_Test_Unique"})
        assert filter_res.status_code == 200
        leads = filter_res.json()["leads"]
        assert len(leads) >= 1
        assert any(l["channel"] == "Evento_Test_Unique" for l in leads)
        print(f"Channel filter working, found {len(leads)} leads")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=headers)
    
    def test_update_lead_channel(self, headers):
        """PUT /api/leads/{id} updates channel field"""
        # Create
        create_res = requests.post(f"{BASE_URL}/api/leads", headers=headers, json={
            "name": "TEST_Lead_Update_Channel",
            "whatsapp": "0993333333",
            "channel": "Web"
        })
        lead_id = create_res.json()["id"]
        
        # Update channel
        update_res = requests.put(f"{BASE_URL}/api/leads/{lead_id}", headers=headers, json={"channel": "Fibeca"})
        assert update_res.status_code == 200
        assert update_res.json()["channel"] == "Fibeca"
        
        # Verify
        get_res = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=headers)
        assert get_res.json()["channel"] == "Fibeca"
        print(f"Updated lead channel: {lead_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=headers)


class TestCleanup(TestAuth):
    """Cleanup test data"""
    
    def test_cleanup_test_campaigns(self, headers):
        """Remove TEST_ prefixed campaigns"""
        list_res = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=headers)
        for campaign in list_res.json():
            if campaign["name"].startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/qr-campaigns/{campaign['id']}", headers=headers)
                print(f"Cleaned up campaign: {campaign['name']}")
    
    def test_cleanup_test_intents(self, headers):
        """Remove TEST_ prefixed intents"""
        list_res = requests.get(f"{BASE_URL}/api/intents", headers=headers)
        for intent in list_res.json():
            if intent["name"].startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/intents/{intent['id']}", headers=headers)
                print(f"Cleaned up intent: {intent['name']}")
    
    def test_cleanup_test_leads(self, headers):
        """Remove TEST_ prefixed leads"""
        list_res = requests.get(f"{BASE_URL}/api/leads", headers=headers)
        for lead in list_res.json().get("leads", []):
            if lead["name"].startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/leads/{lead['id']}", headers=headers)
                print(f"Cleaned up lead: {lead['name']}")
