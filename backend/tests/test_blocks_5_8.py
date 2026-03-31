"""
Test suite for Blocks 5-8: Advisor Assignment, Notifications, Lead Cards, Customer Context
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://whatsapp-sales-hub-7.preview.emergentagent.com').rstrip('/')

@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@fakulti.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")

@pytest.fixture(scope="module")
def advisor_token():
    """Get advisor (Carlos) auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "carlos@fakulti.com",
        "password": "advisor123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Advisor authentication failed")

@pytest.fixture(scope="module")
def admin_client(admin_token):
    """Session with admin auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session

@pytest.fixture(scope="module")
def advisor_client(advisor_token):
    """Session with advisor auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {advisor_token}"
    })
    return session


class TestBlock5AdvisorAPIs:
    """Block 5: Advisor assignment and role-based filtering APIs"""
    
    def test_get_advisors_returns_list_with_leads_count(self, admin_client):
        """GET /api/advisors returns advisors with leads_count field"""
        response = admin_client.get(f"{BASE_URL}/api/advisors")
        assert response.status_code == 200
        
        advisors = response.json()
        assert isinstance(advisors, list)
        assert len(advisors) >= 2  # Carlos and Ana
        
        # Check for required fields
        for advisor in advisors:
            assert "id" in advisor
            assert "name" in advisor
            assert "email" in advisor
            assert "leads_count" in advisor  # Block 5 requirement
            assert "role" in advisor
            assert advisor["role"] == "advisor"
    
    def test_assign_lead_to_advisor(self, admin_client):
        """PUT /api/leads/{lead_id}/assign assigns advisor to lead"""
        # First create a test lead
        create_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block5_AssignLead",
            "whatsapp": "0999999105",
            "city": "Quito"
        })
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Get an advisor ID
        advisors_response = admin_client.get(f"{BASE_URL}/api/advisors")
        advisor_id = advisors_response.json()[0]["id"]
        
        # Assign lead to advisor
        assign_response = admin_client.put(f"{BASE_URL}/api/leads/{lead_id}/assign", json={
            "advisor_id": advisor_id
        })
        assert assign_response.status_code == 200
        assert "asignado" in assign_response.json().get("message", "").lower()
        
        # Verify assignment via GET lead
        lead_response = admin_client.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert lead_response.status_code == 200
        lead_data = lead_response.json()
        assert lead_data.get("assigned_advisor") == advisor_id
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_unassign_lead_from_advisor(self, admin_client):
        """PUT /api/leads/{lead_id}/assign with empty advisor_id unassigns"""
        # Create and assign a test lead
        create_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block5_UnassignLead",
            "whatsapp": "0999999106"
        })
        lead_id = create_response.json()["id"]
        advisors = admin_client.get(f"{BASE_URL}/api/advisors").json()
        admin_client.put(f"{BASE_URL}/api/leads/{lead_id}/assign", json={"advisor_id": advisors[0]["id"]})
        
        # Now unassign
        unassign_response = admin_client.put(f"{BASE_URL}/api/leads/{lead_id}/assign", json={
            "advisor_id": ""
        })
        assert unassign_response.status_code == 200
        
        # Verify unassigned
        lead_response = admin_client.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert lead_response.json().get("assigned_advisor") == ""
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_get_lead_includes_advisor_name(self, admin_client):
        """GET /api/leads/{lead_id} includes _advisor_name when assigned"""
        # Create lead and assign
        create_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block5_AdvisorName",
            "whatsapp": "0999999107"
        })
        lead_id = create_response.json()["id"]
        advisors = admin_client.get(f"{BASE_URL}/api/advisors").json()
        advisor = advisors[0]
        admin_client.put(f"{BASE_URL}/api/leads/{lead_id}/assign", json={"advisor_id": advisor["id"]})
        
        # Get lead and check for _advisor_name
        lead_response = admin_client.get(f"{BASE_URL}/api/leads/{lead_id}")
        assert lead_response.status_code == 200
        lead_data = lead_response.json()
        assert "_advisor_name" in lead_data
        assert lead_data["_advisor_name"] == advisor["name"]
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_role_based_filtering_advisor_sees_only_assigned_leads(self, admin_client, advisor_client):
        """Advisors only see their assigned leads"""
        # Get Carlos's advisor ID
        advisors = admin_client.get(f"{BASE_URL}/api/advisors").json()
        carlos = next((a for a in advisors if "carlos" in a["email"].lower()), advisors[0])
        
        # Create two leads - one assigned to Carlos, one not
        lead1_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block5_CarlosLead",
            "whatsapp": "0999999108"
        })
        lead1_id = lead1_response.json()["id"]
        admin_client.put(f"{BASE_URL}/api/leads/{lead1_id}/assign", json={"advisor_id": carlos["id"]})
        
        lead2_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block5_UnassignedLead",
            "whatsapp": "0999999109"
        })
        lead2_id = lead2_response.json()["id"]
        
        # Admin sees all leads
        admin_leads = admin_client.get(f"{BASE_URL}/api/leads").json()["leads"]
        admin_lead_ids = [l["id"] for l in admin_leads]
        assert lead1_id in admin_lead_ids
        assert lead2_id in admin_lead_ids
        
        # Advisor sees only assigned leads
        advisor_leads = advisor_client.get(f"{BASE_URL}/api/leads").json()["leads"]
        advisor_lead_ids = [l["id"] for l in advisor_leads]
        assert lead1_id in advisor_lead_ids  # Carlos's assigned lead
        assert lead2_id not in advisor_lead_ids  # Unassigned lead not visible
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead1_id}")
        admin_client.delete(f"{BASE_URL}/api/leads/{lead2_id}")


class TestBlock6NotificationAPIs:
    """Block 6: Internal notification alerts APIs"""
    
    def test_get_chat_alerts_returns_list(self, admin_client):
        """GET /api/chat/alerts returns list of alerts"""
        response = admin_client.get(f"{BASE_URL}/api/chat/alerts")
        assert response.status_code == 200
        
        alerts = response.json()
        assert isinstance(alerts, list)
    
    def test_get_advisors_notifications_returns_list(self, admin_client):
        """GET /api/advisors/notifications returns list of notifications"""
        response = admin_client.get(f"{BASE_URL}/api/advisors/notifications")
        assert response.status_code == 200
        
        notifications = response.json()
        assert isinstance(notifications, list)
    
    def test_mark_notification_read(self, admin_client):
        """PUT /api/advisors/notifications/{notif_id}/read marks as read"""
        # Note: This will work even if notif doesn't exist (no error thrown)
        response = admin_client.put(f"{BASE_URL}/api/advisors/notifications/test-notif-id/read")
        assert response.status_code == 200
        assert "leída" in response.json().get("message", "").lower() or "read" in response.json().get("message", "").lower()
    
    def test_mark_all_notifications_read(self, admin_client):
        """PUT /api/advisors/notifications/read-all marks all as read"""
        response = admin_client.put(f"{BASE_URL}/api/advisors/notifications/read-all")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestBlock7LeadCardAPIs:
    """Block 7: Lead card tags (channel, source, city, product_interest) APIs"""
    
    def test_lead_includes_tag_fields(self, admin_client):
        """GET /api/leads returns leads with channel, source, city, product_interest fields"""
        # Create lead with all tag fields
        create_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block7_TagFields",
            "whatsapp": "0999999110",
            "city": "Guayaquil",
            "source": "TV",
            "channel": "TV/QR",
            "product_interest": "Bombro"
        })
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Verify fields are returned in leads list
        leads_response = admin_client.get(f"{BASE_URL}/api/leads")
        leads = leads_response.json()["leads"]
        test_lead = next((l for l in leads if l["id"] == lead_id), None)
        
        assert test_lead is not None
        assert test_lead.get("city") == "Guayaquil"
        assert test_lead.get("source") == "TV"
        assert test_lead.get("channel") == "TV/QR"
        assert test_lead.get("product_interest") == "Bombro"
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_advisor_filter_in_leads(self, admin_client):
        """GET /api/leads?advisor={id} filters by advisor"""
        advisors = admin_client.get(f"{BASE_URL}/api/advisors").json()
        if not advisors:
            pytest.skip("No advisors available")
        
        advisor = advisors[0]
        response = admin_client.get(f"{BASE_URL}/api/leads", params={"advisor": advisor["id"]})
        assert response.status_code == 200
        
        leads = response.json()["leads"]
        # All returned leads should be assigned to this advisor (or empty if none)
        for lead in leads:
            assert lead.get("assigned_advisor") == advisor["id"]


class TestBlock8CustomerContextAPIs:
    """Block 8: Customer context card APIs - lead details for chat"""
    
    def test_get_lead_session_includes_full_lead_details(self, admin_client):
        """GET /api/chat/lead-session/{lead_id} returns lead with all context fields"""
        # Create lead with full details
        create_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block8_Context",
            "whatsapp": "0999999111",
            "city": "Cuenca",
            "email": "test.block8@example.com",
            "source": "web",
            "channel": "Web",
            "product_interest": "CBD",
            "season": "verano"
        })
        lead_id = create_response.json()["id"]
        
        # Get lead session
        session_response = admin_client.get(f"{BASE_URL}/api/chat/lead-session/{lead_id}")
        assert session_response.status_code == 200
        
        data = session_response.json()
        assert "lead" in data
        lead = data["lead"]
        
        # Verify all context fields
        assert lead.get("whatsapp") == "0999999111"
        assert lead.get("email") == "test.block8@example.com"
        assert lead.get("city") == "Cuenca"
        assert lead.get("source") == "web"
        assert lead.get("channel") == "Web"
        assert lead.get("product_interest") == "CBD"
        assert lead.get("season") == "verano"
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead_id}")
    
    def test_lead_session_includes_advisor_name(self, admin_client):
        """GET /api/chat/lead-session/{lead_id} includes _advisor_name when assigned"""
        # Create and assign lead
        create_response = admin_client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_Block8_AdvisorContext",
            "whatsapp": "0999999112"
        })
        lead_id = create_response.json()["id"]
        
        advisors = admin_client.get(f"{BASE_URL}/api/advisors").json()
        advisor = advisors[0]
        admin_client.put(f"{BASE_URL}/api/leads/{lead_id}/assign", json={"advisor_id": advisor["id"]})
        
        # Get lead session
        session_response = admin_client.get(f"{BASE_URL}/api/chat/lead-session/{lead_id}")
        assert session_response.status_code == 200
        
        lead = session_response.json().get("lead", {})
        assert "_advisor_name" in lead
        assert lead["_advisor_name"] == advisor["name"]
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/leads/{lead_id}")


class TestCleanup:
    """Cleanup any remaining test data"""
    
    def test_cleanup_test_leads(self, admin_client):
        """Remove TEST_ prefixed leads"""
        leads_response = admin_client.get(f"{BASE_URL}/api/leads", params={"limit": 500})
        leads = leads_response.json().get("leads", [])
        
        deleted = 0
        for lead in leads:
            if lead.get("name", "").startswith("TEST_Block"):
                admin_client.delete(f"{BASE_URL}/api/leads/{lead['id']}")
                deleted += 1
        
        print(f"Cleaned up {deleted} test leads")
        assert True
