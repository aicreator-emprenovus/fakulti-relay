"""
Test Leads API for Kanban Board Feature
Tests the leads CRUD operations and stage change endpoint.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLeadsKanban:
    """Test leads API endpoints for Kanban board functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # === Authentication Tests ===
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@fakulti.com"
        print("✓ Login with admin@fakulti.com / admin123 successful")
    
    def test_leads_requires_auth(self):
        """Test that leads endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/leads")
        assert response.status_code == 401
        print("✓ GET /api/leads requires authentication (401)")
    
    # === Leads GET Tests ===
    
    def test_get_leads_list(self, auth_headers):
        """Test getting list of leads"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["leads"], list)
        print(f"✓ GET /api/leads returns {data['total']} leads")
    
    def test_get_leads_pagination(self, auth_headers):
        """Test leads pagination with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/leads?limit=500", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # The Kanban board uses limit=500 to get all leads
        assert "leads" in data
        print(f"✓ GET /api/leads with limit=500 returns {len(data['leads'])} leads")
    
    def test_leads_have_required_fields(self, auth_headers):
        """Test that leads have all fields needed for Kanban cards"""
        response = requests.get(f"{BASE_URL}/api/leads?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["leads"]) > 0:
            lead = data["leads"][0]
            # Required fields for Kanban card display
            required_fields = ["id", "name", "whatsapp", "funnel_stage", "source"]
            for field in required_fields:
                assert field in lead, f"Lead missing required field: {field}"
            
            # Check funnel_stage is valid
            valid_stages = ["nuevo", "interesado", "en_negociacion", "cliente_nuevo", "cliente_activo", "perdido"]
            assert lead["funnel_stage"] in valid_stages, f"Invalid funnel_stage: {lead['funnel_stage']}"
            
            print(f"✓ Lead has all required fields: {required_fields}")
            print(f"  Sample lead: {lead['name']} - Stage: {lead['funnel_stage']}")
        else:
            print("⚠ No leads in database to validate fields")
    
    def test_leads_by_stage(self, auth_headers):
        """Test filtering leads by stage"""
        stages = ["nuevo", "interesado", "en_negociacion", "cliente_nuevo", "cliente_activo", "perdido"]
        stage_counts = {}
        
        for stage in stages:
            response = requests.get(f"{BASE_URL}/api/leads?stage={stage}&limit=100", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            stage_counts[stage] = data["total"]
            
            # Verify all returned leads have the correct stage
            for lead in data["leads"]:
                assert lead["funnel_stage"] == stage, f"Lead {lead['id']} has wrong stage"
        
        print(f"✓ Leads by stage filter works: {stage_counts}")
    
    def test_search_leads(self, auth_headers):
        """Test search functionality"""
        # First get a lead to search for
        response = requests.get(f"{BASE_URL}/api/leads?limit=5", headers=auth_headers)
        data = response.json()
        
        if len(data["leads"]) > 0:
            test_lead = data["leads"][0]
            # Search by part of name
            if test_lead.get("name"):
                search_term = test_lead["name"][:3]  # First 3 chars
                search_response = requests.get(
                    f"{BASE_URL}/api/leads?search={search_term}", 
                    headers=auth_headers
                )
                assert search_response.status_code == 200
                search_data = search_response.json()
                print(f"✓ Search for '{search_term}' returned {search_data['total']} results")
        else:
            print("⚠ No leads to test search")
    
    def test_filter_by_source(self, auth_headers):
        """Test filtering by source"""
        response = requests.get(f"{BASE_URL}/api/leads?source=web", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned leads have the correct source
        for lead in data["leads"]:
            assert lead["source"] == "web", f"Lead {lead['id']} has wrong source"
        
        print(f"✓ Source filter works: {data['total']} leads with source=web")
    
    # === Lead CRUD Tests ===
    
    def test_create_lead(self, auth_headers):
        """Test creating a new lead"""
        new_lead = {
            "name": "TEST_Kanban Lead",
            "whatsapp": "+593999111222",
            "city": "Quito",
            "email": "testkanban@test.com",
            "product_interest": "Bombro",
            "source": "web",
            "notes": "Test lead for Kanban testing",
            "funnel_stage": "nuevo"
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", json=new_lead, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == new_lead["name"]
        assert data["whatsapp"] == new_lead["whatsapp"]
        assert data["funnel_stage"] == "nuevo"
        assert "id" in data
        
        print(f"✓ Create lead successful: {data['id'][:8]}...")
        
        # Store ID for cleanup
        self.__class__.created_lead_id = data["id"]
        return data["id"]
    
    def test_get_single_lead(self, auth_headers):
        """Test getting a single lead by ID"""
        if not hasattr(self.__class__, 'created_lead_id'):
            pytest.skip("No lead created in previous test")
        
        lead_id = self.__class__.created_lead_id
        response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == lead_id
        assert data["name"] == "TEST_Kanban Lead"
        print(f"✓ Get single lead works for ID: {lead_id[:8]}...")
    
    def test_update_lead(self, auth_headers):
        """Test updating a lead (Edit icon functionality)"""
        if not hasattr(self.__class__, 'created_lead_id'):
            pytest.skip("No lead created in previous test")
        
        lead_id = self.__class__.created_lead_id
        update_data = {
            "name": "TEST_Kanban Lead Updated",
            "city": "Guayaquil",
            "notes": "Updated via test"
        }
        
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "TEST_Kanban Lead Updated"
        assert data["city"] == "Guayaquil"
        print(f"✓ Update lead successful")
    
    # === Stage Change Tests (Critical for Kanban) ===
    
    def test_change_lead_stage(self, auth_headers):
        """Test changing lead stage via API (dropdown and drag-drop)"""
        if not hasattr(self.__class__, 'created_lead_id'):
            pytest.skip("No lead created in previous test")
        
        lead_id = self.__class__.created_lead_id
        
        # Test changing through stages
        stages_to_test = ["interesado", "en_negociacion", "cliente_nuevo"]
        
        for new_stage in stages_to_test:
            response = requests.put(
                f"{BASE_URL}/api/leads/{lead_id}/stage?stage={new_stage}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Etapa actualizada"
            
            # Verify the change persisted
            verify_response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
            verify_data = verify_response.json()
            assert verify_data["funnel_stage"] == new_stage, f"Stage not updated to {new_stage}"
            
            print(f"✓ Stage changed to '{new_stage}' successfully")
    
    def test_stage_change_invalid_stage(self, auth_headers):
        """Test that invalid stage is rejected"""
        if not hasattr(self.__class__, 'created_lead_id'):
            pytest.skip("No lead created in previous test")
        
        lead_id = self.__class__.created_lead_id
        response = requests.put(
            f"{BASE_URL}/api/leads/{lead_id}/stage?stage=invalid_stage",
            headers=auth_headers
        )
        assert response.status_code == 400
        print("✓ Invalid stage rejected with 400")
    
    # === Delete Test (Cleanup) ===
    
    def test_delete_lead(self, auth_headers):
        """Test deleting a lead (Delete icon functionality)"""
        if not hasattr(self.__class__, 'created_lead_id'):
            pytest.skip("No lead created in previous test")
        
        lead_id = self.__class__.created_lead_id
        response = requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Lead eliminado"
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert verify_response.status_code == 404
        
        print(f"✓ Lead deleted and verified (404 on GET)")
    
    def test_delete_nonexistent_lead(self, auth_headers):
        """Test deleting a lead that doesn't exist"""
        response = requests.delete(f"{BASE_URL}/api/leads/nonexistent-id-12345", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Delete nonexistent lead returns 404")


class TestKanbanStageDistribution:
    """Test that leads are distributed across stages correctly for Kanban"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        return {"Authorization": f"Bearer {response.json()['token']}"}
    
    def test_stage_distribution(self, auth_headers):
        """Test that we can get leads for all 6 Kanban columns"""
        response = requests.get(f"{BASE_URL}/api/leads?limit=500", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Count leads per stage
        stage_counts = {
            "nuevo": 0,
            "interesado": 0,
            "en_negociacion": 0,
            "cliente_nuevo": 0,
            "cliente_activo": 0,
            "perdido": 0
        }
        
        for lead in data["leads"]:
            stage = lead.get("funnel_stage", "nuevo")
            if stage in stage_counts:
                stage_counts[stage] += 1
            else:
                stage_counts["nuevo"] += 1  # Default to nuevo if unknown stage
        
        print(f"✓ Stage distribution for Kanban columns:")
        print(f"  Prospecto (nuevo): {stage_counts['nuevo']}")
        print(f"  Interesado: {stage_counts['interesado']}")
        print(f"  En Negociacion: {stage_counts['en_negociacion']}")
        print(f"  Cliente Nuevo: {stage_counts['cliente_nuevo']}")
        print(f"  Cliente Activo: {stage_counts['cliente_activo']}")
        print(f"  Perdido: {stage_counts['perdido']}")
        print(f"  Total: {data['total']}")
        
        # Verify total matches
        assert sum(stage_counts.values()) == len(data["leads"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
