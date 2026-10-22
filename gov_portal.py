"""
IMPACT LAB - Government & Civic Portals Connect
Problem-to-Impact Platform
================================================
Provides verified routing and awareness for public infrastructure,
municipal services, and civic grievances.

IMPORTANT NOTICE & POLICY:
- IMPACT LAB is an independent innovation and problem-solving platform.
- It does NOT file legal or formal complaints on behalf of citizens.
- Verified official portals are provided solely for public reference and awareness.
- Citizens must independently check jurisdictional eligibility before submitting
  grievances to official government bodies.
"""

# Verified Indian Government Grievance & Civic Portals
VERIFIED_PORTALS = {
    "CPGRAMS": {
        "name": "CPGRAMS (Centralised Public Grievance Redress and Monitoring System)",
        "authority": "Department of Administrative Reforms and Public Grievances (DARPG), Govt. of India",
        "url": "https://pgportal.gov.in/",
        "description": "National single-window portal to lodge grievances against Central and State Government departments.",
        "domains": ["Government", "Public Infrastructure", "General Civic", "Other"]
    },
    "SWACHHATA": {
        "name": "Swachh Bharat Urban / Municipal Grievance Redressal",
        "authority": "Ministry of Housing and Urban Affairs (MoHUA)",
        "url": "https://swachhbharaturban.gov.in/",
        "description": "Official mechanism to report civic sanitation, garbage piles, open drains, and street cleanliness issues to local municipal corporations.",
        "domains": ["Public Infrastructure", "Sanitation", "Environment"]
    },
    "JAL_JEEVAN": {
        "name": "Jal Jeevan Mission Citizen Portal",
        "authority": "Department of Drinking Water and Sanitation, Ministry of Jal Shakti",
        "url": "https://jaljeevanmission.gov.in/",
        "description": "Information and grievance reporting regarding rural piped water supply, tap connections, and potable water testing.",
        "domains": ["Environment", "Water", "Public Infrastructure"]
    },
    "CYBER_CRIME": {
        "name": "National Cyber Crime Reporting Portal",
        "authority": "Ministry of Home Affairs (MHA), Govt. of India",
        "url": "https://cybercrime.gov.in/",
        "description": "Dedicated portal for citizens to report cyber crimes, online financial fraud, and digital identity theft.",
        "domains": ["Technology", "Security", "Finance"]
    },
    "MYGOV": {
        "name": "MyGov Citizen Innovation & Participatory Governance",
        "authority": "National Informatics Centre (NIC) / MeitY",
        "url": "https://www.mygov.in/",
        "description": "Platform for citizen suggestions, innovation challenges, and policy feedback to government bodies.",
        "domains": ["Government", "Innovation", "Community", "Education"]
    },
    "UMANG": {
        "name": "UMANG (Unified Mobile Application for New-age Governance)",
        "authority": "Ministry of Electronics and Information Technology (MeitY)",
        "url": "https://web.umang.gov.in/",
        "description": "Unified access to over 1,200 central and state government e-services, utilities, and certificates.",
        "domains": ["General Civic", "Public Infrastructure", "Government"]
    }
}

# Keywords triggering civic / government advisory
CIVIC_KEYWORDS = {
    "drain", "drainage", "waterlogging", "sewage", "road", "pothole", "streetlight",
    "garbage", "sanitation", "municipal", "panchayat", "water supply", "contamination",
    "cyber", "scam", "fraud", "police", "electricity", "transformer", "government",
    "public", "ration", "transport", "bus", "traffic", "pollution", "complaint", "civic"
}


def detect_government_relevance(category, text):
    """
    Determines if a problem relates to public infrastructure or government services,
    and returns matched verified portals along with responsible usage guidelines.
    """
    is_civic = False
    lower_cat = (category or "").lower()
    lower_text = (text or "").lower()

    if "infrastructure" in lower_cat or "government" in lower_cat or "environment" in lower_cat:
        is_civic = True

    matched_keywords = [kw for kw in CIVIC_KEYWORDS if kw in lower_text]
    if len(matched_keywords) >= 1:
        is_civic = True

    if not is_civic:
        return {
            "is_civic_related": False,
            "portals": [],
            "matched_keywords": [],
            "advisory_notice": None
        }

    # Match specific portals
    recommended_portals = []

    # Water / Sanitation
    if any(k in lower_text for k in ["water", "pipe", "turbidity", "drain", "waterlogging", "sewage", "cleanliness", "garbage"]):
        recommended_portals.append(VERIFIED_PORTALS["SWACHHATA"])
        recommended_portals.append(VERIFIED_PORTALS["JAL_JEEVAN"])

    # Cyber / IT
    if any(k in lower_text for k in ["cyber", "scam", "hack", "fraud", "phishing", "privacy"]):
        recommended_portals.append(VERIFIED_PORTALS["CYBER_CRIME"])

    # Default to CPGRAMS & MyGov for general public complaints
    if VERIFIED_PORTALS["CPGRAMS"] not in recommended_portals:
        recommended_portals.append(VERIFIED_PORTALS["CPGRAMS"])
    if VERIFIED_PORTALS["MYGOV"] not in recommended_portals:
        recommended_portals.append(VERIFIED_PORTALS["MYGOV"])

    return {
        "is_civic_related": True,
        "portals": recommended_portals[:3],
        "matched_keywords": matched_keywords[:5],
        "advisory_notice": (
            "This problem appears to touch upon public infrastructure or municipal services. "
            "While IMPACT LAB enables community-led technical solutions and prototypes, formal "
            "regulatory action and statutory repairs require verified escalation through official government channels. "
            "Please verify the appropriate jurisdiction (e.g. Municipal Corporation, Jal Board, or District Magistrate) "
            "before lodging an official grievance. IMPACT LAB does NOT file complaints on your behalf."
        )
    }
