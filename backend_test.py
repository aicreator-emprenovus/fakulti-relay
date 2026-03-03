import requests
import sys
from datetime import datetime
import json
import time

class FacultyCRMAPITester:
    def __init__(self, base_url="https://maestro-ventas.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except json.JSONDecodeError:
                    return success, {"raw_content": response.content.decode()}
            else:
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Raw response: {response.text}")

            return success, {}

        except Exception as e:
            self.failed_tests.append(f"{name}: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # ========== AUTH TESTS ==========
    
    def test_login(self):
        """Test login with admin credentials"""
        success, response = self.run_test(
            "Login with admin@faculty.com",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@faculty.com", "password": "admin123"}
        )
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token received: {self.token[:20]}...")
            return True
        return False

    def test_auth_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get current user (/auth/me)",
            "GET",
            "auth/me",
            200
        )
        if success:
            print(f"   User: {response.get('name', 'N/A')} - {response.get('email', 'N/A')}")
        return success

    # ========== DASHBOARD TESTS ==========
    
    def test_dashboard_stats(self):
        """Test dashboard stats API"""
        success, response = self.run_test(
            "Dashboard stats",
            "GET",
            "dashboard/stats",
            200
        )
        if success:
            required_fields = ['total_leads', 'stages', 'total_sales']
            for field in required_fields:
                if field not in response:
                    print(f"   ⚠️ Missing required field: {field}")
                    self.failed_tests.append(f"Dashboard stats missing field: {field}")
                    return False
            print(f"   Total leads: {response['total_leads']}")
            print(f"   Total sales: ${response['total_sales']}")
            print(f"   Stages: {response['stages']}")
        return success

    # ========== LEADS TESTS ==========
    
    def test_get_leads(self):
        """Test get leads with filters"""
        success, response = self.run_test(
            "Get leads",
            "GET",
            "leads",
            200
        )
        if success:
            leads = response.get('leads', [])
            print(f"   Found {len(leads)} leads")
            if leads:
                print(f"   First lead: {leads[0].get('name', 'N/A')}")
        return success

    def test_create_lead(self):
        """Test create new lead"""
        test_lead = {
            "name": "Test User CRM",
            "whatsapp": "+593999888777",
            "city": "Quito",
            "email": "test@faculty.com",
            "product_interest": "Bombro",
            "source": "web",
            "notes": "Test lead from API testing",
            "funnel_stage": "nuevo"
        }
        success, response = self.run_test(
            "Create new lead",
            "POST",
            "leads",
            200,
            data=test_lead
        )
        if success:
            lead_id = response.get('id')
            print(f"   Created lead ID: {lead_id}")
            # Store for later tests
            self.test_lead_id = lead_id
        return success

    def test_update_lead(self):
        """Test update lead"""
        if not hasattr(self, 'test_lead_id'):
            print("   Skipping - no lead ID from create test")
            return False
            
        update_data = {
            "funnel_stage": "interesado",
            "notes": "Updated from API test"
        }
        success, response = self.run_test(
            "Update lead",
            "PUT",
            f"leads/{self.test_lead_id}",
            200,
            data=update_data
        )
        return success

    def test_get_lead_detail(self):
        """Test get single lead"""
        if not hasattr(self, 'test_lead_id'):
            print("   Skipping - no lead ID from create test")
            return False
            
        success, response = self.run_test(
            "Get lead detail",
            "GET",
            f"leads/{self.test_lead_id}",
            200
        )
        if success:
            print(f"   Lead: {response.get('name')} - Stage: {response.get('funnel_stage')}")
        return success

    # ========== PRODUCTS TESTS ==========
    
    def test_get_products(self):
        """Test get products - should have 4 seeded products"""
        success, response = self.run_test(
            "Get products",
            "GET",
            "products",
            200
        )
        if success:
            products = response if isinstance(response, list) else []
            print(f"   Found {len(products)} products")
            expected_products = ["Bombro", "Gomitas", "CBD Colageno", "Pitch Up"]
            for product in products:
                product_name = product.get('name', '')
                print(f"   - {product_name}: ${product.get('price', 0)}")
            
            # Check if we have the expected products
            if len(products) != 4:
                self.failed_tests.append(f"Expected 4 products, got {len(products)}")
        return success

    # ========== GAMES TESTS ==========
    
    def test_get_games_config(self):
        """Test get games config - should have 3 game configs"""
        success, response = self.run_test(
            "Get games config",
            "GET",
            "games/config",
            200
        )
        if success:
            games = response if isinstance(response, list) else []
            print(f"   Found {len(games)} game configs")
            expected_games = ["roulette", "mystery_box", "lucky_button"]
            for game in games:
                game_type = game.get('game_type', '')
                print(f"   - {game.get('name', 'N/A')} ({game_type})")
            
            if len(games) != 3:
                self.failed_tests.append(f"Expected 3 game configs, got {len(games)}")
        return success

    def test_game_public(self):
        """Test public game endpoint"""
        success, response = self.run_test(
            "Get public roulette config",
            "GET",
            "games/public/roulette",
            200
        )
        if success:
            # Should not have probabilities in public config
            if 'probabilities' in str(response):
                self.failed_tests.append("Public game config should not expose probabilities")
            print(f"   Game: {response.get('name', 'N/A')}")
            print(f"   Prizes: {len(response.get('prizes', []))}")
        return success

    def test_game_play(self):
        """Test playing a game"""
        game_data = {
            "game_type": "roulette",
            "whatsapp": "+593999999999",
            "name": "Test Player",
            "city": "Quito"
        }
        success, response = self.run_test(
            "Play roulette game",
            "POST",
            "games/play",
            200,
            data=game_data
        )
        if success:
            print(f"   Prize won: {response.get('prize', 'N/A')}")
            print(f"   Message: {response.get('message', 'N/A')}")
            if response.get('coupon'):
                print(f"   Coupon: {response.get('coupon')}")
        return success

    # ========== QUOTATIONS TESTS ==========
    
    def test_create_quotation(self):
        """Test create quotation"""
        # First, get a lead ID to use
        if not hasattr(self, 'test_lead_id'):
            print("   Skipping - no lead ID from create test")
            return False
            
        quotation_data = {
            "lead_id": self.test_lead_id,
            "items": [
                {"name": "Bombro - Bone Broth Hidrolizado", "quantity": 1, "price": 55.95},
                {"name": "Gomitas Melatonina", "quantity": 2, "price": 13.25}
            ],
            "notes": "Test quotation"
        }
        success, response = self.run_test(
            "Create quotation",
            "POST",
            "quotations",
            200,
            data=quotation_data
        )
        if success:
            quotation_id = response.get('id')
            print(f"   Quotation ID: {quotation_id}")
            print(f"   Total: ${response.get('total', 0)}")
            self.quotation_id = quotation_id
        return success

    def test_get_quotation_pdf(self):
        """Test quotation PDF generation"""
        if not hasattr(self, 'quotation_id'):
            print("   Skipping - no quotation ID from create test")
            return False
            
        # For PDF endpoint, we expect a different content type
        success, response = self.run_test(
            "Get quotation PDF",
            "GET",
            f"quotations/{self.quotation_id}/pdf",
            200
        )
        if success:
            print("   PDF generated successfully")
        return success

    # ========== LOYALTY TESTS ==========
    
    def test_loyalty_sequences(self):
        """Test loyalty sequences"""
        success, response = self.run_test(
            "Get loyalty sequences",
            "GET",
            "loyalty/sequences",
            200
        )
        if success:
            sequences = response if isinstance(response, list) else []
            print(f"   Found {len(sequences)} loyalty sequences")
        return success

    def test_create_loyalty_sequence(self):
        """Test create loyalty sequence"""
        sequence_data = {
            "product_id": "test-product-id",
            "product_name": "Test Product",
            "messages": [
                {"day": 1, "message": "Gracias por tu compra!", "type": "welcome"},
                {"day": 30, "message": "¿Cómo te ha funcionado el producto?", "type": "follow_up"}
            ],
            "active": True
        }
        success, response = self.run_test(
            "Create loyalty sequence",
            "POST",
            "loyalty/sequences",
            200,
            data=sequence_data
        )
        if success:
            print(f"   Sequence ID: {response.get('id')}")
        return success

    # ========== BULK TESTS ==========
    
    def test_bulk_download(self):
        """Test bulk download"""
        success, response = self.run_test(
            "Bulk download all leads",
            "GET",
            "bulk/download?download_type=all",
            200
        )
        if success:
            print("   Excel file generated successfully")
        return success

    # ========== CHAT TESTS ==========
    
    def test_chat_message(self):
        """Test AI chat functionality"""
        chat_data = {
            "session_id": f"test_session_{int(time.time())}",
            "message": "Hola, ¿qué productos tienen disponibles?",
            "lead_id": getattr(self, 'test_lead_id', None)
        }
        success, response = self.run_test(
            "Send chat message",
            "POST",
            "chat/message",
            200,
            data=chat_data
        )
        if success:
            ai_response = response.get('response', '')
            print(f"   AI Response: {ai_response[:100]}...")
            self.chat_session_id = response.get('session_id')
        return success

    def test_chat_sessions(self):
        """Test get chat sessions"""
        success, response = self.run_test(
            "Get chat sessions",
            "GET",
            "chat/sessions",
            200
        )
        if success:
            sessions = response if isinstance(response, list) else []
            print(f"   Found {len(sessions)} chat sessions")
        return success

    # ========== CLEANUP TESTS ==========
    
    def test_delete_lead(self):
        """Test delete the test lead"""
        if not hasattr(self, 'test_lead_id'):
            print("   Skipping - no lead ID to delete")
            return False
            
        success, response = self.run_test(
            "Delete test lead",
            "DELETE",
            f"leads/{self.test_lead_id}",
            200
        )
        return success

def main():
    print("🚀 Starting Faculty CRM API Testing...")
    print("=" * 50)
    
    tester = FacultyCRMAPITester()
    
    # Authentication Tests
    print("\n📋 AUTHENTICATION TESTS")
    if not tester.test_login():
        print("❌ Login failed - stopping all tests")
        return 1
    
    tester.test_auth_me()
    
    # Dashboard Tests  
    print("\n📊 DASHBOARD TESTS")
    tester.test_dashboard_stats()
    
    # Leads Tests
    print("\n👥 LEADS TESTS")
    tester.test_get_leads()
    tester.test_create_lead()
    tester.test_update_lead()
    tester.test_get_lead_detail()
    
    # Products Tests
    print("\n🛍️ PRODUCTS TESTS")
    tester.test_get_products()
    
    # Games Tests
    print("\n🎮 GAMES TESTS")
    tester.test_get_games_config()
    tester.test_game_public()
    tester.test_game_play()
    
    # Quotations Tests
    print("\n📄 QUOTATIONS TESTS")
    tester.test_create_quotation()
    tester.test_get_quotation_pdf()
    
    # Loyalty Tests
    print("\n❤️ LOYALTY TESTS")
    tester.test_loyalty_sequences()
    tester.test_create_loyalty_sequence()
    
    # Bulk Tests
    print("\n📤 BULK TESTS")
    tester.test_bulk_download()
    
    # Chat Tests
    print("\n💬 CHAT AI TESTS")
    tester.test_chat_message()
    tester.test_chat_sessions()
    
    # Cleanup
    print("\n🧹 CLEANUP TESTS")
    tester.test_delete_lead()
    
    # Final Results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for i, test in enumerate(tester.failed_tests, 1):
            print(f"{i}. {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())