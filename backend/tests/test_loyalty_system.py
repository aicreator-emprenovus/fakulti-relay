"""
Test suite for the Loyalty System - P2 Feature
Tests the following features:
- POST /api/loyalty/sequences - create new sequence with product and messages
- GET /api/loyalty/sequences - list all sequences
- DELETE /api/loyalty/sequences/{id} - delete a sequence
- POST /api/loyalty/enroll?lead_id=X&sequence_id=Y - enroll lead in sequence
- GET /api/loyalty/enrollments - list enrollments with progress
- DELETE /api/loyalty/enrollments/{id} - delete enrollment
- POST /api/loyalty/process - process pending loyalty messages
- Auto-enrollment on purchase
- Duplicate enrollment prevention
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLoyaltySystemSetup:
    """Setup tests - ensure auth and get necessary data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_01_login_success(self):
        """Test login to get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"Login successful: {data['user']['email']}")


class TestLoyaltySequences:
    """Test loyalty sequences CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def products(self, auth_headers):
        """Get available products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        return response.json()
    
    def test_02_get_sequences(self, auth_headers):
        """Test GET /api/loyalty/sequences - list all sequences"""
        response = requests.get(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} existing sequences")
    
    def test_03_create_sequence(self, auth_headers, products):
        """Test POST /api/loyalty/sequences - create new sequence"""
        assert len(products) > 0, "No products available for testing"
        product = products[0]
        
        sequence_data = {
            "product_id": product["id"],
            "product_name": product["name"],
            "messages": [
                {"day": 0, "content": "TEST_MSG: Gracias por tu compra! Esperamos que disfrutes tu producto.", "active": True},
                {"day": 3, "content": "TEST_MSG: Como te va con el producto? Tienes alguna pregunta?", "active": True},
                {"day": 7, "content": "TEST_MSG: Recuerda tomar tu suplemento diariamente para mejores resultados.", "active": True}
            ],
            "active": True
        }
        
        response = requests.post(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers, json=sequence_data)
        assert response.status_code == 200, f"Create sequence failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["product_id"] == product["id"]
        assert data["product_name"] == product["name"]
        assert len(data["messages"]) == 3
        assert data["active"] == True
        
        # Store for later tests
        TestLoyaltySequences.created_sequence_id = data["id"]
        print(f"Created sequence: {data['id']} for product: {data['product_name']}")
        return data
    
    def test_04_verify_sequence_created(self, auth_headers):
        """Test GET to verify the created sequence exists"""
        response = requests.get(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers)
        assert response.status_code == 200
        
        sequences = response.json()
        created_id = getattr(TestLoyaltySequences, 'created_sequence_id', None)
        assert created_id is not None, "No sequence was created in previous test"
        
        found = any(seq["id"] == created_id for seq in sequences)
        assert found, f"Created sequence {created_id} not found in sequences list"
        print(f"Verified sequence {created_id} exists in list")
    
    def test_05_delete_sequence(self, auth_headers):
        """Test DELETE /api/loyalty/sequences/{id} - delete a sequence"""
        created_id = getattr(TestLoyaltySequences, 'created_sequence_id', None)
        assert created_id is not None, "No sequence to delete"
        
        response = requests.delete(f"{BASE_URL}/api/loyalty/sequences/{created_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        print(f"Deleted sequence: {created_id}")
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers)
        sequences = response.json()
        found = any(seq["id"] == created_id for seq in sequences)
        assert not found, "Sequence still exists after deletion"


class TestLoyaltyEnrollments:
    """Test loyalty enrollment operations"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_sequence(self, auth_headers):
        """Create a test sequence for enrollment tests"""
        # Get first product
        products_response = requests.get(f"{BASE_URL}/api/products")
        products = products_response.json()
        product = products[0]
        
        sequence_data = {
            "product_id": product["id"],
            "product_name": f"TEST_ENROLLMENT_{product['name']}",
            "messages": [
                {"day": 0, "content": "TEST_ENROLL_MSG: Dia 0 - Gracias por comprar!", "active": True},
                {"day": 1, "content": "TEST_ENROLL_MSG: Dia 1 - Como te va?", "active": True},
                {"day": 3, "content": "TEST_ENROLL_MSG: Dia 3 - Recordatorio", "active": True}
            ],
            "active": True
        }
        
        response = requests.post(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers, json=sequence_data)
        assert response.status_code == 200
        sequence = response.json()
        print(f"Created test sequence: {sequence['id']}")
        return sequence
    
    @pytest.fixture(scope="class")
    def test_lead(self, auth_headers):
        """Create a test lead for enrollment tests"""
        lead_data = {
            "name": f"TEST_ENROLL_Lead_{uuid.uuid4().hex[:6]}",
            "whatsapp": f"+593TEST{uuid.uuid4().hex[:8]}",
            "city": "Quito",
            "source": "web",
            "funnel_stage": "cliente_nuevo"
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json=lead_data)
        assert response.status_code == 200
        lead = response.json()
        print(f"Created test lead: {lead['id']} - {lead['name']}")
        return lead
    
    def test_06_get_enrollments(self, auth_headers):
        """Test GET /api/loyalty/enrollments - list enrollments"""
        response = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} existing enrollments")
    
    def test_07_enroll_lead(self, auth_headers, test_sequence, test_lead):
        """Test POST /api/loyalty/enroll?lead_id=X&sequence_id=Y - enroll lead"""
        response = requests.post(
            f"{BASE_URL}/api/loyalty/enroll?lead_id={test_lead['id']}&sequence_id={test_sequence['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Enroll failed: {response.text}"
        
        data = response.json()
        assert data["lead_id"] == test_lead["id"]
        assert data["sequence_id"] == test_sequence["id"]
        assert data["status"] == "activo"
        assert "messages" in data
        assert len(data["messages"]) == 3  # 3 messages in our test sequence
        
        # All messages should be pending initially
        for msg in data["messages"]:
            assert msg["status"] == "pendiente"
            assert "scheduled_date" in msg
        
        TestLoyaltyEnrollments.created_enrollment_id = data["id"]
        print(f"Enrolled lead {test_lead['name']} in sequence {test_sequence['product_name']}, enrollment id: {data['id']}")
        return data
    
    def test_08_verify_enrollment_in_list(self, auth_headers):
        """Verify enrollment appears in enrollments list with progress data"""
        response = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers)
        assert response.status_code == 200
        
        enrollments = response.json()
        enrollment_id = getattr(TestLoyaltyEnrollments, 'created_enrollment_id', None)
        assert enrollment_id is not None
        
        enrollment = next((e for e in enrollments if e["id"] == enrollment_id), None)
        assert enrollment is not None, f"Enrollment {enrollment_id} not found in list"
        
        assert "lead_name" in enrollment
        assert "lead_whatsapp" in enrollment
        assert "sequence_name" in enrollment
        assert "messages" in enrollment
        print(f"Verified enrollment in list: {enrollment['lead_name']} -> {enrollment['sequence_name']}")
    
    def test_09_duplicate_enrollment_prevention(self, auth_headers, test_sequence, test_lead):
        """Test that enrolling the same lead twice returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/loyalty/enroll?lead_id={test_lead['id']}&sequence_id={test_sequence['id']}",
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for duplicate enrollment, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        print(f"Duplicate enrollment correctly rejected: {data['detail']}")
    
    def test_10_delete_enrollment(self, auth_headers):
        """Test DELETE /api/loyalty/enrollments/{id} - delete enrollment"""
        enrollment_id = getattr(TestLoyaltyEnrollments, 'created_enrollment_id', None)
        assert enrollment_id is not None
        
        response = requests.delete(f"{BASE_URL}/api/loyalty/enrollments/{enrollment_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        print(f"Deleted enrollment: {enrollment_id}")
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers)
        enrollments = response.json()
        found = any(e["id"] == enrollment_id for e in enrollments)
        assert not found, "Enrollment still exists after deletion"


class TestLoyaltyProcessing:
    """Test message processing functionality"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def process_test_setup(self, auth_headers):
        """Create sequence and enrollment for processing test"""
        # Get first product
        products_response = requests.get(f"{BASE_URL}/api/products")
        products = products_response.json()
        product = products[0]
        
        # Create sequence with day 0 message (should be processed immediately)
        sequence_data = {
            "product_id": product["id"],
            "product_name": f"TEST_PROCESS_{product['name']}",
            "messages": [
                {"day": 0, "content": "TEST_PROCESS: Immediate message - day 0", "active": True},
                {"day": 30, "content": "TEST_PROCESS: Future message - day 30", "active": True}
            ],
            "active": True
        }
        
        seq_response = requests.post(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers, json=sequence_data)
        assert seq_response.status_code == 200
        sequence = seq_response.json()
        
        # Create test lead
        lead_data = {
            "name": f"TEST_PROCESS_Lead_{uuid.uuid4().hex[:6]}",
            "whatsapp": f"+593TESTPROC{uuid.uuid4().hex[:6]}",
            "city": "Guayaquil",
            "source": "web",
            "funnel_stage": "cliente_nuevo"
        }
        lead_response = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json=lead_data)
        assert lead_response.status_code == 200
        lead = lead_response.json()
        
        # Enroll lead
        enroll_response = requests.post(
            f"{BASE_URL}/api/loyalty/enroll?lead_id={lead['id']}&sequence_id={sequence['id']}",
            headers=auth_headers
        )
        assert enroll_response.status_code == 200
        enrollment = enroll_response.json()
        
        print(f"Test setup complete - sequence: {sequence['id']}, lead: {lead['id']}, enrollment: {enrollment['id']}")
        return {"sequence": sequence, "lead": lead, "enrollment": enrollment}
    
    def test_11_process_pending_messages(self, auth_headers, process_test_setup):
        """Test POST /api/loyalty/process - process pending messages"""
        response = requests.post(f"{BASE_URL}/api/loyalty/process", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "processed" in data
        assert "message" in data
        print(f"Processed messages: {data['processed']} - {data['message']}")
    
    def test_12_verify_messages_processed(self, auth_headers, process_test_setup):
        """Verify day 0 message was processed (marked as enviado)"""
        enrollment_id = process_test_setup["enrollment"]["id"]
        
        response = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers)
        enrollments = response.json()
        
        enrollment = next((e for e in enrollments if e["id"] == enrollment_id), None)
        assert enrollment is not None
        
        # Day 0 message should be 'enviado', day 30 should be 'pendiente'
        messages = enrollment["messages"]
        day_0_msg = next((m for m in messages if m["day"] == 0), None)
        day_30_msg = next((m for m in messages if m["day"] == 30), None)
        
        assert day_0_msg is not None, "Day 0 message not found"
        assert day_0_msg["status"] == "enviado", f"Day 0 message should be 'enviado', got '{day_0_msg['status']}'"
        
        assert day_30_msg is not None, "Day 30 message not found"
        assert day_30_msg["status"] == "pendiente", f"Day 30 message should still be 'pendiente', got '{day_30_msg['status']}'"
        
        print(f"Verified: Day 0 = {day_0_msg['status']}, Day 30 = {day_30_msg['status']}")
    
    def test_13_cleanup_process_test(self, auth_headers, process_test_setup):
        """Clean up test data"""
        enrollment_id = process_test_setup["enrollment"]["id"]
        sequence_id = process_test_setup["sequence"]["id"]
        lead_id = process_test_setup["lead"]["id"]
        
        # Delete enrollment
        requests.delete(f"{BASE_URL}/api/loyalty/enrollments/{enrollment_id}", headers=auth_headers)
        # Delete sequence
        requests.delete(f"{BASE_URL}/api/loyalty/sequences/{sequence_id}", headers=auth_headers)
        # Delete lead
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        
        print(f"Cleaned up test data: enrollment {enrollment_id}, sequence {sequence_id}, lead {lead_id}")


class TestAutoEnrollmentOnPurchase:
    """Test auto-enrollment when a lead makes a purchase"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def auto_enroll_setup(self, auth_headers):
        """Create sequence and lead for auto-enrollment test"""
        # Get first product
        products_response = requests.get(f"{BASE_URL}/api/products")
        products = products_response.json()
        product = products[0]
        
        # Create ACTIVE sequence for this product
        sequence_data = {
            "product_id": product["id"],
            "product_name": f"AUTO_ENROLL_{product['name']}",
            "messages": [
                {"day": 0, "content": "AUTO_ENROLL: Gracias por tu compra!", "active": True},
                {"day": 7, "content": "AUTO_ENROLL: Una semana despues...", "active": True}
            ],
            "active": True  # Must be active for auto-enrollment
        }
        
        seq_response = requests.post(f"{BASE_URL}/api/loyalty/sequences", headers=auth_headers, json=sequence_data)
        assert seq_response.status_code == 200
        sequence = seq_response.json()
        
        # Create test lead (NOT enrolled yet)
        lead_data = {
            "name": f"AUTO_ENROLL_Lead_{uuid.uuid4().hex[:6]}",
            "whatsapp": f"+593AUTOENROLL{uuid.uuid4().hex[:6]}",
            "city": "Cuenca",
            "source": "web",
            "funnel_stage": "interesado"  # Start as interesado
        }
        lead_response = requests.post(f"{BASE_URL}/api/leads", headers=auth_headers, json=lead_data)
        assert lead_response.status_code == 200
        lead = lead_response.json()
        
        print(f"Auto-enroll setup - Product: {product['id']}, Sequence: {sequence['id']}, Lead: {lead['id']}")
        return {"product": product, "sequence": sequence, "lead": lead}
    
    def test_14_auto_enroll_on_purchase(self, auth_headers, auto_enroll_setup):
        """Test POST /api/leads/{lead_id}/purchase auto-enrolls lead in loyalty sequence"""
        lead = auto_enroll_setup["lead"]
        product = auto_enroll_setup["product"]
        sequence = auto_enroll_setup["sequence"]
        
        # Make a purchase
        purchase_data = {
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": 1,
            "price": product["price"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/leads/{lead['id']}/purchase",
            headers=auth_headers,
            json=purchase_data
        )
        assert response.status_code == 200, f"Purchase failed: {response.text}"
        
        updated_lead = response.json()
        assert updated_lead["funnel_stage"] == "cliente_nuevo"
        assert len(updated_lead["purchase_history"]) > 0
        print(f"Purchase recorded for lead {lead['name']}")
        
        # Verify auto-enrollment happened
        enrollments_response = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers)
        enrollments = enrollments_response.json()
        
        # Find enrollment for this lead - auto-enrollment picks the FIRST active sequence for the product
        # (may not be the exact sequence we created, but any active sequence for this product)
        enrollment = next(
            (e for e in enrollments if e["lead_id"] == lead["id"]),
            None
        )
        
        assert enrollment is not None, f"Auto-enrollment did not happen! Lead {lead['id']} not enrolled in any sequence"
        assert enrollment["status"] == "activo"
        assert len(enrollment["messages"]) >= 1  # Should have at least 1 message
        
        TestAutoEnrollmentOnPurchase.auto_enrollment_id = enrollment["id"]
        print(f"Auto-enrollment verified! Lead {lead['name']} enrolled in sequence: {enrollment['sequence_name']}")
    
    def test_15_no_duplicate_auto_enroll(self, auth_headers, auto_enroll_setup):
        """Test that second purchase doesn't create duplicate enrollment"""
        lead = auto_enroll_setup["lead"]
        product = auto_enroll_setup["product"]
        sequence = auto_enroll_setup["sequence"]
        
        # Get current enrollment count for this lead/sequence
        enrollments_before = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers).json()
        count_before = sum(1 for e in enrollments_before if e["lead_id"] == lead["id"] and e["sequence_id"] == sequence["id"])
        
        # Make another purchase
        purchase_data = {
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": 2,
            "price": product["price"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/leads/{lead['id']}/purchase",
            headers=auth_headers,
            json=purchase_data
        )
        assert response.status_code == 200
        
        # Verify no duplicate enrollment
        enrollments_after = requests.get(f"{BASE_URL}/api/loyalty/enrollments", headers=auth_headers).json()
        count_after = sum(1 for e in enrollments_after if e["lead_id"] == lead["id"] and e["sequence_id"] == sequence["id"])
        
        assert count_after == count_before, f"Duplicate enrollment created! Before: {count_before}, After: {count_after}"
        print("Verified: No duplicate auto-enrollment on second purchase")
    
    def test_16_cleanup_auto_enroll_test(self, auth_headers, auto_enroll_setup):
        """Clean up test data"""
        sequence_id = auto_enroll_setup["sequence"]["id"]
        lead_id = auto_enroll_setup["lead"]["id"]
        enrollment_id = getattr(TestAutoEnrollmentOnPurchase, 'auto_enrollment_id', None)
        
        # Delete enrollment
        if enrollment_id:
            requests.delete(f"{BASE_URL}/api/loyalty/enrollments/{enrollment_id}", headers=auth_headers)
        
        # Delete sequence
        requests.delete(f"{BASE_URL}/api/loyalty/sequences/{sequence_id}", headers=auth_headers)
        
        # Delete lead
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        
        print(f"Cleaned up auto-enroll test data")


class TestLoyaltyErrorHandling:
    """Test error handling in loyalty system"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_17_enroll_nonexistent_lead(self, auth_headers):
        """Test enrolling non-existent lead returns 404"""
        fake_lead_id = str(uuid.uuid4())
        fake_sequence_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/loyalty/enroll?lead_id={fake_lead_id}&sequence_id={fake_sequence_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent lead")
    
    def test_18_delete_nonexistent_enrollment(self, auth_headers):
        """Test deleting non-existent enrollment returns 404"""
        fake_enrollment_id = str(uuid.uuid4())
        
        response = requests.delete(
            f"{BASE_URL}/api/loyalty/enrollments/{fake_enrollment_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent enrollment")
    
    def test_19_auth_required_sequences(self):
        """Test that sequences endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/loyalty/sequences")
        assert response.status_code == 401
        print("Correctly requires auth for sequences endpoint")
    
    def test_20_auth_required_enrollments(self):
        """Test that enrollments endpoint requires auth"""
        response = requests.get(f"{BASE_URL}/api/loyalty/enrollments")
        assert response.status_code == 401
        print("Correctly requires auth for enrollments endpoint")
    
    def test_21_auth_required_process(self):
        """Test that process endpoint requires auth"""
        response = requests.post(f"{BASE_URL}/api/loyalty/process")
        assert response.status_code == 401
        print("Correctly requires auth for process endpoint")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
