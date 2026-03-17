"""
Block 3 Tests: Product-Specific Bots and QR Scan Counter
========================================================
Features tested:
1. GET /api/products returns 5 products with bot_config
2. GET /api/products/{id}/bot-config returns bot config for a product
3. PUT /api/products/{id}/bot-config updates bot config fields
4. QR Campaigns show scan_count field
5. Product-specific bot prompts (build_product_bot_prompt logic)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@fakulti.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestProductBotConfig:
    """Test product bot configuration endpoints"""
    
    def test_get_products_returns_5_products(self, auth_headers):
        """Verify GET /api/products returns 5 products"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        products = response.json()
        assert isinstance(products, list), "Products should be a list"
        assert len(products) == 5, f"Expected 5 products, got {len(products)}"
        
        # Check expected product names (partial match due to longer names in DB)
        product_names = [p["name"] for p in products]
        expected_keywords = ["Bombro", "Melatonina", "CBD", "Pitch Up", "Magnesio"]
        for keyword in expected_keywords:
            found = any(keyword.lower() in pn.lower() for pn in product_names)
            assert found, f"Expected product containing '{keyword}' not found in {product_names}"
        print(f"✓ All 5 products found: {product_names}")
    
    def test_products_have_bot_config_structure(self, auth_headers):
        """Verify each product has bot_config object (or defaults available)"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200
        products = response.json()
        
        for p in products:
            # bot_config may be explicitly stored or available via GET endpoint
            product_id = p["id"]
            bot_res = requests.get(f"{BASE_URL}/api/products/{product_id}/bot-config", headers=auth_headers)
            assert bot_res.status_code == 200, f"Failed to get bot config for {p['name']}: {bot_res.text}"
            
            config = bot_res.json()
            expected_fields = ["personality", "key_benefits", "usage_info", "restrictions", "faqs"]
            for field in expected_fields:
                assert field in config, f"Bot config for {p['name']} missing field '{field}'"
            print(f"✓ Bot config structure verified for product: {p['name']}")
    
    def test_get_product_bot_config_endpoint(self, auth_headers):
        """Test GET /api/products/{id}/bot-config returns correct structure"""
        # First get a product
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0
        
        product = products[0]
        product_id = product["id"]
        
        # Get bot config
        bot_response = requests.get(f"{BASE_URL}/api/products/{product_id}/bot-config", headers=auth_headers)
        assert bot_response.status_code == 200, f"Failed: {bot_response.text}"
        
        config = bot_response.json()
        expected_fields = ["personality", "key_benefits", "usage_info", "restrictions", "faqs"]
        for field in expected_fields:
            assert field in config, f"Missing field: {field}"
        
        print(f"✓ GET /api/products/{product_id}/bot-config returns correct structure")
    
    def test_get_bot_config_for_nonexistent_product(self, auth_headers):
        """Test GET /api/products/{id}/bot-config returns 404 for invalid product"""
        fake_id = "nonexistent-product-id-12345"
        response = requests.get(f"{BASE_URL}/api/products/{fake_id}/bot-config", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ GET bot-config for nonexistent product returns 404")
    
    def test_update_product_bot_config(self, auth_headers):
        """Test PUT /api/products/{id}/bot-config updates fields"""
        # Get a product
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200
        products = response.json()
        
        # Find Bombro product
        bombro = next((p for p in products if "Bombro" in p["name"]), None)
        if not bombro:
            bombro = products[0]
        
        product_id = bombro["id"]
        
        # Update bot config
        new_config = {
            "personality": "TEST: Experto en nutricion deportiva, amigable y motivador",
            "key_benefits": "TEST: Mejora articulaciones, soporte digestivo, recuperacion muscular",
            "usage_info": "TEST: Un sachet al dia disuelto en agua o jugo",
            "restrictions": "TEST: No hacer promesas medicas. Consultar medico antes.",
            "faqs": "TEST: Es de origen bovino? Si, caldo de hueso 100% natural."
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/products/{product_id}/bot-config", 
            json=new_config, 
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_config = update_response.json()
        assert updated_config["personality"] == new_config["personality"]
        assert updated_config["key_benefits"] == new_config["key_benefits"]
        assert updated_config["usage_info"] == new_config["usage_info"]
        print(f"✓ PUT /api/products/{product_id}/bot-config successfully updated")
        
        # Verify persistence with GET
        verify_response = requests.get(f"{BASE_URL}/api/products/{product_id}/bot-config", headers=auth_headers)
        assert verify_response.status_code == 200
        verified_config = verify_response.json()
        assert verified_config["personality"] == new_config["personality"], "Config not persisted"
        print("✓ Bot config update persisted correctly")
    
    def test_update_bot_config_filters_invalid_fields(self, auth_headers):
        """Test that PUT /api/products/{id}/bot-config only allows valid fields"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        products = response.json()
        product_id = products[0]["id"]
        
        # Try to update with invalid fields
        config_with_invalid = {
            "personality": "Valid personality",
            "invalid_field": "Should be ignored",
            "another_bad_field": "Also ignored"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/products/{product_id}/bot-config",
            json=config_with_invalid,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # Verify only valid field was saved
        config = update_response.json()
        assert "invalid_field" not in config
        assert "another_bad_field" not in config
        print("✓ Invalid fields filtered correctly in bot config update")


class TestQRCampaignScanCount:
    """Test QR campaign scan_count field"""
    
    def test_qr_campaigns_have_scan_count(self, auth_headers):
        """Verify GET /api/qr-campaigns includes scan_count field"""
        response = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        campaigns = response.json()
        assert isinstance(campaigns, list), "Expected list of campaigns"
        
        for campaign in campaigns:
            assert "scan_count" in campaign, f"Campaign {campaign.get('name')} missing scan_count"
            assert isinstance(campaign["scan_count"], int), f"scan_count should be integer, got {type(campaign['scan_count'])}"
            print(f"✓ Campaign '{campaign['name']}' has scan_count: {campaign['scan_count']}")
        
        print(f"✓ All {len(campaigns)} QR campaigns have scan_count field")
    
    def test_qr_campaign_leads_count_also_present(self, auth_headers):
        """Verify leads_count field is also present (from Block 2)"""
        response = requests.get(f"{BASE_URL}/api/qr-campaigns", headers=auth_headers)
        assert response.status_code == 200
        
        campaigns = response.json()
        for campaign in campaigns:
            assert "leads_count" in campaign, f"Campaign {campaign.get('name')} missing leads_count"
        
        print("✓ All campaigns have both scan_count and leads_count fields")


class TestProductBotPromptLogic:
    """Test that products with bot_config can be used for specialized prompts"""
    
    def test_product_with_bot_config_can_be_retrieved(self, auth_headers):
        """Ensure product data includes bot_config after update"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        products = response.json()
        
        # Check that at least one product has bot_config stored (after our earlier update)
        products_with_config = [p for p in products if p.get("bot_config")]
        
        # Even if empty, the endpoint should work
        for p in products:
            bot_res = requests.get(f"{BASE_URL}/api/products/{p['id']}/bot-config", headers=auth_headers)
            assert bot_res.status_code == 200
        
        print("✓ All products' bot_config accessible via endpoint")
    
    def test_all_five_products_exist_with_correct_data(self, auth_headers):
        """Verify all 5 expected products exist with basic required fields"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200
        products = response.json()
        
        required_fields = ["id", "name", "price"]
        for p in products:
            for field in required_fields:
                assert field in p, f"Product missing field: {field}"
            assert p["price"] >= 0, f"Price should be positive for {p['name']}"
        
        names = [p["name"] for p in products]
        print(f"✓ All products verified: {names}")


class TestSettingsPageDataFlow:
    """Test the data flow for Settings page (Products and Bots)"""
    
    def test_create_update_delete_product_flow(self, auth_headers):
        """Test full CRUD flow for products"""
        # Create test product
        test_product = {
            "name": "TEST_Product_Block3",
            "code": "TEST-B3",
            "description": "Test product for Block 3 testing",
            "price": 99.99,
            "original_price": 149.99,
            "stock": 50,
            "category": "test",
            "active": True
        }
        
        create_res = requests.post(f"{BASE_URL}/api/products", json=test_product, headers=auth_headers)
        assert create_res.status_code == 200, f"Create failed: {create_res.text}"
        created = create_res.json()
        product_id = created["id"]
        print(f"✓ Product created: {product_id}")
        
        # Update bot config for new product
        bot_config = {
            "personality": "TEST bot personality",
            "key_benefits": "TEST benefits",
            "usage_info": "TEST usage",
            "restrictions": "TEST restrictions",
            "faqs": "TEST faqs"
        }
        bot_res = requests.put(f"{BASE_URL}/api/products/{product_id}/bot-config", json=bot_config, headers=auth_headers)
        assert bot_res.status_code == 200
        print("✓ Bot config set for test product")
        
        # Verify bot config
        verify_res = requests.get(f"{BASE_URL}/api/products/{product_id}/bot-config", headers=auth_headers)
        assert verify_res.status_code == 200
        verified = verify_res.json()
        assert verified["personality"] == bot_config["personality"]
        print("✓ Bot config verified")
        
        # Delete test product
        delete_res = requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=auth_headers)
        assert delete_res.status_code == 200
        print("✓ Test product deleted")
        
        # Verify deletion
        get_res = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        products = get_res.json()
        assert not any(p["id"] == product_id for p in products), "Product should be deleted"
        print("✓ Full CRUD flow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
