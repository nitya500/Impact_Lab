"""
IMPACT LAB - Comprehensive Verification & Test Suite
Problem-to-Impact Platform
===================================================
Automated test suite verifying:
- Database schema, relationships, and SQLite persistence
- NLP vectorization, tokenization, stopword removal, and TF-IDF Cosine Similarity
- MCDA Feasibility scoring algorithm and explainability
- Civic / Government portal detection rules
- Flask routes (HTML templates, redirects, forms, flash alerts)
- REST API backward compatibility endpoints
- Edge cases (empty inputs, non-existent problem ID, zero match queries)
"""

import os
import unittest
import json
import sqlite3

# Import application components
import database
import nlp_engine
import feasibility_engine
import gov_portal
import ai_suggester
from app import app


class ImpactLabTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test client and ensure database initialization."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        cls.client = app.test_client()
        database.init_db()

    # --------------------------------------------------------------------------
    # 1. Database & Persistence Tests
    # --------------------------------------------------------------------------
    def test_database_initialization_and_seed_data(self):
        """Verify tables exist and seed data is properly populated."""
        conn = database.get_db_connection()
        
        # Verify problem records
        probs = conn.execute("SELECT * FROM problems").fetchall()
        self.assertGreaterEqual(len(probs), 4, "Should have at least 4 seed problems.")
        
        # Verify solutions exist
        sols = conn.execute("SELECT * FROM solutions").fetchall()
        self.assertGreaterEqual(len(sols), 5, "Should have at least 5 seed solutions.")
        
        # Verify helpers exist
        helpers = conn.execute("SELECT * FROM helpers").fetchall()
        self.assertGreaterEqual(len(helpers), 4, "Should have at least 4 seed helpers.")
        
        conn.close()

    def test_database_platform_statistics(self):
        """Verify platform statistics calculation returns non-zero counts."""
        stats = database.get_platform_statistics()
        self.assertIn("total_problems", stats)
        self.assertIn("total_solutions", stats)
        self.assertIn("tested_solutions", stats)
        self.assertIn("registered_helpers", stats)
        self.assertGreater(stats["total_problems"], 0)
        self.assertGreater(stats["total_solutions"], 0)

    # --------------------------------------------------------------------------
    # 2. NLP Engine & TF-IDF Cosine Similarity Tests
    # --------------------------------------------------------------------------
    def test_nlp_tokenization_and_stopwords(self):
        """Verify tokenization removes punctuation and stopwords."""
        raw = "This is a very important customer support query with 100% automation!"
        tokens = nlp_engine.tokenize(raw)
        self.assertIn("support", tokens)
        self.assertIn("customer", tokens)
        
        clean = nlp_engine.remove_stopwords(tokens)
        self.assertNotIn("this", clean)
        self.assertNotIn("is", clean)
        self.assertNotIn("a", clean)
        self.assertNotIn("very", clean)
        self.assertIn("customer", clean)
        self.assertIn("support", clean)

    def test_nlp_keyword_extraction(self):
        """Verify meaningful keywords extraction from problem text."""
        text = "Repeated queries regarding hostel mess timings, meal distribution, and student queue delay."
        kws = nlp_engine.extract_keywords(text, top_n=5)
        self.assertIsInstance(kws, list)
        self.assertGreaterEqual(len(kws), 3)

    def test_nlp_tfidf_cosine_similarity(self):
        """Verify TF-IDF vectorization and cosine similarity mathematics."""
        docs = [
            "automated customer support ticketing system with knowledge base",
            "stormwater drainage grate mesh filter for municipal flooding",
            "hostel cafeteria food donation routing and surplus meal logistics"
        ]
        vectorizer = nlp_engine.TextVectorizer(docs)
        
        vec1 = vectorizer.transform("customer support ticket helpdesk")
        vec2 = vectorizer.transform("automated customer support ticketing system")
        vec3 = vectorizer.transform("urban drainage flood filter")
        
        sim_high = nlp_engine.TextVectorizer.cosine_similarity(vec1, vec2)
        sim_low = nlp_engine.TextVectorizer.cosine_similarity(vec1, vec3)
        
        self.assertGreater(sim_high, sim_low, "Support query must match support doc much higher than drainage doc")
        self.assertGreater(sim_high, 0.30)
        self.assertEqual(sim_low, 0.0)

    def test_nlp_solution_ranking_explainability(self):
        """Verify rank_matching_solutions returns explainable rationale and scores."""
        query = "customer support response time queries FAQ"
        all_sols = database.get_all_solutions()
        ranked = nlp_engine.rank_matching_solutions(query, all_sols)
        
        self.assertGreater(len(ranked), 0)
        top = ranked[0]
        self.assertIn("relevance_score", top)
        self.assertIn("matched_keywords", top)
        self.assertIn("explanation", top)
        self.assertIn("is_verified", top)
        self.assertFalse(top["is_verified"], "Must be marked as unverified suggestion")

    def test_nlp_empty_query_edge_case(self):
        """Verify ranking handles empty query gracefully without crashing."""
        res = nlp_engine.rank_matching_solutions("", database.get_all_solutions())
        self.assertEqual(res, [])

    # --------------------------------------------------------------------------
    # 3. MCDA Feasibility Engine Tests
    # --------------------------------------------------------------------------
    def test_feasibility_scoring_calculation(self):
        """Verify multi-criteria weighted scoring algorithm and penalty."""
        inputs = {
            "expected_benefit": 9,        # 9/10 * 25 = 22.5
            "technical_feasibility": 8,   # 8/10 * 20 = 16.0
            "cost_fit": 9,                # 9/10 * 15 = 13.5
            "implementation_time": 9,     # 9/10 * 15 = 13.5
            "resource_availability": 8,   # 8/10 * 15 = 12.0
            "scalability": 8,             # 8/10 * 10 = 8.0
            "risk_level": 2               # (2 - 1) * 1.5 = 1.5 penalty
        }
        # Base = 22.5 + 16.0 + 13.5 + 13.5 + 12.0 + 8.0 = 85.5
        # Penalty = 1.5 -> Net = 84.0
        result = feasibility_engine.calculate_feasibility(inputs)
        
        self.assertAlmostEqual(result["overall_score"], 84.0, delta=0.5)
        self.assertEqual(result["tier"], "High Feasibility & High Impact")
        self.assertGreater(len(result["positive_factors"]), 0)
        self.assertIn("disclaimer", result)
        self.assertIn("explanation", result)

    def test_feasibility_boundary_clamping(self):
        """Verify inputs outside 1-10 are safely clamped."""
        inputs = {
            "expected_benefit": 999,
            "technical_feasibility": -50,
            "cost_fit": 5,
            "implementation_time": 5,
            "resource_availability": 5,
            "scalability": 5,
            "risk_level": 50
        }
        result = feasibility_engine.calculate_feasibility(inputs)
        self.assertGreaterEqual(result["overall_score"], 0.0)
        self.assertLessEqual(result["overall_score"], 100.0)

    # --------------------------------------------------------------------------
    # 4. Civic & Government Portal Detection Tests
    # --------------------------------------------------------------------------
    def test_civic_portal_detection_positive(self):
        """Verify infrastructure problem correctly identifies verified government portals."""
        res = gov_portal.detect_government_relevance(
            "Public Infrastructure",
            "Severe monsoon waterlogging and choked municipal storm drainage"
        )
        self.assertTrue(res["is_civic_related"])
        self.assertGreater(len(res["portals"]), 0)
        self.assertIsNotNone(res["advisory_notice"])
        # Verify portal contains verified gov.in URL
        self.assertTrue(any(".gov.in" in p["url"] for p in res["portals"]))

    def test_civic_portal_detection_negative(self):
        """Verify software/tech problem is not mistakenly tagged as municipal."""
        res = gov_portal.detect_government_relevance(
            "Technology & Operations",
            "Python web app caching optimization and database index tuning"
        )
        self.assertFalse(res["is_civic_related"])
        self.assertEqual(len(res["portals"]), 0)

    # --------------------------------------------------------------------------
    # 5. Flask Web View Routes Tests
    # --------------------------------------------------------------------------
    def test_route_home(self):
        """Test homepage renders status 200 with IMPACT LAB branding."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"IMPACT LAB", response.data)
        self.assertIn(b"From Ideas to Tested Impact", response.data)
        self.assertNotIn(b"INNOTECH'26", response.data)

    def test_route_problems_page_and_filtering(self):
        """Test problem explorer and keyword search filtering."""
        response = self.client.get("/problems")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore Real-World Challenges", response.data)

        # Filter by keyword
        response_filtered = self.client.get("/problems?q=support")
        self.assertEqual(response_filtered.status_code, 200)
        self.assertIn(b"High Customer Support", response_filtered.data)

    def test_route_problem_details(self):
        """Test problem detail view for problem #1 (featured problem)."""
        response = self.client.get("/problems/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"High Customer Support Response Times", response.data)
        self.assertIn(b"Proposed Solutions", response.data)

    def test_route_problem_details_not_found(self):
        """Test 404 handling on non-existent problem."""
        response = self.client.get("/problems/999999")
        self.assertEqual(response.status_code, 404)

    def test_route_submit_problem_form_and_action(self):
        """Test submitting a new problem via web form and database persistence."""
        post_data = {
            "title": "Automated Campus Bicycle Sharing Station Lock Failure",
            "category": "Technology & Operations",
            "user_type": "Student / Campus",
            "description": "Smart locks on campus rental cycles frequently freeze after winter rainstorms, trapping deposits.",
            "keywords": "bicycle, iot, smart lock, rental, campus transit",
            "location": "Engineering Quad Station",
            "expected_impact": "Zero frozen lock errors during morning peak hours (8am - 10am)",
            "constraints": "Budget under 2000 INR; must survive outdoor rain exposure",
            "proposed_solution": "3D printed weatherproof silicon flap covers for servo solenoid",
            "contact_email": "transit@campus.edu"
        }
        response = self.client.post("/submit", data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"successfully registered", response.data)
        self.assertIn(b"Automated Campus Bicycle Sharing", response.data)

    def test_route_discover_page(self):
        """Test discover page with both select mode and custom query mode."""
        # Query by existing problem ID
        resp_id = self.client.get("/discover?problem_id=1")
        self.assertEqual(resp_id.status_code, 200)
        self.assertIn(b"Ranked Solution Matches", resp_id.data)

        # Query by custom query string
        resp_q = self.client.get("/discover?q=waterlogging+drain+flood")
        self.assertEqual(resp_q.status_code, 200)
        self.assertIn(b"Ranked Solution Matches", resp_q.data)

    def test_route_evaluate_page_and_action(self):
        """Test feasibility evaluator page and post submission."""
        resp_get = self.client.get("/evaluate?title=Smart+Drain+Trap")
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn(b"Solution Feasibility", resp_get.data)

        eval_data = {
            "solution_title": "Smart Drain Trap",
            "expected_benefit": 8,
            "technical_feasibility": 8,
            "cost_fit": 9,
            "implementation_time": 7,
            "resource_availability": 8,
            "scalability": 7,
            "risk_level": 3
        }
        resp_post = self.client.post("/evaluate", data=eval_data, follow_redirects=True)
        self.assertEqual(resp_post.status_code, 200)
        self.assertIn(b"Feasibility evaluation calculated and saved", resp_post.data)

    def test_route_help_network_and_volunteer(self):
        """Test help network dashboard and volunteer registration."""
        resp_get = self.client.get("/help-network")
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn(b"Active Community Help Inquiries", resp_get.data)

        # Register helper
        helper_data = {
            "name": "Kavita Singhal",
            "contact": "kavita.iot@college.edu",
            "category": "Technology",
            "skills": "Python, MicroPython, ESP8266, MQTT",
            "description": "Third year electronics student building IoT environmental telemetry.",
            "availability": "4 hrs on weekends"
        }
        resp_helper = self.client.post("/help-network/volunteer", data=helper_data, follow_redirects=True)
        self.assertEqual(resp_helper.status_code, 200)
        self.assertIn(b"Thank you for joining as a volunteer", resp_helper.data)

    def test_route_about_page(self):
        """Test about page with clean product overview and collapsible reviewer formulas."""
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ABOUT IMPACT LAB", response.data)
        self.assertIn(b"From Ideas to Tested Impact", response.data)
        self.assertIn(b"Core Platform Modules", response.data)
        self.assertIn(b"Smart Solution Discovery", response.data)
        self.assertIn(b"Technical Architecture &amp; Formulas (For Reviewers)", response.data)
        self.assertNotIn(b"INNOTECH'26", response.data)

    # --------------------------------------------------------------------------
    # 6. REST API Endpoints Tests
    # --------------------------------------------------------------------------
    def test_api_endpoints_backward_compatibility(self):
        """Verify JSON REST APIs return valid JSON and expected status codes."""
        # GET /api/problems
        r_probs = self.client.get("/api/problems")
        self.assertEqual(r_probs.status_code, 200)
        probs_data = r_probs.get_json()
        self.assertIsInstance(probs_data, list)
        self.assertGreater(len(probs_data), 0)

        # POST /api/problems
        new_prob = {
            "title": "API Submitted Lab Equipment Scheduling Conflict",
            "description": "Students cannot reserve spectroscopy tools without physical sign-in sheet.",
            "category": "Technology & Operations",
            "user_type": "Student"
        }
        r_post_p = self.client.post("/api/problems", json=new_prob)
        self.assertEqual(r_post_p.status_code, 201)
        res_json = r_post_p.get_json()
        self.assertIn("problem", res_json)
        prob_id = res_json["problem"]["id"]

        # POST /api/solutions
        new_sol = {
            "problem_id": prob_id,
            "title": "Google Calendar Resource Booking QR Gateway",
            "description": "QR code on microscope triggers Google Apps Script booking validation."
        }
        r_post_s = self.client.post("/api/solutions", json=new_sol)
        self.assertEqual(r_post_s.status_code, 201)

        # GET /api/stats
        r_stats = self.client.get("/api/stats")
        self.assertEqual(r_stats.status_code, 200)
        stats_data = r_stats.get_json()
        self.assertIn("total_problems", stats_data)

        # POST /api/discover
        r_disc = self.client.post("/api/discover", json={"query": "microscope equipment scheduling"})
        self.assertEqual(r_disc.status_code, 200)
        disc_data = r_disc.get_json()
        self.assertIn("results", disc_data)

        # POST /api/evaluate
        r_eval = self.client.post("/api/evaluate", json={"expected_benefit": 8, "technical_feasibility": 9})
        self.assertEqual(r_eval.status_code, 200)
        eval_json = r_eval.get_json()
        self.assertIn("overall_score", eval_json)


if __name__ == "__main__":
    unittest.main()
