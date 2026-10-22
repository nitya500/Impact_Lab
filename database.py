"""
IMPACT LAB - Database Module (SQLite)
Problem-to-Impact Platform
====================================
Handles persistent storage for:
- Problems (community, civic, tech, environmental, engineering, etc.)
- Solutions (proposals, resources, difficulty, test results)
- Feasibility Evaluations (MCDA scoring criteria & explainable results)
- Help Requests & Helper Interests (collaboration network)
- Help Givers (expert & technical volunteer directory)
"""

import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "impact_lab.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates tables if they do not exist, performs safe schema upgrades, and seeds initial data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Problems Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        keywords TEXT,
        location TEXT,
        expected_impact TEXT,
        constraints TEXT,
        available_resources TEXT,
        proposed_solution TEXT,
        user_type TEXT DEFAULT 'Help Seeker',
        contact_email TEXT,
        severity TEXT DEFAULT 'Medium', -- 'Low', 'Medium', 'High', 'Critical'
        status TEXT DEFAULT 'Open', -- 'Open', 'In Progress', 'Testing', 'Resolved'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Solutions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        author_name TEXT DEFAULT 'Community Solver',
        author_type TEXT DEFAULT 'Independent Contributor',
        required_resources TEXT,
        difficulty TEXT DEFAULT 'Medium', -- 'Low', 'Medium', 'High'
        estimated_cost TEXT DEFAULT 'Low', -- 'Zero / Free', 'Low (< ₹5,000)', 'Medium (₹5k - ₹25k)', 'High (> ₹25k)'
        expected_benefit TEXT,
        time_weeks INTEGER DEFAULT 4,
        status TEXT DEFAULT 'Proposed', -- 'Proposed', 'Selected', 'Testing', 'Result Recorded'
        target_metric TEXT,
        actual_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE
    )
    """)

    # 3. Feasibility Assessments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feasibility_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id INTEGER,
        solution_title TEXT NOT NULL,
        overall_score REAL NOT NULL,
        criteria_scores TEXT NOT NULL, -- JSON formatted scores
        positive_factors TEXT,        -- JSON list
        risks TEXT,                   -- JSON list
        recommendations TEXT,         -- JSON list
        explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE SET NULL
    )
    """)

    # 4. Help Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS help_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id INTEGER,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        skills_needed TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        urgency TEXT DEFAULT 'Normal', -- 'Low', 'Normal', 'High', 'Critical'
        status TEXT DEFAULT 'Open',     -- 'Open', 'In Progress', 'Resolved'
        contact_name TEXT,
        contact_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE SET NULL
    )
    """)

    # 5. Helper Interests Table (solvers who offer to help a specific request)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS helper_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        help_request_id INTEGER NOT NULL,
        helper_name TEXT NOT NULL,
        helper_email TEXT NOT NULL,
        skills TEXT NOT NULL,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (help_request_id) REFERENCES help_requests (id) ON DELETE CASCADE
    )
    """)

    # 6. Help Giver Directory Table (standing roster of experts/students)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS helpers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        skills TEXT NOT NULL,
        category TEXT DEFAULT 'Technology',
        description TEXT,
        contact TEXT,
        availability TEXT DEFAULT 'Part-time Volunteer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Safe Schema Migration Check (for existing database instances)
    # Check problems table columns
    problem_cols = [c[1] for c in cursor.execute("PRAGMA table_info(problems)").fetchall()]
    if "severity" not in problem_cols:
        cursor.execute("ALTER TABLE problems ADD COLUMN severity TEXT DEFAULT 'Medium'")
    if "available_resources" not in problem_cols:
        cursor.execute("ALTER TABLE problems ADD COLUMN available_resources TEXT DEFAULT ''")

    # Check help_requests table columns
    help_cols = [c[1] for c in cursor.execute("PRAGMA table_info(help_requests)").fetchall()]
    if "category" not in help_cols:
        cursor.execute("ALTER TABLE help_requests ADD COLUMN category TEXT DEFAULT 'General'")

    conn.commit()

    # Check if seed data is needed
    cursor.execute("SELECT COUNT(*) FROM problems")
    problem_count = cursor.fetchone()[0]

    if problem_count == 0:
        seed_database(conn)
    else:
        # Check if extended multi-domain seed data (laptop impact, healthcare, etc.) is missing
        laptop_check = cursor.execute("SELECT id FROM problems WHERE title LIKE '%Laptop%'").fetchone()
        if not laptop_check:
            seed_extended_domains(conn)

    conn.close()


def seed_database(conn):
    """Inserts realistic starter problems and solutions representing diverse domains."""
    cursor = conn.cursor()

    # Problem 1: Operational Support Workflow
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Medium', ?)
    """, (
        "High Customer Support Response Times with Repetitive Queries",
        "A regional community center receives over 150 repetitive support inquiries per week regarding schedule timings, eligibility criteria, and fee structures. The current manual response turnaround takes 48-72 hours, resulting in user frustration and volunteer burnout.",
        "Technology & Operations",
        "customer support, response time, automation, queries, ticket system, chatbot, faq",
        "Regional Community Center, Sector 62",
        "Reduce response time from 48 hours to under 2 hours for standard queries and reduce volunteer workload by 60%.",
        "Budget capped at ₹8,000; non-technical volunteer staff; requires open-source or free-tier hosting.",
        "2 office laptops, shared broadband internet, volunteer coordinator time (10 hrs/week).",
        "We are considering setting up an automated triage or FAQ bot but do not know which approach is most cost-effective.",
        "Business / Community",
        "coordinator@communityorg.org",
        "Testing"
    ))
    prob1_id = cursor.lastrowid

    # Solutions for Problem 1
    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob1_id,
        "Categorized Self-Service Knowledge Base & Smart FAQ Portal",
        "Build a fast, mobile-friendly searchable FAQ portal with structured search tags, accordion answers, and quick inquiry escalation forms using lightweight static site tech.",
        "Technology & Operations",
        "Web Systems Working Group",
        "Software Engineer",
        "Static web hosting (GitHub Pages/Netlify), Markdown content structure, domain DNS.",
        "Low",
        "Zero / Free",
        "Addresses 45-50% of routine questions instantly with zero recurring server cost.",
        2,
        "Selected",
        "Resolve 40% of queries without staff intervention",
        "Measured in pilot week 2: 52% of visitors found answers directly on the portal without submitting tickets."
    ))

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob1_id,
        "Lightweight Open-Source Ticket Routing Workflow",
        "Deploy a free self-hosted ticketing system (such as FreeScout or Zammad) to tag incoming emails, auto-assign categories, and send automated acknowledgment templates.",
        "Technology & Operations",
        "IT Infrastructure Volunteer",
        "Systems Specialist",
        "Small VPS or local intranet server, email SMTP configuration, 2 hours staff training.",
        "Medium",
        "Low (< ₹5,000)",
        "Eliminates lost emails and brings first-response acknowledgment time under 15 minutes.",
        3,
        "Proposed",
        "Bring staff turnaround to under 8 hours",
        None
    ))

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob1_id,
        "Rule-Based Telegram / WhatsApp Community Support Bot",
        "Create an automated interactive messaging bot answering the top 20 repetitive questions 24/7 with instant keyword recognition and human handoff.",
        "Technology & Operations",
        "Automation Developer",
        "Software Engineer",
        "Telegram Bot API (free) / WhatsApp Business Cloud API, Python Flask webhook server.",
        "Medium",
        "Low (< ₹5,000)",
        "Instant responses 24/7 on mobile chat where the community already communicates.",
        3,
        "Testing",
        "Provide answers in under 10 seconds for standard queries",
        "Beta running with 35 test users: 89% query resolution without human escalation."
    ))

    # Problem 2: Civic / Infrastructure / Government Issue
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'High', ?)
    """, (
        "Severe Monsoon Stormwater Drain Clogging and Street Inundation",
        "Every monsoon, municipal storm drains in our residential block become choked with plastic debris, causing knee-deep waterlogging, mosquito breeding, and traffic disruption. Local residents need both a rapid civic escalation mechanism and a community desilting/mesh trap solution.",
        "Public Infrastructure",
        "waterlogging, storm drain, municipal, drainage, flooding, civic, sanitation, monsoon",
        "Ward 14, East Delhi / Noida Corridor",
        "Prevent localized road flooding for 4,000 residents and eliminate standing water within 4 hours of heavy rainfall.",
        "Requires municipal clearance for permanent alterations; community budget limited to ₹15,000.",
        "Resident welfare volunteers, local welding fabricator partnership, basic hand tools.",
        "Install perforated wire-mesh litter traps at road surface inlets and establish a community monitoring brigade.",
        "Community Representative",
        "resident.welfare@block-c.org",
        "Open"
    ))
    prob2_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob2_id,
        "Modular Removable Galvanized Mesh Drain Grate Traps",
        "Install removable, corrosion-resistant steel mesh screens right beneath street runoff grates to capture solid waste before it reaches subterranean drain pipes.",
        "Public Infrastructure",
        "Civic Infrastructure Working Group",
        "Engineering Working Group",
        "Galvanized iron mesh sheets, angle irons, local fabrication welder, warning flags.",
        "Medium",
        "Medium (₹5k - ₹25k)",
        "Prevents 90% of plastic debris from entering underground conduits, allowing quick surface cleaning by sanitation workers.",
        3,
        "Proposed",
        "Zero underground blockage during 50mm/hr cloudburst",
        None
    ))

    # Problem 3: Community & Social Innovation
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Medium', ?)
    """, (
        "Institutional Cafeteria Surplus Food Recovery & Logistics",
        "Commercial and institutional cafeterias discard between 30kg to 60kg of safe, edible surplus cooked food daily because of unpredictable attendance on weekends and holidays. Meanwhile, nearby community night shelters face meal shortages.",
        "Social & Community",
        "food waste, cafeteria, hunger, donation, logistics, surplus food, volunteers",
        "North District Community Hub",
        "Recover over 1,000 kg of edible meals per month and distribute them safely to verified community shelters within 90 minutes of closing.",
        "Food safety window is strictly 2 hours; volunteer transit must be zero-cost or walking distance.",
        "4 insulated thermal delivery bags, student volunteer WhatsApp group (30 members).",
        "A notification system alerting food recovery volunteers when cafeteria surplus exceeds 10 portions.",
        "Help Seeker",
        "foodaction@communitynet.org",
        "In Progress"
    ))
    prob3_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob3_id,
        "Surplus Food Alert Webapp with QR Verification",
        "A simple progressive web app where facility managers tap one button to broadcast excess quantity, automatically pinging assigned volunteer riders with insulated carriers.",
        "Social & Community",
        "Surplus Logistics Working Group",
        "Community Innovator",
        "Thermal delivery bags, basic web app, messaging group webhook, manager login.",
        "Low",
        "Low (< ₹5,000)",
        "Instant dispatch within 20 minutes of meal completion, ensuring zero food spoilage.",
        2,
        "Testing",
        "Save 25kg+ daily surplus",
        "Week 1 trial: 180kg food diverted to shelter across 6 shifts with 100% safety compliance."
    ))

    # Problem 4: Environmental / Clean Energy
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Critical', ?)
    """, (
        "Lack of Real-time Water Quality Monitoring in Rural Community Tanks",
        "Open village water storage reservoirs suffer from periodic bacterial contamination and turbidity spikes after unseasonal rains, causing gastrointestinal outbreaks before conventional lab tests return results.",
        "Environmental",
        "water quality, turbidity, sensors, rural health, potable water, iot, contamination",
        "Surajpur Village Panchayat",
        "Provide early warning of contamination spikes within 15 minutes instead of 4 days.",
        "No continuous grid power; sensor unit must be low-power battery or solar powered.",
        "1 prototype Arduino kit, water testing reagent strips, village panchayat permission.",
        "Low-cost floating sensor buoy with pH and turbidity probes.",
        "NGO",
        "wateraction@ruralngo.in",
        "Open"
    ))
    prob4_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob4_id,
        "Solar-Powered IoT Buoy with Turbidity and pH Telemetry",
        "An ESP32-based hermetically sealed buoy equipped with analog turbidity and pH sensors, solar trickle charger, and SIM800L module transmitting daily SMS alerts to the village health worker.",
        "Environmental",
        "Clean Tech Sensors Initiative",
        "Hardware Working Group",
        "ESP32 micro-controller, turbidity probe, small 5W solar panel, GSM module, waterproof enclosure.",
        "High",
        "Medium (₹5k - ₹25k)",
        "Automated continuous testing preventing waterborne epidemics through proactive alerts.",
        6,
        "Proposed",
        "Detect turbidity surges (> 5 NTU) within 15 mins",
        None
    ))

    # Pre-seed Feasibility Evaluations
    cursor.execute("""
    INSERT INTO feasibility_evaluations (problem_id, solution_title, overall_score, criteria_scores, positive_factors, risks, recommendations, explanation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob1_id,
        "Categorized Self-Service Knowledge Base & Smart FAQ Portal",
        84.5,
        json.dumps({
            "expected_benefit": 8.5,
            "technical_feasibility": 9.5,
            "cost_fit": 9.5,
            "implementation_time": 9.0,
            "resource_availability": 8.0,
            "scalability": 8.5,
            "risk_penalty": 2.0
        }),
        json.dumps([
            "Extremely low financial overhead using static hosting",
            "High technical feasibility with minimal maintenance requirements",
            "Fast deployment turnaround within 2 weeks"
        ]),
        json.dumps([
            "Requires initial effort to write and structure clear answers",
            "Will not resolve complex non-standard user grievances automatically"
        ]),
        json.dumps([
            "Include an easy escalation form button at the bottom of every FAQ",
            "Review query logs monthly to update missing answers"
        ]),
        "The proposal scores 84.5/100 due to near-zero implementation cost, high accessibility for non-technical users, and rapid speed to deployment."
    ))

    # Pre-seed Help Requests
    cursor.execute("""
    INSERT INTO help_requests (problem_id, title, description, skills_needed, category, urgency, status, contact_name, contact_info)
    VALUES (?, ?, ?, ?, 'Technology & Operations', 'Normal', 'Open', ?, ?)
    """, (
        prob1_id,
        "Need volunteer with static documentation engine experience for knowledge base",
        "We have compiled the 40 most common questions from our support logs and need someone to help structure the search filter and mobile UI.",
        "HTML/CSS, Static Site Generator, UI Design",
        "Operations Lead",
        "support.ops@communityhub.org"
    ))
    req1_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO help_requests (problem_id, title, description, skills_needed, category, urgency, status, contact_name, contact_info)
    VALUES (?, ?, ?, ?, 'Public Infrastructure', 'High', 'In Progress', ?, ?)
    """, (
        prob2_id,
        "Seeking Structural or Mechanical Engineer to design drain mesh brackets",
        "Need assistance drafting simple dimension drawings for weldable galvanized grate brackets that won't impede road street sweepers.",
        "CAD / AutoCAD, Mechanical Fabrication, Civil Engineering",
        "Civic Action Coordinator",
        "rwa.ward14@civicnet.org"
    ))

    cursor.execute("""
    INSERT INTO help_requests (problem_id, title, description, skills_needed, category, urgency, status, contact_name, contact_info)
    VALUES (?, ?, ?, ?, 'Environmental', 'Normal', 'Open', ?, ?)
    """, (
        prob4_id,
        "Looking for Embedded Systems Specialist for sensor telemetry calibration",
        "Sensor hardware is assembled; need help calibrating analog voltage readings into NTU turbidity units and sending AT commands over GSM.",
        "Arduino, Embedded C, IoT, Sensor Calibration",
        "Field Engineering Lead",
        "field.ops@ruralwater.org"
    ))

    # Pre-seed Helper Interests
    cursor.execute("""
    INSERT INTO helper_interests (help_request_id, helper_name, helper_email, skills, message)
    VALUES (?, ?, ?, ?, ?)
    """, (
        req1_id,
        "Jordan Lee",
        "jordan.dev@solutions.org",
        "Frontend Web Dev, Bootstrap, JavaScript",
        "I have built two static documentation sites and can set up the search interface in 3 days."
    ))

    # Pre-seed Standing Helpers Directory
    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Arvind Joshi, M.Sc.",
        "Water Quality, Environmental Chemistry, Spectrometry",
        "Environment",
        "Environmental scientist available for water testing protocol validation and sensor telemetry consultation.",
        "joshi.enviro@solutions.org",
        "Weekends (2-4 hrs)"
    ))

    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Sneha M.",
        "Python, Flask, NLP, REST APIs",
        "Technology",
        "Software engineer with experience in building lightweight webhooks, automation pipelines, and text categorization tools.",
        "sneha.dev@solutions.org",
        "Evenings & Weekends"
    ))

    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Harsh Vardhan",
        "Civil CAD, Municipal Drainage, Urban Hydrology",
        "Infrastructure",
        "Civil and municipal hydrology consultant specializing in urban stormwater runoff management.",
        "harsh.hydrology@solutions.org",
        "Project-based consultation"
    ))

    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Meera Swaminathan",
        "Community Outreach, NGO Logistics, Field Operations",
        "Social & Community",
        "Operations coordinator with 5 years experience in food recovery networks and community logistics.",
        "meera.logistics@actionnet.org",
        "Active Volunteer"
    ))

    conn.commit()

    # Now add extended multi-domain seed data (Engineering, Healthcare, College Life, etc.)
    seed_extended_domains(conn)


def seed_extended_domains(conn):
    """
    Seeds comprehensive problems, solutions, help requests, and volunteer experts
    across Engineering & Innovation, Healthcare Accessibility, College Life,
    Education, and Government Services.
    """
    cursor = conn.cursor()

    # Domain 1: Engineering & Innovation (Physical damage, materials, protective design)
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Frequent Laptop Screen & Casing Damage from Accidental Drops in Maker Labs",
        "Engineering students carrying laptops in active mechanical fabrication workshops and crowded maker spaces experience frequent casing fractures, screen cracks, and motherboard flex damage caused by accidental drops from workbenches. Existing laptop sleeves are clumsy to keep on while working, and commercial rugged cases are prohibitively expensive for students.",
        "Engineering & Innovation",
        "laptop, damage, accidental impacts, drops, shock absorption, protective design, materials, engineering, hinge, casing, mechanics",
        "University Advanced Prototyping Workshop, Block 4",
        "Prevent 85% of drop-induced screen cracks and chassis fractures from typical 1.2m workbench heights while maintaining device cooling.",
        "Fabrication cost must be under ₹1,000 per unit; must not block exhaust fan vents or USB ports; must be easily manufacturable with campus 3D printers.",
        "Campus maker space FDM 3D printers, digital calipers, standard filament stock, student test laptops.",
        "Dual-layer snap-on bumper design utilizing non-Newtonian shear-thickening polymer padding and TPU corner cushions.",
        "Academic / Research",
        "makerlab.lead@engineering.edu",
        "High",
        "Testing"
    ))
    prob_eng_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_eng_id,
        "Corner-Reinforced Elastomeric Shock Dissipation Chassis with Viscoelastic Foam",
        "Design a form-fitting dual-layer protective case using thermoplastic polyurethane (TPU) honeycombed corner air-cushions and viscoelastic foam inserts. The non-Newtonian shock-absorbing layer remains pliable during normal carry but instantly stiffens upon high-velocity impact, redirecting kinetic energy away from the LCD panel and display hinges.",
        "Engineering & Innovation",
        "Advanced Materials & Structural Mechanics Lab",
        "Engineering Working Group",
        "Fused deposition 3D printer (TPU filament), viscoelastic foam inserts, CAD structural stress analysis (SolidWorks).",
        "Medium",
        "Low (< ₹5,000)",
        "Dampens up to 85% of perpendicular drop shock; passes repeated 1.5m drop tests onto concrete without functional chassis deformation or panel crack.",
        3,
        "Testing",
        "Zero internal component failure from 1.2m drop test",
        "Validated on 10 drop trials: corner deceleration reduced by 72G compared to rigid plastic."
    ))

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_eng_id,
        "Internal Honeycomb Structural Ribbing & Free-Fall Accelerometer Auto-Parking",
        "Internal chassis reinforcing ribbing using aerospace-grade composite geometry paired with open-source firmware that leverages the laptop's internal accelerometer to auto-park hard disk heads and engage an active tension lock on screen hinges within 150ms of detected free-fall.",
        "Engineering & Innovation",
        "Mechatronics Prototyping Group",
        "Software & Hardware Working Group",
        "Embedded firmware toolchain, laser-cut internal polycarbonate bracket, vibration testing rig.",
        "High",
        "Medium (₹5k - ₹25k)",
        "Prevents screen hinge snap-back and protects mechanical components during mid-air trajectory.",
        4,
        "Proposed",
        "Engage protective latch within 150ms of detected zero-G fall",
        None
    ))

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_eng_id,
        "Modular Snap-On Impact-Absorbing Edge Bumpers",
        "Modular clip-on silicone-composite corner bumpers with air-pocket dispersion chambers that attach securely to standard 13-inch and 15-inch laptop edges without blocking airflow exhaust vents or USB ports.",
        "Engineering & Innovation",
        "Product Design Collective",
        "Industrial Designer",
        "Open-source STL 3D print models, food-grade silicone casting mold, compression clips.",
        "Low",
        "Zero / Free",
        "Low-cost printable protection costing less than ₹200 to fabricate in any university maker lab.",
        1,
        "Result Recorded",
        "Fit 90% of student laptops under ₹300 per unit",
        "Tested across 45 student devices: zero screen breaks recorded over 60-day test period."
    ))

    # Pre-seed evaluation for the laptop engineering solution
    cursor.execute("""
    INSERT INTO feasibility_evaluations (problem_id, solution_title, overall_score, criteria_scores, positive_factors, risks, recommendations, explanation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_eng_id,
        "Corner-Reinforced Elastomeric Shock Dissipation Chassis with Viscoelastic Foam",
        88.0,
        json.dumps({
            "expected_benefit": 9.0,
            "technical_feasibility": 9.0,
            "cost_fit": 8.5,
            "implementation_time": 8.5,
            "resource_availability": 9.0,
            "scalability": 8.5,
            "risk_penalty": 1.5
        }),
        json.dumps([
            "Strong structural performance against perpendicular impact shocks",
            "Readily 3D-printable with campus TPU filaments and low overhead",
            "Directly protects both casing and vulnerable screen hinges"
        ]),
        json.dumps([
            "TPU filament printing requires tuned printer extrusion temperatures",
            "Dimensional tolerances must account for varied manufacturer laptop thicknesses"
        ]),
        json.dumps([
            "Provide parametric CAD files allowing students to input their exact laptop dimensions",
            "Include thermal channel cutouts to avoid restricting intake airflow"
        ]),
        "Scores 88.0/100 due to high technical feasibility, exceptional impact mitigation, and low fabrication cost for university students."
    ))

    # Domain 2: Healthcare Accessibility
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Pediatric Vaccine Cold-Chain Temperature Breaches in Remote Rural Sub-Centers",
        "Rural primary health sub-centers experience frequent unrecorded temperature fluctuations in vaccine storage coolers due to daily 6-hour power outages. Health workers cannot tell whether stored polio and measles vaccines experienced thermal damage, risking compromised efficacy during immunization drives.",
        "Healthcare Accessibility",
        "vaccine, cold chain, temperature breach, healthcare, rural health, refrigeration, iot monitor, immunization, medicine",
        "District Health Sub-Centers, Mandi Rural Block",
        "100% detection of cold-chain thermal excursions before vaccine administration; preserve vaccine potency for 5,000 infants.",
        "Power cuts last up to 8 hours; must operate on backup solar or rechargeable battery; non-technical ASHA worker usability.",
        "Solar rooftop panel at primary center, 2 domestic vaccine ice-boxes, ASHA community network.",
        "Phase-change material thermal storage box paired with Bluetooth low-energy telemetry sensor.",
        "NGO / Non-Profit",
        "health.outreach@ruralsanitation.org",
        "Critical",
        "Testing"
    ))
    prob_health_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_health_id,
        "Phase-Change Material (PCM) Passive Carrier with BLE Temperature Logging",
        "A modular insulated vaccine carrier lined with bio-based phase-change material (PCM) maintaining temperatures strictly between 2°C and 8°C for up to 54 hours without electricity, equipped with a low-power Bluetooth beacon logging hourly temperatures to an offline mobile phone app.",
        "Healthcare Accessibility",
        "Bio-Thermal Systems Research Group",
        "Biomedical Engineer",
        "PCM packs (5°C transition point), vacuum-insulated box, BLE temperature logger module.",
        "Medium",
        "Low (< ₹5,000)",
        "Guarantees safe storage during prolonged blackouts with cryptographic tamper-proof logging.",
        3,
        "Testing",
        "Maintain 2°C to 8°C window for 48 hours without grid power",
        "Field pilot: 54 hours maintained under 38°C ambient heat with zero excursions."
    ))

    # Domain 3: College & Student Life
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Hostel Late-Night Campus Transit & Dark Pathway Safety Concern",
        "Students walking back from the central library and computer labs to west-campus residence hostels between 11 PM and 2 AM report safety anxiety and poorly lit blind corners along peripheral campus routes.",
        "College & Student Life",
        "campus safety, student life, night transit, security escort, dark pathways, emergency, college, hostel",
        "West Campus Residential Quad, University Campus",
        "Zero transit safety incidents; achieve under 4 minutes peer escort pairing for late-night commuters.",
        "Student-run initiative with budget under ₹10,000; strict privacy protection (no public location broadcast).",
        "Student council volunteer network, campus WiFi coverage along main avenues.",
        "Mutual peer-escort coordination web app with QR check-in and distress panic triggers.",
        "Help Seeker",
        "studentcouncil@campuslife.edu",
        "High",
        "Resolved"
    ))
    prob_coll_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_coll_id,
        "Student Peer-Escort Transit Coordination Webapp",
        "A progressive web application allowing verified students departing late from labs to pair with other students or campus security guards walking in the same direction, complete with route checkpoints.",
        "College & Student Life",
        "Campus Safety Student Taskforce",
        "Student Developer",
        "Lightweight Python Flask backend, campus student ID SSO, SMS notification gateway.",
        "Low",
        "Zero / Free",
        "Eliminates solo late-night walks and creates a verified safe buddy transit network.",
        2,
        "Result Recorded",
        "Average pairing time under 4 minutes with 100% safe arrivals",
        "Successfully conducted 340+ verified safe escorts over the spring semester with zero incidents."
    ))

    # Domain 4: Education & Learning
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Accessible STEM Lab Equipment for Visually Impaired Students",
        "Visually impaired students enrolled in undergraduate physics and electrical engineering courses struggle to participate in laboratory experiments because standard digital multimeters and oscilloscope readouts are purely visual.",
        "Education & Learning",
        "accessibility, stem lab, visually impaired, audio multimeter, braille, science education, inclusive, tools",
        "Central Science & Engineering Labs",
        "Allow visually impaired students to conduct circuit measurement labs completely independently.",
        "Budget under ₹3,000 per workstation; compatible with standard 5V/12V breadboard circuits.",
        "Campus electronics workshop, Arduino kits, 3D printing equipment.",
        "Open-source audio-tactile digital multimeter with voice output and braille labels.",
        "Academic / Research",
        "inclusive.stem@education.org",
        "Medium",
        "Testing"
    ))
    prob_edu_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_edu_id,
        "Open-Source Audio-Tactile Talking Multimeter & Sensor Hub",
        "An Arduino-based measurement interface that reads voltage, current, resistance, and temperature, converting numerical values into synthesized speech through an onboard speaker or headphone jack, accompanied by 3D-printed tactile braille markings.",
        "Education & Learning",
        "Assistive Technology Innovation Lab",
        "Hardware Specialist",
        "Arduino Nano, DFPlayer Mini voice module, precision voltage divider, 3D printed case.",
        "Low",
        "Low (< ₹5,000)",
        "Provides real-time auditory verification of electronic measurements with 99% accuracy.",
        2,
        "Testing",
        "Speak measurement values accurately within 800ms of probe contact",
        "Tested with 12 students: completed circuit verification labs with 100% independence."
    ))

    # Domain 5: Government & Civic Services
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Pothole Clustering & Hazardous Road Surface Delays on Commuter Arterials",
        "Heavy monsoon rains cause deep pothole clusters on major arterial roads connecting industrial sectors to residential neighborhoods, resulting in vehicle damage, two-wheeler accidents, and traffic gridlocks. Citizens have no transparent mechanism to monitor road contractor repair accountability.",
        "Government & Civic Services",
        "pothole, road surface, road damage, civic, municipal, public works, traffic safety, government, infrastructure",
        "Arterial Road Corridor, Sector 18 to 62",
        "Reduce municipal pothole repair verification turnaround from 45 days to under 7 days.",
        "Requires official civic body alignment; photo submissions must be geo-tagged and tamper-proof.",
        "Local commuters, smartphone cameras, citizen advocacy group.",
        "Geo-tagged civic issue tracker integrated with municipal grievance portals.",
        "Community Representative",
        "civicwatch@citizensgroup.org",
        "High",
        "Open"
    ))
    prob_gov_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status, target_metric, actual_result)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prob_gov_id,
        "Geo-Tagged Road Hazard Reporting & Public Works Accountability Dashboard",
        "A crowdsourced web app where commuters snap road surface damage with automatic EXIF GPS tagging, clustering adjacent reports to highlight high-risk corridors and generating auto-formatted submissions to municipal CPGRAMS portals.",
        "Government & Civic Services",
        "Civic Tech Working Group",
        "Software Engineer",
        "Leaflet.js mapping, GPS coordinates extraction, public works API integration.",
        "Low",
        "Zero / Free",
        "Creates transparent, auditable evidence logs that compel civic departments to honor repair SLAs.",
        2,
        "Proposed",
        "Achieve public works contractor inspection within 72 hours of 5 citizen votes",
        None
    ))

    # Extended Help Requests
    cursor.execute("""
    INSERT INTO help_requests (problem_id, title, description, skills_needed, category, urgency, status, contact_name, contact_info)
    VALUES (?, ?, ?, ?, 'Engineering & Innovation', 'High', 'In Progress', ?, ?)
    """, (
        prob_eng_id,
        "Need 3D CAD designer to optimize snap-on laptop bumper corner geometries",
        "We have tested our TPU shock absorption foam on 3D printed prototypes, but need someone skilled in SolidWorks/Fusion360 to refine snap-latch clearances for multiple laptop bezels.",
        "SolidWorks, Fusion 360, 3D Printing, Mechanical Design",
        "Prof. K. Sharma",
        "makerlab.lead@engineering.edu"
    ))
    req_eng_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO helper_interests (help_request_id, helper_name, helper_email, skills, message)
    VALUES (?, ?, ?, ?, ?)
    """, (
        req_eng_id,
        "Vikramaditya Roy",
        "vikram.cad@engineering.edu",
        "Fusion 360, Parametric CAD, TPU 3D Printing",
        "I have 3 years of CAD prototyping experience and can create parametric STL files adaptable to any laptop thickness in 4 days."
    ))

    cursor.execute("""
    INSERT INTO help_requests (problem_id, title, description, skills_needed, category, urgency, status, contact_name, contact_info)
    VALUES (?, ?, ?, ?, 'Healthcare Accessibility', 'Critical', 'Open', ?, ?)
    """, (
        prob_health_id,
        "Seeking IoT firmware developer for BLE vaccine temperature logger",
        "Need an embedded developer to write low-power C++ firmware for Nordic nRF52 BLE beacon to log temperature every 30 minutes with 6-month coin-cell battery life.",
        "Embedded C++, BLE, nRF52, Ultra-Low Power Firmware",
        "Dr. Alok Verma",
        "health.outreach@ruralsanitation.org"
    ))

    # Extended Standing Helpers Directory
    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Dr. Rajesh K., Ph.D.",
        "Materials Science, Polymer Chemistry, Impact Dissipation",
        "Engineering & Innovation",
        "Materials researcher with expertise in shear-thickening non-Newtonian fluids, impact mechanics, and protective gear design.",
        "rajesh.materials@innovation.org",
        "Weekends (2-4 hrs)"
    ))

    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Ananya Sen, M.Tech",
        "Embedded Systems, IoT, Bluetooth Low Energy, Biomedical Telemetry",
        "Healthcare Accessibility",
        "Hardware engineer specializing in medical sensor monitoring, ultra-low-power circuits, and telemetry systems.",
        "ananya.biomed@techhealth.org",
        "Evenings & Weekends"
    ))

    cursor.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Tanvi Sharma",
        "Assistive Technology, Braille Interface Design, Inclusive UX",
        "Education & Learning",
        "Accessibility specialist focused on creating audio and tactile interfaces for blind and low-vision students in STEM.",
        "tanvi.access@eduforall.org",
        "Flexible (4 hrs/week)"
    ))

    conn.commit()


# ==============================================================================
# Helper Query Functions for Application
# ==============================================================================

def get_all_problems(search=None, category=None, status=None, sort=None):
    """
    Fetches problems filtered by keyword search, category, or status,
    with flexible sorting options (newest, oldest, severity, solutions).
    """
    conn = get_db_connection()
    query = "SELECT * FROM problems WHERE 1=1"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if search:
        search_term = f"%{search}%"
        query += " AND (title LIKE ? OR description LIKE ? OR keywords LIKE ? OR location LIKE ?)"
        params.extend([search_term, search_term, search_term, search_term])

    # Dynamic Sorting
    if sort == "oldest":
        query += " ORDER BY id ASC"
    elif sort == "severity":
        query += " ORDER BY CASE severity WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END, id DESC"
    elif sort == "title":
        query += " ORDER BY title ASC"
    else:  # default newest
        query += " ORDER BY id DESC"

    problems = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(p) for p in problems]


def get_problem_by_id(problem_id):
    """Fetches a single problem by ID."""
    conn = get_db_connection()
    problem = conn.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    conn.close()
    return dict(problem) if problem else None


def get_solutions_for_problem(problem_id):
    """Fetches all solutions proposed for a specific problem."""
    conn = get_db_connection()
    solutions = conn.execute(
        "SELECT * FROM solutions WHERE problem_id = ? ORDER BY id DESC",
        (problem_id,)
    ).fetchall()
    conn.close()
    return [dict(s) for s in solutions]


def get_all_solutions():
    """Fetches all solutions with parent problem details and keywords."""
    conn = get_db_connection()
    query = """
    SELECT s.*, p.title as problem_title, p.category as problem_category, p.keywords as problem_keywords
    FROM solutions s
    LEFT JOIN problems p ON s.problem_id = p.id
    ORDER BY s.id DESC
    """
    solutions = conn.execute(query).fetchall()
    conn.close()
    return [dict(s) for s in solutions]


def get_all_help_requests(search=None, category=None, status=None):
    """
    Fetches all help requests with interest counts, filtered by keyword,
    category, and status.
    """
    conn = get_db_connection()
    query = """
    SELECT hr.*, COUNT(hi.id) as interested_helpers_count
    FROM help_requests hr
    LEFT JOIN helper_interests hi ON hr.id = hi.help_request_id
    WHERE 1=1
    """
    params = []

    if category and category != "All":
        query += " AND hr.category = ?"
        params.append(category)

    if status and status != "All":
        query += " AND hr.status = ?"
        params.append(status)

    if search:
        search_term = f"%{search}%"
        query += " AND (hr.title LIKE ? OR hr.description LIKE ? OR hr.skills_needed LIKE ?)"
        params.extend([search_term, search_term, search_term])

    query += " GROUP BY hr.id ORDER BY hr.id DESC"
    requests_data = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in requests_data]


def update_help_request_status(request_id, new_status):
    """Updates the status of a specific help request."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE help_requests SET status = ? WHERE id = ?",
        (new_status, request_id)
    )
    conn.commit()
    conn.close()


def get_recent_evaluations(limit=5):
    """Fetches recent feasibility evaluations with associated problem details."""
    conn = get_db_connection()
    query = """
    SELECT fe.*, p.title as problem_title, p.category as problem_category
    FROM feasibility_evaluations fe
    LEFT JOIN problems p ON fe.problem_id = p.id
    ORDER BY fe.id DESC
    LIMIT ?
    """
    evals = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(e) for e in evals]


def get_platform_statistics():
    """Calculates comprehensive live platform metrics for the homepage and Impact Dashboard."""
    conn = get_db_connection()
    
    total_problems = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
    total_solutions = conn.execute("SELECT COUNT(*) FROM solutions").fetchone()[0]
    testing_solutions = conn.execute(
        "SELECT COUNT(*) FROM solutions WHERE status IN ('Testing', 'Result Recorded')"
    ).fetchone()[0]
    total_helpers = conn.execute("SELECT COUNT(*) FROM helpers").fetchone()[0]
    total_requests = conn.execute("SELECT COUNT(*) FROM help_requests").fetchone()[0]

    open_problems = conn.execute("SELECT COUNT(*) FROM problems WHERE status = 'Open'").fetchone()[0]
    in_prog_problems = conn.execute("SELECT COUNT(*) FROM problems WHERE status = 'In Progress'").fetchone()[0]
    testing_problems = conn.execute("SELECT COUNT(*) FROM problems WHERE status = 'Testing'").fetchone()[0]
    resolved_problems = conn.execute("SELECT COUNT(*) FROM problems WHERE status = 'Resolved'").fetchone()[0]

    # Category Distribution
    cat_rows = conn.execute("""
    SELECT category, COUNT(*) as cnt
    FROM problems
    GROUP BY category
    ORDER BY cnt DESC
    """).fetchall()
    categories_distribution = [{"category": r["category"], "count": r["cnt"]} for r in cat_rows]

    # Difficulty Distribution
    diff_rows = conn.execute("""
    SELECT difficulty, COUNT(*) as cnt
    FROM solutions
    GROUP BY difficulty
    """).fetchall()
    difficulty_distribution = {r["difficulty"]: r["cnt"] for r in diff_rows}

    # Status Distribution
    status_distribution = {
        "Open": open_problems,
        "In Progress": in_prog_problems,
        "Testing": testing_problems,
        "Resolved": resolved_problems
    }

    # Average Feasibility Score
    avg_score_row = conn.execute("SELECT AVG(overall_score) FROM feasibility_evaluations").fetchone()[0]
    avg_score = round(avg_score_row, 1) if avg_score_row else 78.5

    conn.close()

    return {
        "total_problems": total_problems,
        "total_solutions": total_solutions,
        "tested_solutions": testing_solutions,
        "registered_helpers": total_helpers,
        "help_requests": total_requests,
        "open_problems": open_problems,
        "in_progress_problems": in_prog_problems,
        "testing_problems": testing_problems,
        "resolved_problems": resolved_problems,
        "categories_distribution": categories_distribution,
        "status_distribution": status_distribution,
        "difficulty_distribution": difficulty_distribution,
        "average_feasibility_score": avg_score
    }
