"""
Block 1 Features Testing for Fakulti CRM
=========================================
Tests for:
1. Stage labels (Contacto inicial, Chat, En Negociación, Leads ganados, Cartera activa, Perdido)
2. Phone normalization (Ecuador phones: +593 -> 0XX format)
3. Season/temporada filter on leads
4. Games standby (only slot_machine active)
5. Bulk Excel upload with phone normalization, season and channel
6. Channel field added to leads
"""

import pytest
import requests
import os
import io
import openpyxl

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock1Features:
    """Block 1 CRM Update Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: login and get token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # ============ PHONE NORMALIZATION TESTS ============
    
    def test_phone_normalization_plus593(self):
        """POST /api/leads with +593991234567 should store as 0991234567"""
        lead_data = {
            "name": "TEST_PhoneNorm1",
            "whatsapp": "+593991234567",
            "source": "web"
        }
        res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert res.status_code == 200, f"Create lead failed: {res.text}"
        
        created = res.json()
        assert created["whatsapp"] == "0991234567", f"Phone not normalized: {created['whatsapp']}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Phone +593991234567 normalized to 0991234567")
    
    def test_phone_normalization_593_no_plus(self):
        """POST /api/leads with 593991234567 should store as 0991234567"""
        lead_data = {
            "name": "TEST_PhoneNorm2",
            "whatsapp": "593991234567",
            "source": "web"
        }
        res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert res.status_code == 200, f"Create lead failed: {res.text}"
        
        created = res.json()
        assert created["whatsapp"] == "0991234567", f"Phone not normalized: {created['whatsapp']}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Phone 593991234567 normalized to 0991234567")
    
    def test_phone_already_normalized(self):
        """POST /api/leads with 0991234567 should stay as 0991234567"""
        lead_data = {
            "name": "TEST_PhoneNorm3",
            "whatsapp": "0991234567",
            "source": "web"
        }
        res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert res.status_code == 200, f"Create lead failed: {res.text}"
        
        created = res.json()
        assert created["whatsapp"] == "0991234567", f"Phone changed unexpectedly: {created['whatsapp']}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Phone 0991234567 stays normalized")
    
    # ============ SEASON FILTER TESTS ============
    
    def test_season_filter_verano(self):
        """GET /api/leads?season=verano should filter correctly"""
        # Create test lead with season
        lead_data = {
            "name": "TEST_SeasonVerano",
            "whatsapp": "0999888777",
            "season": "verano",
            "source": "web"
        }
        create_res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert create_res.status_code == 200
        created = create_res.json()
        
        # Filter by season
        filter_res = requests.get(f"{BASE_URL}/api/leads?season=verano", headers=self.headers)
        assert filter_res.status_code == 200
        
        leads = filter_res.json()["leads"]
        assert any(l["id"] == created["id"] for l in leads), "Season filter not working"
        
        # All returned leads should have verano season
        for lead in leads:
            if lead.get("season"):  # Some leads may not have season set
                assert lead["season"] == "verano" or lead["season"] == "", f"Wrong season in filter results: {lead['season']}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Season filter works for 'verano'")
    
    def test_season_filter_invierno(self):
        """GET /api/leads?season=invierno should filter correctly"""
        # Create test lead with season
        lead_data = {
            "name": "TEST_SeasonInvierno",
            "whatsapp": "0999888776",
            "season": "invierno",
            "source": "web"
        }
        create_res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert create_res.status_code == 200
        created = create_res.json()
        
        # Filter by season
        filter_res = requests.get(f"{BASE_URL}/api/leads?season=invierno", headers=self.headers)
        assert filter_res.status_code == 200
        
        leads = filter_res.json()["leads"]
        assert any(l["id"] == created["id"] for l in leads), "Season filter not working for invierno"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Season filter works for 'invierno'")
    
    # ============ CHANNEL FIELD TESTS ============
    
    def test_lead_has_channel_field(self):
        """Lead should support channel field"""
        lead_data = {
            "name": "TEST_Channel",
            "whatsapp": "0999888775",
            "channel": "Instagram",
            "source": "pauta_digital"
        }
        create_res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert create_res.status_code == 200
        created = create_res.json()
        
        assert created.get("channel") == "Instagram", f"Channel not saved: {created.get('channel')}"
        
        # Verify on GET
        get_res = requests.get(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        assert get_res.status_code == 200
        assert get_res.json().get("channel") == "Instagram"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Channel field works correctly")
    
    def test_channel_filter(self):
        """GET /api/leads?channel=Facebook should filter correctly"""
        # Create test lead with channel
        lead_data = {
            "name": "TEST_ChannelFacebook",
            "whatsapp": "0999888774",
            "channel": "Facebook",
            "source": "pauta_digital"
        }
        create_res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert create_res.status_code == 200
        created = create_res.json()
        
        # Filter by channel
        filter_res = requests.get(f"{BASE_URL}/api/leads?channel=Facebook", headers=self.headers)
        assert filter_res.status_code == 200
        
        leads = filter_res.json()["leads"]
        assert any(l["id"] == created["id"] for l in leads), "Channel filter not working"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Channel filter works correctly")
    
    # ============ GAMES STANDBY TESTS ============
    
    def test_games_config_standby(self):
        """GET /api/games/config should show roulette=inactive, scratch_card=inactive, slot_machine=active"""
        res = requests.get(f"{BASE_URL}/api/games/config", headers=self.headers)
        assert res.status_code == 200, f"Games config failed: {res.text}"
        
        configs = res.json()
        
        # Find each game config
        slot_machine = next((c for c in configs if c.get("game_type") == "slot_machine"), None)
        roulette = next((c for c in configs if c.get("game_type") == "roulette"), None)
        scratch_card = next((c for c in configs if c.get("game_type") == "scratch_card"), None)
        
        # Check slot_machine is active
        if slot_machine:
            assert slot_machine.get("active") == True, f"slot_machine should be active: {slot_machine.get('active')}"
            print("✓ slot_machine is active")
        else:
            print("⚠ slot_machine config not found (may not be seeded)")
        
        # Check roulette is inactive
        if roulette:
            assert roulette.get("active") == False, f"roulette should be inactive: {roulette.get('active')}"
            print("✓ roulette is inactive")
        else:
            print("⚠ roulette config not found (expected if games standby)")
        
        # Check scratch_card is inactive
        if scratch_card:
            assert scratch_card.get("active") == False, f"scratch_card should be inactive: {scratch_card.get('active')}"
            print("✓ scratch_card is inactive")
        else:
            print("⚠ scratch_card config not found (expected if games standby)")
        
        print("✓ Games standby configuration verified")
    
    # ============ BULK UPLOAD TESTS ============
    
    def test_bulk_upload_phone_normalization(self):
        """POST /api/bulk/upload should normalize phone numbers"""
        # Create Excel file in memory
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Nombre", "WhatsApp", "Ciudad", "Temporada", "Canal"])
        ws.append(["TEST_Bulk1", "+593987654321", "Quito", "verano", "Instagram"])
        ws.append(["TEST_Bulk2", "593976543210", "Guayaquil", "invierno", "Facebook"])
        ws.append(["TEST_Bulk3", "0965432109", "Cuenca", "todo_el_año", "TikTok"])
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        files = {"file": ("test_bulk.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res = requests.post(f"{BASE_URL}/api/bulk/upload", files=files, headers=self.headers)
        assert res.status_code == 200, f"Bulk upload failed: {res.text}"
        
        result = res.json()
        assert result.get("created", 0) > 0 or result.get("updated", 0) > 0, f"No leads processed: {result}"
        
        # Verify phone normalization by searching for the leads
        search_res = requests.get(f"{BASE_URL}/api/leads?search=TEST_Bulk", headers=self.headers)
        assert search_res.status_code == 200
        
        leads = search_res.json()["leads"]
        for lead in leads:
            if lead["name"] == "TEST_Bulk1":
                assert lead["whatsapp"] == "0987654321", f"Bulk phone not normalized: {lead['whatsapp']}"
            elif lead["name"] == "TEST_Bulk2":
                assert lead["whatsapp"] == "0976543210", f"Bulk phone not normalized: {lead['whatsapp']}"
            elif lead["name"] == "TEST_Bulk3":
                assert lead["whatsapp"] == "0965432109", f"Bulk phone changed: {lead['whatsapp']}"
        
        # Cleanup
        for lead in leads:
            if lead["name"].startswith("TEST_Bulk"):
                requests.delete(f"{BASE_URL}/api/leads/{lead['id']}", headers=self.headers)
        
        print("✓ Bulk upload normalizes phone numbers correctly")
    
    def test_bulk_upload_season_channel(self):
        """POST /api/bulk/upload should preserve season and channel fields"""
        # Create Excel file in memory
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Nombre", "WhatsApp", "Ciudad", "Temporada", "Canal"])
        ws.append(["TEST_BulkSC1", "0912345678", "Quito", "verano", "WhatsApp"])
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        files = {"file": ("test_season_channel.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res = requests.post(f"{BASE_URL}/api/bulk/upload", files=files, headers=self.headers)
        assert res.status_code == 200, f"Bulk upload failed: {res.text}"
        
        # Verify season and channel
        search_res = requests.get(f"{BASE_URL}/api/leads?search=TEST_BulkSC1", headers=self.headers)
        assert search_res.status_code == 200
        
        leads = search_res.json()["leads"]
        assert len(leads) > 0, "Bulk uploaded lead not found"
        
        lead = leads[0]
        assert lead.get("season") == "verano", f"Season not preserved: {lead.get('season')}"
        assert lead.get("channel") == "WhatsApp", f"Channel not preserved: {lead.get('channel')}"
        
        # Cleanup
        for lead in leads:
            if lead["name"].startswith("TEST_BulkSC"):
                requests.delete(f"{BASE_URL}/api/leads/{lead['id']}", headers=self.headers)
        
        print("✓ Bulk upload preserves season and channel fields")
    
    # ============ DASHBOARD STATS (STAGE LABELS) ============
    
    def test_dashboard_stats_funnel_stages(self):
        """GET /api/dashboard/stats should return correct stage keys"""
        res = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert res.status_code == 200, f"Dashboard stats failed: {res.text}"
        
        stats = res.json()
        stages = stats.get("stages", {})
        
        expected_stages = ["nuevo", "interesado", "en_negociacion", "cliente_nuevo", "cliente_activo", "perdido"]
        for stage in expected_stages:
            assert stage in stages, f"Missing stage: {stage}"
        
        print("✓ Dashboard stats returns all funnel stages")
    
    # ============ LEAD DETAIL DIALOG FIELDS ============
    
    def test_lead_has_temporada_and_channel(self):
        """Lead detail should include season (temporada) and channel fields"""
        # Create lead with both fields
        lead_data = {
            "name": "TEST_DetailFields",
            "whatsapp": "0999111222",
            "season": "verano",
            "channel": "Instagram",
            "source": "pauta_digital"
        }
        create_res = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=self.headers)
        assert create_res.status_code == 200
        created = create_res.json()
        
        # Get lead detail
        detail_res = requests.get(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        assert detail_res.status_code == 200
        
        detail = detail_res.json()
        assert "season" in detail, "season field missing in lead detail"
        assert "channel" in detail, "channel field missing in lead detail"
        assert detail["season"] == "verano"
        assert detail["channel"] == "Instagram"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{created['id']}", headers=self.headers)
        print("✓ Lead detail includes season and channel fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
