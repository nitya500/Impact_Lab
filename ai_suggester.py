"""
IMPACT LAB - Solution Suggestion & Knowledge Engine
Problem-to-Impact Platform
===================================================
Provides structured solution proposals for problems lacking existing solutions.

Priority Cascade:
1. Exact & semantically matched database solutions (via NLP Engine).
2. Curated engineering & community knowledge patterns matching category/keywords.
3. Optional external AI API integration (if configured via environment variable).

Ensures 100% local operation without external API keys or network dependencies.
All algorithmic proposals are transparently marked as suggestions, not proven facts.
"""

import os
import json
import urllib.request
import urllib.error

# Domain Pattern Knowledge Base (Local heuristics for diverse domains)
DOMAIN_KNOWLEDGE_TEMPLATES = {
    "Technology & Operations": [
        {
            "title": "Low-Code Process Automation & Triage Pipeline",
            "description": "Implement a modular workflow using open-source webhook triggers to categorize incoming demands, generate automated confirmations, and route urgent tasks to responsible team leads.",
            "difficulty": "Low",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "Python Flask / Node webhook script, Google Sheets / Airtable database, free messaging bot API.",
            "expected_benefit": "Reduces manual triage time by up to 50% and prevents inquiries from dropping through the cracks.",
            "possible_limitations": "Requires initial staff familiarization and clean rules definition for edge cases.",
            "feasibility_assessment": "High (Readily available open-source libraries and standard API connectors).",
            "why_matches": "Directly targets operational backlogs and communication delays through automated routing."
        },
        {
            "title": "Searchable Self-Service Knowledge Base & Community Wiki",
            "description": "Establish a centralized, indexed repository of FAQs, standard operating procedures, and troubleshooting guides accessible on mobile devices.",
            "difficulty": "Low",
            "estimated_cost": "Zero / Free",
            "required_resources": "Markdown documentation engine (MkDocs/Hugo) or free Notion/Obsidian shared portal.",
            "expected_benefit": "Enables end-users to find answers independently 24/7 without waiting for manual human assistance.",
            "possible_limitations": "Requires ongoing editorial upkeep when guidelines or processes change.",
            "feasibility_assessment": "Very High (Zero hosting cost on GitHub Pages or Netlify; rapid 1-2 week setup).",
            "why_matches": "Empowers users with instant information access, dramatically cutting repetitive query volume."
        }
    ],
    "Public Infrastructure": [
        {
            "title": "Surface-Level Debris Interceptor & Catch-Basin Screen",
            "description": "Fabricate custom-fitted perforated galvanized steel screens right under stormwater drain covers to intercept coarse solid waste (plastic bags, bottles, dry leaves) before they enter subterranean drain pipes.",
            "difficulty": "Medium",
            "estimated_cost": "Medium (₹5k - ₹25k)",
            "required_resources": "Galvanized steel mesh, local metal fabricator/welder, secure locking latches.",
            "expected_benefit": "Prevents catastrophic underground blockages and allows quick visual inspection and surface raking by municipal workers.",
            "possible_limitations": "Must be raked regularly after storms to prevent surface debris from matting over the grate.",
            "feasibility_assessment": "High (Locally sourced materials; no electrical power or complex software needed).",
            "why_matches": "Directly tackles root cause of urban stormwater choking at entry points without costly pipe replacement."
        },
        {
            "title": "Crowdsourced Civic Geo-Tagging & Maintenance Tracker",
            "description": "A lightweight mobile web dashboard allowing residents to pin photo-verified coordinates of damaged infrastructure and track civic agency response times publicly.",
            "difficulty": "Medium",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "OpenStreetMap / Leaflet.js, lightweight backend, cloud photo storage.",
            "expected_benefit": "Provides structured, transparent photographic evidence for ward counselors and municipal engineers.",
            "possible_limitations": "Relies on resident participation and responsive civic authority follow-through.",
            "feasibility_assessment": "High (Builds on open web standards with minimal compute overhead).",
            "why_matches": "Transforms sporadic verbal complaints into geo-tagged, verifiable civic data logs."
        }
    ],
    "Social & Campus": [
        {
            "title": "Peer-to-Peer Resource Circulation & Notification Dispatch",
            "description": "A scheduled notification broadcast system connecting surplus resources (such as cafeteria meals, lab equipment, or textbooks) directly to verified student volunteers within a 30-minute reaction window.",
            "difficulty": "Low",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "Instant messaging webhook (WhatsApp / Telegram / Email), volunteer contact roster, food-grade thermal containers.",
            "expected_benefit": "Minimizes wastage of valuable resources while supporting under-resourced peers and local shelters.",
            "possible_limitations": "Dependent on dependable student volunteer shift turnouts during exam cycles.",
            "feasibility_assessment": "Very High (Simple tech stack, strong student community empathy and engagement).",
            "why_matches": "Connects supply and demand in real-time within a localized geographic radius."
        }
    ],
    "Environmental": [
        {
            "title": "Low-Power Telemetry & Early Warning Sentinel Unit",
            "description": "Deploy battery/solar-powered microcontroller nodes equipped with dedicated environmental probes (pH, turbidity, particulate matter) logging sensor data to a centralized dashboard.",
            "difficulty": "Medium",
            "estimated_cost": "Medium (₹5k - ₹25k)",
            "required_resources": "ESP32 or Arduino micro-controllers, calibrated analog sensors, solar trickle charger, weather-sealed IP65 casing.",
            "expected_benefit": "Enables proactive warning hours before contamination levels reach critical thresholds.",
            "possible_limitations": "Sensors require periodic cleaning and field calibration every 3-6 months.",
            "feasibility_assessment": "Medium (Requires basic electronics fabrication skills and field waterproofing).",
            "why_matches": "Replaces slow, sporadic manual sampling with continuous automated monitoring."
        }
    ],
    "Engineering & Innovation": [
        {
            "title": "Shock-Absorbing Elastomeric Metamaterial Protective Chassis",
            "description": "Design an energy-dissipating lattice structure using viscoelastic foams or non-Newtonian polymers that disperse perpendicular drop energy laterally away from delicate internal electronic components.",
            "difficulty": "Medium",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "Parametric CAD models, 3D printer (TPU / Flexible resin), viscoelastic foam stock.",
            "expected_benefit": "Absorbs up to 80% of kinetic impact energy from 1.5m drops onto unyielding surfaces.",
            "possible_limitations": "Requires iterative dimensional tuning for individual device tolerances.",
            "feasibility_assessment": "High (Rapidly manufacturable on standard institutional additive equipment).",
            "why_matches": "Directly mitigates structural failure points and drop vulnerability through materials engineering."
        },
        {
            "title": "Active Free-Fall Sensor-Triggered Tension Latching",
            "description": "Utilize existing onboard accelerometer hardware to detect zero-G free-fall states and actuate electromagnetic or tension-spring latches to protect screen hinges and fragile disk heads before impact.",
            "difficulty": "High",
            "estimated_cost": "Medium (₹5k - ₹25k)",
            "required_resources": "Low-latency IMU sensor, solenoid or spring latch, micro-controller firmware.",
            "expected_benefit": "Provides sub-150ms structural defense before physical impact occurs.",
            "possible_limitations": "Complex integration with external device shells.",
            "feasibility_assessment": "Medium (Requires precision electromechanical prototyping).",
            "why_matches": "Proactively shields delicate hinges and joints prior to deceleration impact."
        }
    ],
    "Healthcare Accessibility": [
        {
            "title": "Passive Phase-Change Cold-Chain Carrier & Telemetry Logger",
            "description": "A thermally insulated vaccine carrier utilizing non-toxic phase-change material (PCM) packs to hold strict 2-8°C storage for up to 48 hours without grid power, paired with a BLE temperature logger.",
            "difficulty": "Medium",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "Vacuum insulation panels, 5°C phase-change packs, low-cost BLE temperature beacon.",
            "expected_benefit": "Prevents cold-chain breakage in remote clinics during extended blackouts.",
            "possible_limitations": "PCM packs require pre-conditioning before dispatch.",
            "feasibility_assessment": "Very High (Proven thermal physics, zero moving parts).",
            "why_matches": "Eliminates electricity dependence for medical cold-chain integrity."
        }
    ],
    "College & Student Life": [
        {
            "title": "Campus Peer-Escort & Night-Transit Companion Network",
            "description": "A student-operated mobile web service matching peers walking along similar campus paths after late study hours, featuring QR safety check-ins and emergency route beacons.",
            "difficulty": "Low",
            "estimated_cost": "Zero / Free",
            "required_resources": "Lightweight web app, student identity verification, volunteer escort roster.",
            "expected_benefit": "Ensures no student walks isolated at late hours, dramatically boosting campus transit safety.",
            "possible_limitations": "Requires consistent volunteer presence during exam cycles.",
            "feasibility_assessment": "Very High (Minimal tech overhead, strong community engagement).",
            "why_matches": "Organizes collective student presence to overcome isolated vulnerability."
        }
    ],
    "Education & Learning": [
        {
            "title": "Multimodal Audio-Tactile STEM Measurement Interface",
            "description": "Convert standard digital laboratory sensors into voice-synthesized and braille-labeled readouts, enabling visually impaired students to participate in experimental science autonomously.",
            "difficulty": "Low",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "Arduino / Raspberry Pi Pico, speech synthesizer module, 3D tactile braille enclosure.",
            "expected_benefit": "Provides independent laboratory experimentation for students with disabilities.",
            "possible_limitations": "Must be calibrated against standard bench instruments.",
            "feasibility_assessment": "High (Readily available open-source hardware modules).",
            "why_matches": "Bridges the sensory gap in experimental science education."
        }
    ],
    "Government & Civic Services": [
        {
            "title": "Civic Geo-Tagging & Municipal Service SLA Dashboard",
            "description": "A community transparency portal allowing residents to submit verified photos with GPS coordinates of infrastructure failures, tracking civic agency repair timelines publicly.",
            "difficulty": "Low",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "OpenStreetMap / Leaflet, mobile camera web interface, CPGRAMS / municipal mail gateway.",
            "expected_benefit": "Transforms scattered complaints into verifiable, clustered civic data.",
            "possible_limitations": "Requires municipal responsiveness to achieve resolution.",
            "feasibility_assessment": "High (Standard web mapping technology).",
            "why_matches": "Creates transparent public accountability for infrastructure maintenance."
        }
    ],
    "General / Other": [
        {
            "title": "Modular Community Pilot Program & Rapid Prototyping Cycle",
            "description": "Establish a structured 3-phase pilot: (1) Baseline measurement of the bottleneck, (2) 14-day low-cost test with an initial cohort of 20 users, and (3) Quantitative evaluation against target milestones before scaling.",
            "difficulty": "Low",
            "estimated_cost": "Low (< ₹5,000)",
            "required_resources": "Feedback forms, cohort communication group, documented measurement rubric.",
            "expected_benefit": "Validates core user assumptions with minimal financial exposure before investing substantial time or capital.",
            "possible_limitations": "Requires committed test participants to provide honest, constructive weekly feedback.",
            "feasibility_assessment": "High (Standard agile innovation methodology adaptable to any field).",
            "why_matches": "Provides a clear scientific framework for testing hypotheses under real constraints."
        }
    ]
}


def get_curated_suggestions(problem_category, problem_text):
    """
    Retrieves curated engineering and community solution patterns
    matched to the problem's domain and keywords.
    """
    suggestions = []
    cat_key = "General / Other"
    
    # Domain matching
    for key in DOMAIN_KNOWLEDGE_TEMPLATES:
        if key.lower() in (problem_category or "").lower():
            cat_key = key
            break

    # Pull domain patterns
    base_templates = DOMAIN_KNOWLEDGE_TEMPLATES.get(cat_key, DOMAIN_KNOWLEDGE_TEMPLATES["General / Other"])
    
    for t in base_templates:
        item = dict(t)
        item["is_algorithmic_suggestion"] = True
        item["source"] = "Curated Impact Knowledge Base"
        suggestions.append(item)

    # If general, also supplement with adjacent category ideas
    if cat_key == "General / Other":
        for t in DOMAIN_KNOWLEDGE_TEMPLATES["Technology & Operations"][:1]:
            item = dict(t)
            item["is_algorithmic_suggestion"] = True
            item["source"] = "Curated Impact Knowledge Base"
            suggestions.append(item)

    return suggestions


def generate_external_ai_suggestion(problem_title, problem_description, problem_category, constraints=""):
    """
    Optional external AI integration if GEMINI_API_KEY is defined in environment.
    If not defined or on network error, gracefully returns None.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = f"""
You are an engineering advisor for IMPACT LAB.
Suggest a practical, low-cost, scalable solution for this problem:
Title: {problem_title}
Category: {problem_category}
Description: {problem_description}
Constraints: {constraints}

Respond with ONLY valid JSON with keys:
"title", "description", "required_resources", "difficulty" (Low/Medium/High),
"estimated_cost", "expected_benefit", "possible_limitations", "feasibility_assessment", "why_matches"
"""
        req_body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(req_body).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content_text)
            parsed["is_algorithmic_suggestion"] = True
            parsed["source"] = "Gemini AI Advisor"
            return parsed
    except Exception:
        # Graceful fallback: return None on any failure so local engine handles it
        return None
