"""
Test suite for Automation Rules endpoints - CRM Fakulti
Tests: Export, Import, Delete All, Update with wa_template fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEVELOPER_EMAIL = "aicreator@emprenovus.com"
DEVELOPER_PASSWORD = "Jlsb*1082"
ADMIN_EMAIL = "admin@fakulti.com"
ADMIN_PASSWORD = "Admin123!"


class TestAutomationRulesEndpoints:
    """Test automation rules CRUD and new export/import/delete-all endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token for developer"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as developer
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEVELOPER_EMAIL,
            "password": DEVELOPER_PASSWORD
        })
        assert login_res.status_code == 200, f"Developer login failed: {login_res.text}"
        self.token = login_res.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store created rule IDs for cleanup
        self.created_rule_ids = []
        yield
        
        # Cleanup: Delete test rules
        for rule_id in self.created_rule_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/automation/rules/{rule_id}")
            except:
                pass
    
    # ========== GET /automation/rules ==========
    def test_get_automation_rules(self):
        """Test GET /api/automation/rules returns list"""
        res = self.session.get(f"{BASE_URL}/api/automation/rules")
        assert res.status_code == 200, f"GET rules failed: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/automation/rules returns {len(data)} rules")
    
    # ========== POST /automation/rules (Create) ==========
    def test_create_automation_rule(self):
        """Test POST /api/automation/rules creates a new rule"""
        payload = {
            "name": "TEST_Rule_Create",
            "trigger_type": "sin_respuesta",
            "trigger_value": "4",
            "action_type": "enviar_mensaje",
            "action_value": "Hola {nombre}, te recordamos...",
            "description": "Test rule for automation",
            "active": True,
            "wa_template_name": "test_template",
            "wa_template_language": "es"
        }
        res = self.session.post(f"{BASE_URL}/api/automation/rules", json=payload)
        assert res.status_code == 200, f"Create rule failed: {res.text}"
        
        data = res.json()
        assert "id" in data, "Response should have id"
        assert data["name"] == payload["name"], "Name should match"
        assert data["wa_template_name"] == "test_template", "wa_template_name should be saved"
        assert data["wa_template_language"] == "es", "wa_template_language should be saved"
        
        self.created_rule_ids.append(data["id"])
        print(f"PASS: POST /api/automation/rules created rule with id {data['id']}")
        return data["id"]
    
    # ========== PUT /automation/rules/{id} (Update with wa_template fields) ==========
    def test_update_automation_rule_with_wa_template_fields(self):
        """Test PUT /api/automation/rules/{id} accepts wa_template_name and wa_template_language"""
        # First create a rule
        create_payload = {
            "name": "TEST_Rule_Update",
            "trigger_type": "sin_respuesta",
            "trigger_value": "2",
            "action_type": "enviar_mensaje",
            "action_value": "Original message",
            "description": "Original description",
            "active": True,
            "wa_template_name": "",
            "wa_template_language": "es"
        }
        create_res = self.session.post(f"{BASE_URL}/api/automation/rules", json=create_payload)
        assert create_res.status_code == 200, f"Create rule failed: {create_res.text}"
        rule_id = create_res.json()["id"]
        self.created_rule_ids.append(rule_id)
        
        # Update the rule with wa_template fields
        update_payload = {
            "name": "TEST_Rule_Updated",
            "trigger_type": "sin_respuesta",
            "trigger_value": "6",
            "action_type": "enviar_mensaje",
            "action_value": "Updated message",
            "description": "Updated description",
            "active": True,
            "wa_template_name": "recordatorio_fakulti",
            "wa_template_language": "es_MX"
        }
        update_res = self.session.put(f"{BASE_URL}/api/automation/rules/{rule_id}", json=update_payload)
        assert update_res.status_code == 200, f"Update rule failed with 422: {update_res.text}"
        
        updated_data = update_res.json()
        assert updated_data["name"] == "TEST_Rule_Updated", "Name should be updated"
        assert updated_data["wa_template_name"] == "recordatorio_fakulti", "wa_template_name should be updated"
        assert updated_data["wa_template_language"] == "es_MX", "wa_template_language should be updated"
        
        # Verify with GET
        get_res = self.session.get(f"{BASE_URL}/api/automation/rules")
        rules = get_res.json()
        updated_rule = next((r for r in rules if r["id"] == rule_id), None)
        assert updated_rule is not None, "Rule should exist"
        assert updated_rule["wa_template_name"] == "recordatorio_fakulti", "wa_template_name should persist"
        
        print(f"PASS: PUT /api/automation/rules/{rule_id} successfully updated with wa_template fields (no 422 error)")
    
    # ========== GET /automation/rules/export ==========
    def test_export_automation_rules(self):
        """Test GET /api/automation/rules/export returns all rules as JSON array"""
        res = self.session.get(f"{BASE_URL}/api/automation/rules/export")
        assert res.status_code == 200, f"Export rules failed: {res.text}"
        
        data = res.json()
        assert isinstance(data, list), "Export should return a list"
        
        # Verify structure if rules exist
        if len(data) > 0:
            rule = data[0]
            assert "name" in rule, "Rule should have name"
            assert "trigger_type" in rule, "Rule should have trigger_type"
            assert "action_type" in rule, "Rule should have action_type"
        
        print(f"PASS: GET /api/automation/rules/export returns {len(data)} rules as JSON array")
    
    # ========== POST /automation/rules/import ==========
    def test_import_automation_rules(self):
        """Test POST /api/automation/rules/import accepts rules array and creates them"""
        import_payload = {
            "rules": [
                {
                    "name": "TEST_Imported_Rule_1",
                    "trigger_type": "nuevo_lead",
                    "trigger_value": "",
                    "action_type": "enviar_mensaje",
                    "action_value": "Bienvenido!",
                    "description": "Imported rule 1",
                    "active": True,
                    "wa_template_name": "bienvenida",
                    "wa_template_language": "es"
                },
                {
                    "name": "TEST_Imported_Rule_2",
                    "trigger_type": "sin_respuesta",
                    "trigger_value": "24",
                    "action_type": "enviar_mensaje",
                    "action_value": "Recordatorio",
                    "description": "Imported rule 2",
                    "active": False,
                    "wa_template_name": "",
                    "wa_template_language": "es"
                }
            ]
        }
        
        res = self.session.post(f"{BASE_URL}/api/automation/rules/import", json=import_payload)
        assert res.status_code == 200, f"Import rules failed: {res.text}"
        
        data = res.json()
        assert "imported" in data, "Response should have imported count"
        assert data["imported"] == 2, f"Should import 2 rules, got {data['imported']}"
        
        # Verify rules were created
        get_res = self.session.get(f"{BASE_URL}/api/automation/rules")
        rules = get_res.json()
        imported_names = [r["name"] for r in rules]
        assert "TEST_Imported_Rule_1" in imported_names, "Imported rule 1 should exist"
        assert "TEST_Imported_Rule_2" in imported_names, "Imported rule 2 should exist"
        
        # Store IDs for cleanup
        for rule in rules:
            if rule["name"].startswith("TEST_Imported_Rule"):
                self.created_rule_ids.append(rule["id"])
        
        print(f"PASS: POST /api/automation/rules/import successfully imported {data['imported']} rules")
    
    def test_import_empty_rules_returns_400(self):
        """Test POST /api/automation/rules/import with empty rules returns 400"""
        res = self.session.post(f"{BASE_URL}/api/automation/rules/import", json={"rules": []})
        assert res.status_code == 400, f"Empty import should return 400, got {res.status_code}"
        print("PASS: POST /api/automation/rules/import with empty rules returns 400")
    
    # ========== DELETE /automation/rules/all ==========
    def test_delete_all_automation_rules(self):
        """Test DELETE /api/automation/rules/all deletes all rules"""
        # First create some test rules
        for i in range(3):
            payload = {
                "name": f"TEST_DeleteAll_Rule_{i}",
                "trigger_type": "sin_respuesta",
                "trigger_value": str(i + 1),
                "action_type": "enviar_mensaje",
                "action_value": f"Message {i}",
                "description": f"Test rule {i}",
                "active": True,
                "wa_template_name": "",
                "wa_template_language": "es"
            }
            create_res = self.session.post(f"{BASE_URL}/api/automation/rules", json=payload)
            assert create_res.status_code == 200
        
        # Get count before delete
        before_res = self.session.get(f"{BASE_URL}/api/automation/rules")
        before_count = len(before_res.json())
        assert before_count >= 3, f"Should have at least 3 rules, got {before_count}"
        
        # Delete all
        delete_res = self.session.delete(f"{BASE_URL}/api/automation/rules/all")
        assert delete_res.status_code == 200, f"Delete all failed: {delete_res.text}"
        
        data = delete_res.json()
        assert "deleted" in data, "Response should have deleted count"
        assert data["deleted"] >= 3, f"Should delete at least 3 rules, got {data['deleted']}"
        
        # Verify all deleted
        after_res = self.session.get(f"{BASE_URL}/api/automation/rules")
        after_count = len(after_res.json())
        assert after_count == 0, f"Should have 0 rules after delete all, got {after_count}"
        
        # Clear cleanup list since all deleted
        self.created_rule_ids.clear()
        
        print(f"PASS: DELETE /api/automation/rules/all deleted {data['deleted']} rules")


class TestAutomationRulesAdminAccess:
    """Test that admin can also access automation rules endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get auth token for admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
        self.token = login_res.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        self.created_rule_ids = []
        yield
        
        # Cleanup
        for rule_id in self.created_rule_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/automation/rules/{rule_id}")
            except:
                pass
    
    def test_admin_can_export_rules(self):
        """Test admin can access export endpoint"""
        res = self.session.get(f"{BASE_URL}/api/automation/rules/export")
        assert res.status_code == 200, f"Admin export failed: {res.text}"
        print("PASS: Admin can access GET /api/automation/rules/export")
    
    def test_admin_can_import_rules(self):
        """Test admin can import rules"""
        import_payload = {
            "rules": [
                {
                    "name": "TEST_Admin_Import",
                    "trigger_type": "nuevo_lead",
                    "trigger_value": "",
                    "action_type": "enviar_mensaje",
                    "action_value": "Admin imported",
                    "active": True,
                    "wa_template_name": "",
                    "wa_template_language": "es"
                }
            ]
        }
        res = self.session.post(f"{BASE_URL}/api/automation/rules/import", json=import_payload)
        assert res.status_code == 200, f"Admin import failed: {res.text}"
        
        # Get rule ID for cleanup
        get_res = self.session.get(f"{BASE_URL}/api/automation/rules")
        for rule in get_res.json():
            if rule["name"] == "TEST_Admin_Import":
                self.created_rule_ids.append(rule["id"])
        
        print("PASS: Admin can access POST /api/automation/rules/import")
    
    def test_admin_can_delete_all_rules(self):
        """Test admin can delete all rules"""
        # Create a test rule first
        create_res = self.session.post(f"{BASE_URL}/api/automation/rules", json={
            "name": "TEST_Admin_DeleteAll",
            "trigger_type": "sin_respuesta",
            "trigger_value": "1",
            "action_type": "enviar_mensaje",
            "action_value": "Test",
            "active": True,
            "wa_template_name": "",
            "wa_template_language": "es"
        })
        assert create_res.status_code == 200
        
        # Delete all
        res = self.session.delete(f"{BASE_URL}/api/automation/rules/all")
        assert res.status_code == 200, f"Admin delete all failed: {res.text}"
        
        self.created_rule_ids.clear()
        print("PASS: Admin can access DELETE /api/automation/rules/all")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
