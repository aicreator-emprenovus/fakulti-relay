"""
Test suite for Configuracion Panel features:
- Automation Rules CRUD (GET, POST, PATCH toggle, DELETE)
- WhatsApp Config (GET masked token, PUT save, POST test connection)
- AI Config (GET 4 toggles, PUT update)
- Meta WhatsApp Webhook (GET verification, POST incoming)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fakulti.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestAutomationRules(TestAuth):
    """Automation Rules CRUD - /api/automation/rules"""
    
    def test_get_automation_rules_returns_10_seeded(self, headers):
        """GET /api/automation/rules - returns 10 seeded rules"""
        response = requests.get(f"{BASE_URL}/api/automation/rules", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        rules = response.json()
        assert isinstance(rules, list)
        assert len(rules) >= 10, f"Expected at least 10 rules, got {len(rules)}"
        
        # Verify rule structure
        if rules:
            rule = rules[0]
            assert "id" in rule
            assert "name" in rule
            assert "trigger_type" in rule
            assert "action_type" in rule
            assert "active" in rule
        print(f"Found {len(rules)} automation rules")
    
    def test_create_automation_rule(self, headers):
        """POST /api/automation/rules - create new rule"""
        unique_name = f"TEST_Rule_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "trigger_type": "nuevo_lead",
            "trigger_value": "",
            "action_type": "enviar_mensaje",
            "action_value": "Test message content",
            "description": "Test rule created by pytest",
            "active": True
        }
        response = requests.post(f"{BASE_URL}/api/automation/rules", json=payload, headers=headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created = response.json()
        assert created["name"] == unique_name
        assert created["trigger_type"] == "nuevo_lead"
        assert created["action_type"] == "enviar_mensaje"
        assert created["active"] == True
        assert "id" in created
        print(f"Created rule: {created['id']}")
        
        # Store for cleanup
        TestAutomationRules.created_rule_id = created["id"]
        return created["id"]
    
    def test_toggle_rule_active_inactive(self, headers):
        """PATCH /api/automation/rules/{id}/toggle - toggle active/inactive"""
        # First get an existing rule
        response = requests.get(f"{BASE_URL}/api/automation/rules", headers=headers)
        rules = response.json()
        rule_id = rules[0]["id"]
        original_active = rules[0]["active"]
        
        # Toggle
        response = requests.patch(f"{BASE_URL}/api/automation/rules/{rule_id}/toggle", headers=headers)
        assert response.status_code == 200, f"Toggle failed: {response.text}"
        
        result = response.json()
        assert "active" in result
        assert result["active"] == (not original_active), f"Expected toggle from {original_active} to {not original_active}"
        print(f"Toggled rule {rule_id}: {original_active} -> {result['active']}")
        
        # Toggle back to restore original state
        requests.patch(f"{BASE_URL}/api/automation/rules/{rule_id}/toggle", headers=headers)
    
    def test_delete_automation_rule(self, headers):
        """DELETE /api/automation/rules/{id} - delete rule"""
        # Create a new rule to delete
        payload = {
            "name": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}",
            "trigger_type": "nuevo_lead",
            "action_type": "enviar_mensaje",
            "description": "This rule will be deleted"
        }
        create_resp = requests.post(f"{BASE_URL}/api/automation/rules", json=payload, headers=headers)
        assert create_resp.status_code == 200
        rule_id = create_resp.json()["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/automation/rules/{rule_id}", headers=headers)
        assert response.status_code == 200, f"Delete failed: {response.text}"
        
        # Verify deleted
        get_resp = requests.get(f"{BASE_URL}/api/automation/rules", headers=headers)
        rules = get_resp.json()
        rule_ids = [r["id"] for r in rules]
        assert rule_id not in rule_ids, "Rule should be deleted"
        print(f"Deleted rule: {rule_id}")


class TestWhatsAppConfig(TestAuth):
    """WhatsApp Config - /api/config/whatsapp"""
    
    def test_get_whatsapp_config_masked_token(self, headers):
        """GET /api/config/whatsapp - returns config with masked token"""
        response = requests.get(f"{BASE_URL}/api/config/whatsapp", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        config = response.json()
        assert "id" in config
        assert "phone_number_id" in config
        assert "access_token" in config
        assert "verify_token" in config
        assert "business_name" in config
        
        # Token should be masked or empty
        token = config.get("access_token", "")
        if token and len(token) > 4:
            assert "..." in token or token == "****", f"Token should be masked: {token}"
        
        print(f"WhatsApp config: phone_number_id={config.get('phone_number_id')}, verify_token={config.get('verify_token')}")
    
    def test_save_whatsapp_config(self, headers):
        """PUT /api/config/whatsapp - save config"""
        # Get current config first
        get_resp = requests.get(f"{BASE_URL}/api/config/whatsapp", headers=headers)
        current = get_resp.json()
        
        payload = {
            "phone_number_id": current.get("phone_number_id", "") or "test123456789",
            "access_token": current.get("access_token", ""),  # Keep masked token
            "verify_token": "fakulti-whatsapp-verify-token",
            "business_name": "Fakulti Laboratorios Test"
        }
        response = requests.put(f"{BASE_URL}/api/config/whatsapp", json=payload, headers=headers)
        assert response.status_code == 200, f"Save failed: {response.text}"
        
        saved = response.json()
        assert saved["verify_token"] == "fakulti-whatsapp-verify-token"
        print(f"Saved WhatsApp config: business_name={saved.get('business_name')}")
    
    def test_whatsapp_test_connection_fails_without_credentials(self, headers):
        """POST /api/config/whatsapp/test - returns error without real credentials"""
        response = requests.post(f"{BASE_URL}/api/config/whatsapp/test", headers=headers)
        assert response.status_code == 200, f"Test call failed: {response.text}"
        
        result = response.json()
        assert "success" in result
        assert "message" in result
        # Without real credentials, should return failure
        assert result["success"] == False, "Expected failure without real credentials"
        print(f"Test connection result: {result['message']}")


class TestMetaWhatsAppWebhook:
    """Meta WhatsApp Webhook - /api/webhook/whatsapp GET/POST"""
    
    def test_webhook_verification_correct_token(self):
        """GET /api/webhook/whatsapp with correct verify_token returns challenge"""
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "fakulti-whatsapp-verify-token",
            "hub.challenge": "12345"
        }
        response = requests.get(f"{BASE_URL}/api/webhook/whatsapp", params=params)
        assert response.status_code == 200, f"Verification failed: {response.text}"
        assert response.text == "12345", f"Expected challenge '12345', got '{response.text}'"
        print("Webhook verification with correct token: PASSED")
    
    def test_webhook_verification_wrong_token_returns_403(self):
        """GET /api/webhook/whatsapp with wrong token returns 403"""
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "12345"
        }
        response = requests.get(f"{BASE_URL}/api/webhook/whatsapp", params=params)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("Webhook verification with wrong token: 403 PASSED")
    
    def test_webhook_post_accepts_meta_format(self):
        """POST /api/webhook/whatsapp - accepts Meta format incoming message"""
        # Meta WhatsApp webhook format
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550001234",
                            "phone_number_id": "123456789"
                        },
                        "contacts": [{"profile": {"name": "Test User"}, "wa_id": "593991234567"}],
                        "messages": [{
                            "from": "593991234567",
                            "id": "wamid.test123",
                            "timestamp": "1672531200",
                            "type": "text",
                            "text": {"body": "Hola, quiero informacion sobre Bombro"}
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=payload)
        assert response.status_code == 200, f"Webhook POST failed: {response.text}"
        
        result = response.json()
        assert result.get("status") == "ok", f"Expected status 'ok', got {result}"
        print("Webhook POST with Meta format: PASSED")


class TestAIConfig(TestAuth):
    """AI Config - /api/config/ai"""
    
    def test_get_ai_config_has_4_toggles(self, headers):
        """GET /api/config/ai - returns ai config with 4 toggles"""
        response = requests.get(f"{BASE_URL}/api/config/ai", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        config = response.json()
        assert "id" in config
        # Check all 4 toggles exist
        assert "intent_analysis" in config, "Missing intent_analysis toggle"
        assert "lead_classification" in config, "Missing lead_classification toggle"
        assert "product_recommendation" in config, "Missing product_recommendation toggle"
        assert "suggested_responses" in config, "Missing suggested_responses toggle"
        
        # Verify they are booleans
        assert isinstance(config["intent_analysis"], bool)
        assert isinstance(config["lead_classification"], bool)
        assert isinstance(config["product_recommendation"], bool)
        assert isinstance(config["suggested_responses"], bool)
        
        print(f"AI config: {config}")
    
    def test_update_ai_toggles(self, headers):
        """PUT /api/config/ai - update toggles"""
        # Get current config
        get_resp = requests.get(f"{BASE_URL}/api/config/ai", headers=headers)
        current = get_resp.json()
        
        # Toggle one value
        new_value = not current.get("intent_analysis", True)
        payload = {
            "intent_analysis": new_value,
            "lead_classification": current.get("lead_classification", True),
            "product_recommendation": current.get("product_recommendation", True),
            "suggested_responses": current.get("suggested_responses", True)
        }
        
        response = requests.put(f"{BASE_URL}/api/config/ai", json=payload, headers=headers)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        assert updated["intent_analysis"] == new_value
        print(f"Updated AI config: intent_analysis={updated['intent_analysis']}")
        
        # Restore original value
        payload["intent_analysis"] = current.get("intent_analysis", True)
        requests.put(f"{BASE_URL}/api/config/ai", json=payload, headers=headers)


class TestCleanup(TestAuth):
    """Cleanup test-created data"""
    
    def test_cleanup_test_rules(self, headers):
        """Remove test rules created during testing"""
        response = requests.get(f"{BASE_URL}/api/automation/rules", headers=headers)
        rules = response.json()
        
        deleted_count = 0
        for rule in rules:
            if rule.get("name", "").startswith("TEST_"):
                del_resp = requests.delete(f"{BASE_URL}/api/automation/rules/{rule['id']}", headers=headers)
                if del_resp.status_code == 200:
                    deleted_count += 1
        
        print(f"Cleaned up {deleted_count} test rules")
        assert True  # Cleanup is best effort


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
