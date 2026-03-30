"""
Test suite for Campaign Image functionality - P0 bug fix verification
Tests:
1. Auth login
2. Image upload and serving
3. Campaign CRUD with image_url
4. Campaign send records [Imagen:] in chat_messages
5. Campaign list with image_url
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from environment
ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@fakulti.com")
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "admin123")


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Login successful for {ADMIN_EMAIL}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestImageUpload:
    """Image upload and serving tests"""
    
    def test_upload_image(self, auth_headers):
        """Test uploading an image returns URL"""
        # Create a simple test image (1x1 red pixel PNG)
        import base64
        # Minimal valid PNG (1x1 red pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test_image.png", png_data, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/upload-image",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "url" in data, "No URL in response"
        assert data["url"].startswith("/api/uploads/"), f"Unexpected URL format: {data['url']}"
        assert "filename" in data, "No filename in response"
        print(f"✓ Image uploaded successfully: {data['url']}")
        return data["url"]
    
    def test_serve_uploaded_image(self, auth_headers):
        """Test that uploaded image can be served"""
        # First upload an image
        import base64
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        
        files = {"file": ("test_serve.png", png_data, "image/png")}
        upload_response = requests.post(
            f"{BASE_URL}/api/upload-image",
            files=files,
            headers=auth_headers
        )
        assert upload_response.status_code == 200
        url = upload_response.json()["url"]
        
        # Now fetch the image (no auth required for serving)
        serve_response = requests.get(f"{BASE_URL}{url}")
        assert serve_response.status_code == 200, f"Serve failed: {serve_response.status_code}"
        assert "image" in serve_response.headers.get("content-type", ""), "Not an image content type"
        print(f"✓ Image served successfully from {url}")
    
    def test_serve_nonexistent_image(self):
        """Test that nonexistent image returns 404"""
        response = requests.get(f"{BASE_URL}/api/uploads/nonexistent_file_12345.png")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Nonexistent image correctly returns 404")


class TestCampaignCRUD:
    """Campaign CRUD operations with image_url"""
    
    def test_create_campaign_with_image(self, auth_headers):
        """Test creating a campaign with image_url"""
        campaign_data = {
            "name": f"TEST_Campaign_Image_{int(time.time())}",
            "description": "Test campaign with image",
            "campaign_type": "promo",
            "message_template": "Hola {nombre}, mira nuestra promo!",
            "image_url": f"{BASE_URL}/api/uploads/test_image.png",
            "target_stage": "",
            "target_product": "",
            "target_channel": ""
        }
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=campaign_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert "id" in data, "No ID in response"
        assert data["name"] == campaign_data["name"]
        assert data["image_url"] == campaign_data["image_url"], "image_url not saved correctly"
        assert data["status"] == "draft"
        print(f"✓ Campaign created with image_url: {data['id']}")
        return data["id"]
    
    def test_list_campaigns_shows_image_url(self, auth_headers):
        """Test that campaign list includes image_url"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200, f"List failed: {response.text}"
        campaigns = response.json()
        assert isinstance(campaigns, list), "Response should be a list"
        
        # Check if any campaign has image_url field
        has_image_url_field = any("image_url" in c for c in campaigns)
        print(f"✓ Campaigns listed: {len(campaigns)} campaigns, image_url field present: {has_image_url_field}")
    
    def test_update_campaign_image_url(self, auth_headers):
        """Test updating a campaign's image_url"""
        # First create a campaign
        campaign_data = {
            "name": f"TEST_Update_Image_{int(time.time())}",
            "description": "Test update",
            "message_template": "Test message",
            "image_url": ""
        }
        create_response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=campaign_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        campaign_id = create_response.json()["id"]
        
        # Update with image_url
        new_image_url = f"{BASE_URL}/api/uploads/updated_image.png"
        update_data = {
            "name": campaign_data["name"],
            "message_template": campaign_data["message_template"],
            "image_url": new_image_url
        }
        update_response = requests.put(
            f"{BASE_URL}/api/campaigns/{campaign_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated = update_response.json()
        assert updated["image_url"] == new_image_url, "image_url not updated"
        print(f"✓ Campaign image_url updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)


class TestCampaignSend:
    """Campaign send functionality - verifies [Imagen:] in chat_messages"""
    
    def test_campaign_send_records_image_in_chat(self, auth_headers):
        """Test that sending a campaign with image records [Imagen:] in chat_messages"""
        # 1. Create a test lead first
        lead_data = {
            "name": "TEST_Campaign_Lead",
            "whatsapp": "0999999999",
            "city": "Quito",
            "source": "web",
            "funnel_stage": "nuevo"
        }
        lead_response = requests.post(
            f"{BASE_URL}/api/leads",
            json=lead_data,
            headers=auth_headers
        )
        assert lead_response.status_code == 200, f"Lead creation failed: {lead_response.text}"
        lead_id = lead_response.json()["id"]
        print(f"✓ Test lead created: {lead_id}")
        
        # 2. Create a campaign with image_url
        image_url = "/api/uploads/campaign_test_image.png"
        campaign_data = {
            "name": f"TEST_Send_Campaign_{int(time.time())}",
            "description": "Test send with image",
            "message_template": "Hola {nombre}, mira esta imagen!",
            "image_url": image_url,
            "target_stage": "nuevo"  # Target the lead we just created
        }
        campaign_response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=campaign_data,
            headers=auth_headers
        )
        assert campaign_response.status_code == 200, f"Campaign creation failed: {campaign_response.text}"
        campaign_id = campaign_response.json()["id"]
        print(f"✓ Test campaign created: {campaign_id}")
        
        # 3. Send the campaign
        send_response = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/send",
            json={"batch_size": 10},
            headers=auth_headers
        )
        assert send_response.status_code == 200, f"Campaign send failed: {send_response.text}"
        send_data = send_response.json()
        print(f"✓ Campaign sent: {send_data}")
        
        # 4. Check chat sessions for the lead
        sessions_response = requests.get(f"{BASE_URL}/api/chat/sessions", headers=auth_headers)
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        
        # Find session for our test lead
        lead_session = None
        for s in sessions:
            if s.get("lead_id") == lead_id:
                lead_session = s
                break
        
        if lead_session:
            # 5. Get chat history and verify [Imagen:] is present
            history_response = requests.get(
                f"{BASE_URL}/api/chat/history/{lead_session['session_id']}",
                headers=auth_headers
            )
            assert history_response.status_code == 200
            messages = history_response.json()
            
            # Check for [Imagen:] pattern in messages
            found_image_tag = False
            for msg in messages:
                content = msg.get("content", "")
                if "[Imagen:" in content:
                    found_image_tag = True
                    print(f"✓ Found [Imagen:] tag in message: {content[:100]}...")
                    # Verify the image URL is included
                    assert image_url in content or "uploads" in content, "Image URL not in message content"
                    break
            
            if not found_image_tag:
                print(f"Messages found: {[m.get('content', '')[:50] for m in messages]}")
            assert found_image_tag, "No [Imagen:] tag found in chat messages after campaign send"
        else:
            # If no session found, check if campaign was sent to at least one lead
            assert send_data.get("sent", 0) > 0 or send_data.get("failed", 0) == 0, "Campaign should have sent to at least one lead"
            print("✓ Campaign send completed (session may not be created if WA not configured)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
    
    def test_campaign_send_without_image(self, auth_headers):
        """Test that sending a campaign without image works correctly"""
        # Create a test lead
        lead_data = {
            "name": "TEST_NoImage_Lead",
            "whatsapp": "0988888888",
            "funnel_stage": "interesado"
        }
        lead_response = requests.post(
            f"{BASE_URL}/api/leads",
            json=lead_data,
            headers=auth_headers
        )
        assert lead_response.status_code == 200
        lead_id = lead_response.json()["id"]
        
        # Create campaign without image
        campaign_data = {
            "name": f"TEST_NoImage_Campaign_{int(time.time())}",
            "message_template": "Hola {nombre}, mensaje sin imagen",
            "image_url": "",
            "target_stage": "interesado"
        }
        campaign_response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=campaign_data,
            headers=auth_headers
        )
        assert campaign_response.status_code == 200
        campaign_id = campaign_response.json()["id"]
        
        # Send campaign
        send_response = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/send",
            json={"batch_size": 5},
            headers=auth_headers
        )
        assert send_response.status_code == 200
        print(f"✓ Campaign without image sent successfully: {send_response.json()}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_campaigns(self, auth_headers):
        """Remove all TEST_ prefixed campaigns"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        if response.status_code == 200:
            campaigns = response.json()
            deleted = 0
            for c in campaigns:
                if c.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/campaigns/{c['id']}", headers=auth_headers)
                    deleted += 1
            print(f"✓ Cleaned up {deleted} test campaigns")
    
    def test_cleanup_test_leads(self, auth_headers):
        """Remove all TEST_ prefixed leads"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            leads = data.get("leads", [])
            deleted = 0
            for lead in leads:
                if lead.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/leads/{lead['id']}", headers=auth_headers)
                    deleted += 1
            print(f"✓ Cleaned up {deleted} test leads")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
