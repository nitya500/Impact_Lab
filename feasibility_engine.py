"""
IMPACT LAB - Solution Feasibility & Impact Scoring Engine
Problem-to-Impact Platform
=========================================================
Transparent Multi-Criteria Decision Analysis (MCDA) Scoring Algorithm.

Criteria & Weights:
1. Expected Benefit & Social Impact (Weight: 25%)
2. Technical Feasibility (Weight: 20%)
3. Cost Fit / Budget Viability (Weight: 15%)
4. Implementation Speed & Timeframe (Weight: 15%)
5. Resource & Skill Availability (Weight: 15%)
6. Scalability & Replicability (Weight: 10%)
- Risk & Uncertainty Penalty (Deduction: up to 13.5 points)

Outputs:
- Overall Feasibility Score (0 - 100)
- Feasibility Tier (e.g., High Potential, Viable with Revisions, High Risk)
- Individual Criterion Breakdown
- Identified Positive Drivers
- Key Vulnerabilities & Risks
- Actionable Engineering/Execution Recommendations
- Mathematical Formulation & Scoring Breakdown
"""

CRITERIA_WEIGHTS = {
    "expected_benefit": {"weight": 0.25, "name": "Expected Benefit & Impact", "max_pts": 25.0},
    "technical_feasibility": {"weight": 0.20, "name": "Technical Feasibility", "max_pts": 20.0},
    "cost_fit": {"weight": 0.15, "name": "Cost Fit & Budget Viability", "max_pts": 15.0},
    "implementation_time": {"weight": 0.15, "name": "Implementation Speed & Timeframe", "max_pts": 15.0},
    "resource_availability": {"weight": 0.15, "name": "Resource & Skill Availability", "max_pts": 15.0},
    "scalability": {"weight": 0.10, "name": "Scalability & Replicability", "max_pts": 10.0}
}


def calculate_feasibility(inputs):
    """
    Evaluates a solution idea based on multi-criteria inputs.
    
    inputs dict expected keys (values 1 to 10 integer/float):
    - expected_benefit
    - technical_feasibility
    - cost_fit
    - implementation_time
    - resource_availability
    - scalability
    - risk_level (1 = minimal risk, 10 = critical unmitigated risk)
    - (optional) solution_title, problem_title, notes
    """
    scores = {}
    positive_factors = []
    risks = []
    recommendations = []

    # Parse and clamp inputs (1 to 10)
    for key in CRITERIA_WEIGHTS:
        val = float(inputs.get(key, 5))
        clamped = max(1.0, min(10.0, val))
        scores[key] = clamped

    risk_level = max(1.0, min(10.0, float(inputs.get("risk_level", 4))))
    scores["risk_level"] = risk_level

    # 1. Calculate Weighted Base Score
    base_score = 0.0
    criteria_breakdown = {}

    for key, meta in CRITERIA_WEIGHTS.items():
        val = scores[key]
        points_earned = (val / 10.0) * meta["max_pts"]
        base_score += points_earned
        criteria_breakdown[key] = {
            "name": meta["name"],
            "rating": val,
            "weight_percent": int(meta["weight"] * 100),
            "points_earned": round(points_earned, 2),
            "max_points": meta["max_pts"]
        }

        # Analyze positive and negative factors
        if val >= 8.0:
            positive_factors.append(f"Strong rating in {meta['name']} ({val}/10)")
        elif val <= 4.0:
            risks.append(f"Low rating in {meta['name']} ({val}/10) poses a project bottleneck")

    # 2. Risk Deduction: scales from 0 to 13.5 points deduction
    risk_penalty = round((risk_level - 1.0) * 1.5, 2)
    if risk_level >= 7.0:
        risks.append(f"Elevated overall risk factor ({risk_level}/10) requires active contingency planning")

    # Final overall score (0 to 100)
    final_score = round(max(0.0, min(100.0, base_score - risk_penalty)), 1)

    # 3. Determine Feasibility Tier
    if final_score >= 80.0:
        tier = "High Feasibility & High Impact"
        badge_class = "success"
        recommendations.append("The proposal demonstrates strong fundamentals. Proceed to build a rapid minimal prototype (MVP) to test core assumptions.")
    elif final_score >= 60.0:
        tier = "Viable with Targeted Modifications"
        badge_class = "info"
        recommendations.append("The core concept is sound, but specific constraints (such as budget or technical readiness) should be tightened before deployment.")
    elif final_score >= 40.0:
        tier = "Conditional / High Risk Proposal"
        badge_class = "warning"
        recommendations.append("High hurdles identified in implementation or resource availability. Consider simplifying scope or seeking domain mentorship.")
    else:
        tier = "Low Viability under Current Parameters"
        badge_class = "danger"
        recommendations.append("Current constraints make execution improbable. Re-evaluate core assumptions, seek low-cost alternative approaches, or pivot.")

    # Tailored recommendations based on specific weak criteria
    if scores["technical_feasibility"] < 6.0:
        recommendations.append("Technical complexity is high: break the solution down into smaller incremental modules or adopt proven open-source components.")
    if scores["cost_fit"] < 6.0:
        recommendations.append("Budget strain identified: explore open-source alternatives, volunteer labor, or community material donations to lower capital cost.")
    if scores["resource_availability"] < 6.0:
        recommendations.append("Skill gaps present: leverage the IMPACT LAB Help Network to recruit student contributors with relevant expertise.")
    if scores["implementation_time"] < 6.0:
        recommendations.append("Extended deployment timeline: define a 2-week 'Phase 1' pilot to demonstrate early feasibility before full-scale launch.")
    if scores["scalability"] < 6.0:
        recommendations.append("Low scalability: document the process systematically so other campus clubs or communities can replicate it without reinventing the wheel.")

    # Mathematical explanation string for formula breakdown
    calc_explanation = (
        f"Base score was calculated as the weighted sum of 6 criteria: "
        f"Benefit ({criteria_breakdown['expected_benefit']['points_earned']}/{criteria_breakdown['expected_benefit']['max_points']}) + "
        f"Tech ({criteria_breakdown['technical_feasibility']['points_earned']}/{criteria_breakdown['technical_feasibility']['max_points']}) + "
        f"Cost ({criteria_breakdown['cost_fit']['points_earned']}/{criteria_breakdown['cost_fit']['max_points']}) + "
        f"Time ({criteria_breakdown['implementation_time']['points_earned']}/{criteria_breakdown['implementation_time']['max_points']}) + "
        f"Resources ({criteria_breakdown['resource_availability']['points_earned']}/{criteria_breakdown['resource_availability']['max_points']}) + "
        f"Scalability ({criteria_breakdown['scalability']['points_earned']}/{criteria_breakdown['scalability']['max_points']}) = "
        f"{round(base_score, 1)} pts. "
        f"A risk penalty of {risk_penalty} pts was deducted based on an uncertainty rating of {risk_level}/10, "
        f"yielding a net score of {final_score}/100."
    )

    return {
        "overall_score": final_score,
        "base_score": round(base_score, 1),
        "risk_penalty": risk_penalty,
        "tier": tier,
        "badge_class": badge_class,
        "criteria_breakdown": criteria_breakdown,
        "positive_factors": positive_factors if positive_factors else ["Consistent baseline balance across evaluated categories."],
        "risks": risks if risks else ["No single severe failure mode detected, but monitoring remains necessary."],
        "recommendations": recommendations,
        "explanation": calc_explanation,
        "disclaimer": (
            "Disclaimer: This feasibility score is an algorithmic decision-support estimate based on subjective "
            "user ratings and defined MCDA weights. It is not an empirical laboratory measurement or a guarantee "
            "of project success."
        )
    }
