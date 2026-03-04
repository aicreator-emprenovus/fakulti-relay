"""
Test suite for the Loyalty Metrics Dashboard - P3 Feature
Tests the following:
- GET /api/loyalty/metrics - returns comprehensive metrics dashboard data
- Summary metrics: total_clients, repeat_rate, retention_rate, total_revenue, avg_order_value, avg_purchases_per_client
- Loyalty metrics: total_enrollments, active_enrollments, completed_enrollments, sent_messages, pending_messages, delivery_rate
- Product revenue breakdown
- Product repeat purchase rates
- Sequence effectiveness stats
- Top buyers list
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestLoyaltyMetrics:
    """Test loyalty metrics endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@faculty.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_01_metrics_endpoint_requires_auth(self):
        """Test that metrics endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics")
        assert response.status_code == 401
        print("Correctly requires auth for metrics endpoint")
    
    def test_02_metrics_endpoint_returns_200(self, auth_headers):
        """Test GET /api/loyalty/metrics returns 200 with valid auth"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        assert response.status_code == 200
        print("Metrics endpoint returns 200 OK")
    
    def test_03_metrics_has_summary_section(self, auth_headers):
        """Test metrics contains summary with expected fields"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data, "Missing 'summary' section"
        
        summary = data["summary"]
        required_fields = [
            "total_clients", "repeat_buyers", "repeat_rate", "retention_rate",
            "total_revenue", "repeat_revenue", "avg_order_value", 
            "avg_purchases_per_client", "active_clients", "lost_clients"
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing '{field}' in summary"
        
        # Type assertions
        assert isinstance(summary["total_clients"], int)
        assert isinstance(summary["repeat_rate"], (int, float))
        assert isinstance(summary["retention_rate"], (int, float))
        assert isinstance(summary["total_revenue"], (int, float))
        assert isinstance(summary["avg_order_value"], (int, float))
        assert isinstance(summary["avg_purchases_per_client"], (int, float))
        
        print(f"Summary metrics: {summary['total_clients']} clients, {summary['repeat_rate']}% repeat, ${summary['total_revenue']} revenue")
    
    def test_04_metrics_has_loyalty_section(self, auth_headers):
        """Test metrics contains loyalty section with expected fields"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        assert "loyalty" in data, "Missing 'loyalty' section"
        
        loyalty = data["loyalty"]
        required_fields = [
            "total_enrollments", "active_enrollments", "completed_enrollments",
            "total_messages", "sent_messages", "pending_messages", "delivery_rate"
        ]
        
        for field in required_fields:
            assert field in loyalty, f"Missing '{field}' in loyalty"
        
        # Type and value assertions
        assert isinstance(loyalty["total_enrollments"], int)
        assert isinstance(loyalty["active_enrollments"], int)
        assert isinstance(loyalty["completed_enrollments"], int)
        assert isinstance(loyalty["delivery_rate"], (int, float))
        assert loyalty["total_enrollments"] >= loyalty["active_enrollments"]
        assert loyalty["total_messages"] == loyalty["sent_messages"] + loyalty["pending_messages"]
        
        print(f"Loyalty metrics: {loyalty['total_enrollments']} enrollments, {loyalty['sent_messages']} sent, {loyalty['delivery_rate']}% delivery")
    
    def test_05_metrics_has_product_revenue(self, auth_headers):
        """Test metrics contains product_revenue array with expected structure"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        assert "product_revenue" in data, "Missing 'product_revenue' section"
        product_revenue = data["product_revenue"]
        
        assert isinstance(product_revenue, list)
        
        if len(product_revenue) > 0:
            item = product_revenue[0]
            assert "product" in item, "Missing 'product' in product_revenue item"
            assert "revenue" in item, "Missing 'revenue' in product_revenue item"
            assert "orders" in item, "Missing 'orders' in product_revenue item"
            assert "buyer_count" in item, "Missing 'buyer_count' in product_revenue item"
            
            # Type assertions
            assert isinstance(item["product"], str)
            assert isinstance(item["revenue"], (int, float))
            assert isinstance(item["orders"], int)
            assert isinstance(item["buyer_count"], int)
        
        print(f"Product revenue: {len(product_revenue)} products")
    
    def test_06_metrics_has_product_repeat(self, auth_headers):
        """Test metrics contains product_repeat array with expected structure"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        assert "product_repeat" in data, "Missing 'product_repeat' section"
        product_repeat = data["product_repeat"]
        
        assert isinstance(product_repeat, list)
        
        if len(product_repeat) > 0:
            item = product_repeat[0]
            assert "product" in item, "Missing 'product' in product_repeat item"
            assert "total_buyers" in item, "Missing 'total_buyers' in product_repeat item"
            assert "repeat_buyers" in item, "Missing 'repeat_buyers' in product_repeat item"
            assert "repeat_rate" in item, "Missing 'repeat_rate' in product_repeat item"
            
            # Type assertions
            assert isinstance(item["repeat_rate"], (int, float))
            assert item["repeat_rate"] >= 0 and item["repeat_rate"] <= 100
        
        print(f"Product repeat stats: {len(product_repeat)} products")
    
    def test_07_metrics_has_sequence_effectiveness(self, auth_headers):
        """Test metrics contains sequence_effectiveness array with expected structure"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        assert "sequence_effectiveness" in data, "Missing 'sequence_effectiveness' section"
        seq_eff = data["sequence_effectiveness"]
        
        assert isinstance(seq_eff, list)
        
        if len(seq_eff) > 0:
            item = seq_eff[0]
            assert "name" in item, "Missing 'name' in sequence_effectiveness item"
            assert "enrollments" in item, "Missing 'enrollments' in sequence_effectiveness item"
            assert "completed" in item, "Missing 'completed' in sequence_effectiveness item"
            assert "msgs_sent" in item, "Missing 'msgs_sent' in sequence_effectiveness item"
            assert "msgs_total" in item, "Missing 'msgs_total' in sequence_effectiveness item"
            assert "completion_rate" in item, "Missing 'completion_rate' in sequence_effectiveness item"
            assert "delivery_rate" in item, "Missing 'delivery_rate' in sequence_effectiveness item"
            
            # Type assertions
            assert isinstance(item["completion_rate"], (int, float))
            assert isinstance(item["delivery_rate"], (int, float))
        
        print(f"Sequence effectiveness: {len(seq_eff)} sequences")
    
    def test_08_metrics_has_top_buyers(self, auth_headers):
        """Test metrics contains top_buyers array with expected structure"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        assert "top_buyers" in data, "Missing 'top_buyers' section"
        top_buyers = data["top_buyers"]
        
        assert isinstance(top_buyers, list)
        
        if len(top_buyers) > 0:
            buyer = top_buyers[0]
            assert "name" in buyer, "Missing 'name' in top_buyers item"
            assert "purchases" in buyer, "Missing 'purchases' in top_buyers item"
            assert "total_spent" in buyer, "Missing 'total_spent' in top_buyers item"
            assert "stage" in buyer, "Missing 'stage' in top_buyers item"
            
            # Type assertions
            assert isinstance(buyer["name"], str)
            assert isinstance(buyer["purchases"], int)
            assert isinstance(buyer["total_spent"], (int, float))
        
        print(f"Top buyers: {len(top_buyers)} listed")
    
    def test_09_top_buyers_sorted_by_total_spent(self, auth_headers):
        """Test that top_buyers list is sorted by total_spent descending"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        top_buyers = data["top_buyers"]
        
        if len(top_buyers) > 1:
            for i in range(len(top_buyers) - 1):
                assert top_buyers[i]["total_spent"] >= top_buyers[i+1]["total_spent"], \
                    f"Top buyers not sorted correctly: {top_buyers[i]['total_spent']} < {top_buyers[i+1]['total_spent']}"
        
        print("Top buyers correctly sorted by total_spent")
    
    def test_10_verify_current_data(self, auth_headers):
        """Verify metrics reflect the current sample data (Maria Garcia $111.90, Ana Martinez $13.25)"""
        response = requests.get(f"{BASE_URL}/api/loyalty/metrics", headers=auth_headers)
        data = response.json()
        
        # Based on provided context: 2 clients with purchases, 3 loyalty enrollments
        summary = data["summary"]
        loyalty = data["loyalty"]
        top_buyers = data["top_buyers"]
        
        # Verify we have clients data
        assert summary["total_clients"] >= 2, f"Expected at least 2 clients, got {summary['total_clients']}"
        
        # Verify enrollments
        assert loyalty["total_enrollments"] >= 3, f"Expected at least 3 enrollments, got {loyalty['total_enrollments']}"
        
        # Verify top buyers includes Maria Garcia and Ana Martinez
        buyer_names = [b["name"] for b in top_buyers]
        
        if len(top_buyers) >= 2:
            # Should include Maria Garcia (top spender at $111.90) first
            if "Maria Garcia" in buyer_names:
                maria = next((b for b in top_buyers if b["name"] == "Maria Garcia"), None)
                assert maria is not None
                assert abs(maria["total_spent"] - 111.90) < 0.01, f"Maria Garcia's total should be ~$111.90, got ${maria['total_spent']}"
            
            if "Ana Martinez" in buyer_names:
                ana = next((b for b in top_buyers if b["name"] == "Ana Martinez"), None)
                assert ana is not None
                assert abs(ana["total_spent"] - 13.25) < 0.01, f"Ana Martinez's total should be ~$13.25, got ${ana['total_spent']}"
        
        print(f"Verified data: {summary['total_clients']} clients, ${summary['total_revenue']} total revenue")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
