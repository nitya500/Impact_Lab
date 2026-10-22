"""
IMPACT LAB - Main Web Application
Problem-to-Impact Platform
====================================
Tagline: From Ideas to Tested Impact
Built with Python, Flask & SQLite.
"""

import os
import json
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, flash, abort
)

# Custom Modules
import database
import nlp_engine
import feasibility_engine
import gov_portal
import ai_suggester

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "impact_lab_session_secret_key_2026")

# Ensure database and seed data are initialized
database.init_db()


# ==============================================================================
# Web Page Routes
# ==============================================================================

@app.route("/")
def home():
    """
    Homepage: Displays platform branding, hero section, live metrics from SQLite,
    the 5-step methodology, and featured problems.
    """
    stats = database.get_platform_statistics()
    all_probs = database.get_all_problems()
    
    # Enhance problems with their solution counts for display
    conn = database.get_db_connection()
    featured_problems = []
    for p in all_probs[:6]:
        sol_count = conn.execute(
            "SELECT COUNT(*) FROM solutions WHERE problem_id = ?", (p["id"],)
        ).fetchone()[0]
        eval_row = conn.execute(
            "SELECT overall_score FROM feasibility_evaluations WHERE problem_id = ? ORDER BY id DESC LIMIT 1",
            (p["id"],)
        ).fetchone()
        p_dict = dict(p)
        p_dict["solution_count"] = sol_count
        p_dict["latest_eval_score"] = round(eval_row[0], 1) if eval_row else None
        featured_problems.append(p_dict)
    conn.close()

    return render_template(
        "index.html",
        stats=stats,
        featured_problems=featured_problems
    )


@app.route("/dashboard")
def dashboard_page():
    """
    Impact Dashboard: Real-time platform analytics, category breakdown,
    lifecycle stage distribution, solution complexity metrics, and recent activity feed.
    """
    stats = database.get_platform_statistics()
    recent_problems = database.get_all_problems()[:6]
    all_solutions = database.get_all_solutions()[:6]
    recent_evaluations = database.get_recent_evaluations(limit=6)

    # Attach solution counts to recent problems
    conn = database.get_db_connection()
    problems_with_counts = []
    for p in recent_problems:
        sol_count = conn.execute(
            "SELECT COUNT(*) FROM solutions WHERE problem_id = ?", (p["id"],)
        ).fetchone()[0]
        p_dict = dict(p)
        p_dict["solution_count"] = sol_count
        problems_with_counts.append(p_dict)
    conn.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_problems=problems_with_counts,
        all_solutions=all_solutions,
        recent_evaluations=recent_evaluations
    )


@app.route("/problems")
def problems_page():
    """
    Problem Explorer & Dashboard:
    Search by keywords, filter by category or status, sort by newest, oldest, severity, or solutions.
    """
    search_query = request.args.get("q", "").strip()
    category = request.args.get("category", "All").strip()
    status = request.args.get("status", "All").strip()
    sort = request.args.get("sort", "newest").strip()

    raw_problems = database.get_all_problems(
        search=search_query if search_query else None,
        category=category,
        status=status,
        sort=sort
    )

    # Attach solution counts & latest evaluation score
    conn = database.get_db_connection()
    problems = []
    for p in raw_problems:
        sol_count = conn.execute(
            "SELECT COUNT(*) FROM solutions WHERE problem_id = ?", (p["id"],)
        ).fetchone()[0]
        eval_row = conn.execute(
            "SELECT overall_score FROM feasibility_evaluations WHERE problem_id = ? ORDER BY id DESC LIMIT 1",
            (p["id"],)
        ).fetchone()
        p_dict = dict(p)
        p_dict["solution_count"] = sol_count
        p_dict["latest_eval_score"] = round(eval_row[0], 1) if eval_row else None
        problems.append(p_dict)
    conn.close()

    if sort == "solutions":
        problems.sort(key=lambda x: x["solution_count"], reverse=True)

    return render_template(
        "problems.html",
        problems=problems,
        search_query=search_query,
        selected_category=category,
        selected_status=status,
        selected_sort=sort
    )


@app.route("/submit", methods=["GET"])
def submit_problem_page():
    """Renders the comprehensive problem submission form."""
    return render_template("submit.html")


@app.route("/submit", methods=["POST"])
def submit_problem_action():
    """
    Handles problem submission with dual-layer validation and persistent storage.
    Supports optional immediate transition to Feasibility Evaluation if a solution idea is supplied.
    """
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    user_type = request.form.get("user_type", "Help Seeker").strip()
    description = request.form.get("description", "").strip()
    keywords = request.form.get("keywords", "").strip()
    location = request.form.get("location", "").strip()
    expected_impact = request.form.get("expected_impact", "").strip()
    constraints = request.form.get("constraints", "").strip()
    available_resources = request.form.get("available_resources", "").strip()
    proposed_solution = request.form.get("proposed_solution", "").strip()
    contact_email = request.form.get("contact_email", "").strip()
    severity = request.form.get("severity", "Medium").strip()

    # Backend Validation
    if len(title) < 5:
        flash("Problem title must be at least 5 characters long.", "danger")
        return redirect(url_for("submit_problem_page"))

    if not category:
        flash("Please select a problem domain category.", "danger")
        return redirect(url_for("submit_problem_page"))

    if len(description) < 20:
        flash("Please provide a more detailed problem description (at least 20 characters).", "danger")
        return redirect(url_for("submit_problem_page"))

    # Auto-extract keywords if user didn't enter any
    if not keywords:
        auto_kws = nlp_engine.extract_keywords(f"{title} {description}", top_n=6)
        keywords = ", ".join(auto_kws)

    # Insert into SQLite
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open')
    """, (
        title, description, category, keywords, location, expected_impact, constraints, available_resources, proposed_solution, user_type, contact_email, severity
    ))
    new_id = cursor.lastrowid

    # If user provided a proposed solution, automatically record it in the solutions table as well
    if proposed_solution and len(proposed_solution) >= 5:
        cursor.execute("""
        INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status)
        VALUES (?, ?, ?, ?, ?, 'Problem Submitter', ?, 'Medium', 'Low (< ₹5,000)', ?, 4, 'Proposed')
        """, (
            new_id,
            f"Submitter Concept: {title[:50]}",
            proposed_solution,
            category,
            user_type,
            available_resources or constraints or "Standard tools",
            expected_impact or "Initial community relief"
        ))

    conn.commit()
    conn.close()

    flash(f"Problem #{new_id} successfully registered in IMPACT LAB!", "success")
    return redirect(url_for("problem_details_page", problem_id=new_id))


@app.route("/problems/<int:problem_id>")
def problem_details_page(problem_id):
    """
    Problem Details View:
    Displays problem information, civic portal advisories if public infrastructure,
    all proposed solutions with lifecycle stages, and associated help requests.
    """
    problem = database.get_problem_by_id(problem_id)
    if not problem:
        abort(404)

    solutions = database.get_solutions_for_problem(problem_id)

    # Fetch linked help requests
    conn = database.get_db_connection()
    help_requests = conn.execute(
        "SELECT * FROM help_requests WHERE problem_id = ? ORDER BY id DESC",
        (problem_id,)
    ).fetchall()
    conn.close()
    help_requests = [dict(h) for h in help_requests]

    # Detect Government / Civic channel relevance
    combined_text = f"{problem['title']} {problem['description']} {problem.get('keywords', '')}"
    gov_data = gov_portal.detect_government_relevance(problem["category"], combined_text)

    return render_template(
        "problem_detail.html",
        problem=problem,
        solutions=solutions,
        help_requests=help_requests,
        gov_data=gov_data
    )


@app.route("/solutions/propose", methods=["POST"])
def submit_solution_action():
    """Submits a new proposed solution for an existing problem."""
    problem_id = request.form.get("problem_id", type=int)
    title = request.form.get("title", "").strip()
    author_name = request.form.get("author_name", "Community Contributor").strip()
    author_type = request.form.get("author_type", "Independent Contributor").strip()
    description = request.form.get("description", "").strip()
    difficulty = request.form.get("difficulty", "Medium").strip()
    estimated_cost = request.form.get("estimated_cost", "Low (< ₹5,000)").strip()
    time_weeks = request.form.get("time_weeks", 4, type=int)
    required_resources = request.form.get("required_resources", "").strip()
    expected_benefit = request.form.get("expected_benefit", "").strip()

    if not problem_id or not title or not description:
        flash("Solution title and description are required.", "danger")
        return redirect(url_for("problems_page"))

    problem = database.get_problem_by_id(problem_id)
    if not problem:
        abort(404)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Proposed')
    """, (
        problem_id, title, description, problem["category"], author_name, author_type, required_resources, difficulty, estimated_cost, expected_benefit, time_weeks
    ))
    conn.commit()
    conn.close()

    flash("Your proposed solution has been posted successfully!", "success")
    return redirect(url_for("problem_details_page", problem_id=problem_id))


@app.route("/solutions/update-status", methods=["POST"])
def update_solution_status():
    """Updates field test progress and records actual measured results."""
    solution_id = request.form.get("solution_id", type=int)
    problem_id = request.form.get("problem_id", type=int)
    status = request.form.get("status", "Proposed")
    target_metric = request.form.get("target_metric", "").strip()
    actual_result = request.form.get("actual_result", "").strip()

    if not solution_id:
        flash("Invalid solution ID.", "danger")
        return redirect(url_for("problems_page"))

    conn = database.get_db_connection()
    conn.execute("""
    UPDATE solutions
    SET status = ?, target_metric = ?, actual_result = ?
    WHERE id = ?
    """, (status, target_metric, actual_result, solution_id))

    # Also update problem status if testing or resolved
    if status == "Testing":
        conn.execute("UPDATE problems SET status = 'Testing' WHERE id = ?", (problem_id,))
    elif status == "Result Recorded":
        conn.execute("UPDATE problems SET status = 'Resolved' WHERE id = ?", (problem_id,))

    conn.commit()
    conn.close()

    flash("Testing status and measured outcome updated!", "success")
    return redirect(url_for("problem_details_page", problem_id=problem_id))


@app.route("/discover")
def discover_page():
    """
    Solution Discovery Engine:
    Uses TF-IDF Vectorizer and Cosine Similarity to compare query text with
    existing database solutions, ranks them, extracts keywords, and provides
    clear explanations and fallback blueprints.
    """
    all_problems = database.get_all_problems()
    problem_id = request.args.get("problem_id", type=int)
    custom_query = request.args.get("q", "").strip()

    query_text = ""
    problem_category = "General / Other"
    has_searched = False
    ranked_results = []
    extracted_keywords = []
    curated_suggestions = []

    # 1. Determine query context
    if problem_id:
        target_problem = database.get_problem_by_id(problem_id)
        if target_problem:
            query_text = f"{target_problem['title']} {target_problem['description']} {target_problem.get('keywords', '')}"
            problem_category = target_problem["category"]
            has_searched = True
    elif custom_query:
        query_text = custom_query
        has_searched = True

    # 2. Run TF-IDF Matching Engine if a query is specified
    if has_searched and query_text:
        extracted_keywords = nlp_engine.extract_keywords(query_text, top_n=8)
        all_solutions = database.get_all_solutions()
        
        # Rank matching solutions from database
        ranked_results = nlp_engine.rank_matching_solutions(query_text, all_solutions)

        # Retrieve curated domain blueprints (heuristics)
        curated_suggestions = ai_suggester.get_curated_suggestions(problem_category, query_text)

    return render_template(
        "discover.html",
        all_problems=all_problems,
        selected_problem_id=problem_id,
        custom_query=custom_query,
        query_text=query_text,
        has_searched=has_searched,
        ranked_results=ranked_results,
        extracted_keywords=extracted_keywords,
        curated_suggestions=curated_suggestions
    )


@app.route("/evaluate", methods=["GET"])
def evaluate_page():
    """
    Solution Feasibility & Impact Calculator:
    Interactive sliders evaluating proposals across 6 MCDA dimensions.
    """
    solution_title = request.args.get("title", "")
    problem_id = request.args.get("problem_id", type=int)

    # Initial default scores
    initial_scores = {
        "expected_benefit": 8,
        "technical_feasibility": 7,
        "cost_fit": 8,
        "implementation_time": 8,
        "resource_availability": 7,
        "scalability": 8,
        "risk_level": 3
    }

    # Run default calculation
    evaluation = feasibility_engine.calculate_feasibility(initial_scores)

    return render_template(
        "evaluate.html",
        solution_title=solution_title,
        problem_id=problem_id,
        initial_scores=initial_scores,
        evaluation=evaluation
    )


@app.route("/evaluate", methods=["POST"])
def evaluate_action():
    """
    Calculates feasibility score from submitted parameters,
    saves the evaluation into SQLite, and displays results.
    """
    solution_title = request.form.get("solution_title", "Proposed Innovation").strip()
    problem_id = request.form.get("problem_id", type=int)

    inputs = {
        "expected_benefit": float(request.form.get("expected_benefit", 8)),
        "technical_feasibility": float(request.form.get("technical_feasibility", 7)),
        "cost_fit": float(request.form.get("cost_fit", 8)),
        "implementation_time": float(request.form.get("implementation_time", 8)),
        "resource_availability": float(request.form.get("resource_availability", 7)),
        "scalability": float(request.form.get("scalability", 8)),
        "risk_level": float(request.form.get("risk_level", 3)),
        "solution_title": solution_title
    }

    evaluation = feasibility_engine.calculate_feasibility(inputs)

    # Persist in SQLite
    conn = database.get_db_connection()
    conn.execute("""
    INSERT INTO feasibility_evaluations (problem_id, solution_title, overall_score, criteria_scores, positive_factors, risks, recommendations, explanation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        problem_id,
        solution_title,
        evaluation["overall_score"],
        json.dumps(evaluation["criteria_breakdown"]),
        json.dumps(evaluation["positive_factors"]),
        json.dumps(evaluation["risks"]),
        json.dumps(evaluation["recommendations"]),
        evaluation["explanation"]
    ))
    conn.commit()
    conn.close()

    flash("Feasibility evaluation calculated and saved to registry!", "success")

    return render_template(
        "evaluate.html",
        solution_title=solution_title,
        problem_id=problem_id,
        initial_scores=inputs,
        evaluation=evaluation
    )


@app.route("/help-network")
def help_network_page():
    """
    Help Seeker & Help Giver Hub:
    Displays open help inquiries, volunteer helper directory, and submission forms.
    Filtered by keyword search, category, or lifecycle status.
    """
    search_query = request.args.get("q", "").strip()
    category = request.args.get("category", "All").strip()
    status = request.args.get("status", "All").strip()

    requests_list = database.get_all_help_requests(
        search=search_query if search_query else None,
        category=category,
        status=status
    )

    conn = database.get_db_connection()
    # Fetch registered helpers
    helpers_data = conn.execute("SELECT * FROM helpers ORDER BY id DESC").fetchall()
    helpers_list = [dict(h) for h in helpers_data]

    # Fetch recorded helper interests so cards show actual community assistance offers
    interests_data = conn.execute("""
    SELECT hi.*, hr.title as request_title
    FROM helper_interests hi
    JOIN help_requests hr ON hi.help_request_id = hr.id
    ORDER BY hi.id DESC
    """).fetchall()
    interests_list = [dict(i) for i in interests_data]

    conn.close()

    all_problems = database.get_all_problems()

    return render_template(
        "help_network.html",
        requests=requests_list,
        helpers=helpers_list,
        interests=interests_list,
        all_problems=all_problems,
        search_query=search_query,
        selected_category=category,
        selected_status=status
    )


@app.route("/help-network/request", methods=["POST"])
def create_help_request_action():
    """Creates a new help request with domain categorization."""
    title = request.form.get("title", "").strip()
    problem_id = request.form.get("problem_id", type=int)
    category = request.form.get("category", "General").strip()
    skills_needed = request.form.get("skills_needed", "").strip()
    urgency = request.form.get("urgency", "Normal")
    description = request.form.get("description", "").strip()
    contact_name = request.form.get("contact_name", "").strip()
    contact_info = request.form.get("contact_info", "").strip()

    if not title or not skills_needed or not description:
        flash("Title, required skills, and description are required.", "danger")
        return redirect(url_for("help_network_page"))

    conn = database.get_db_connection()
    conn.execute("""
    INSERT INTO help_requests (problem_id, title, description, skills_needed, category, urgency, status, contact_name, contact_info)
    VALUES (?, ?, ?, ?, ?, ?, 'Open', ?, ?)
    """, (problem_id, title, description, skills_needed, category, urgency, contact_name, contact_info))
    conn.commit()
    conn.close()

    flash("Help request posted to the network!", "success")
    return redirect(url_for("help_network_page"))


@app.route("/help-network/update-status", methods=["POST"])
def update_help_status_action():
    """Allows users to update help request lifecycle status (Open, In Progress, Resolved)."""
    request_id = request.form.get("request_id", type=int)
    new_status = request.form.get("status", "Open").strip()

    if not request_id or new_status not in ["Open", "In Progress", "Resolved"]:
        flash("Invalid request ID or status.", "danger")
        return redirect(url_for("help_network_page"))

    database.update_help_request_status(request_id, new_status)
    flash(f"Help Request #{request_id} status updated to '{new_status}'!", "success")
    return redirect(url_for("help_network_page"))


@app.route("/help-network/volunteer", methods=["POST"])
def register_helper_action():
    """Registers a new volunteer solver in the standing directory."""
    name = request.form.get("name", "").strip()
    contact = request.form.get("contact", "").strip()
    category = request.form.get("category", "Technology").strip()
    skills = request.form.get("skills", "").strip()
    description = request.form.get("description", "").strip()
    availability = request.form.get("availability", "Available Volunteer").strip()

    if not name or not skills or not contact:
        flash("Name, contact info, and skills are required.", "danger")
        return redirect(url_for("help_network_page") + "#register-helper")

    conn = database.get_db_connection()
    conn.execute("""
    INSERT INTO helpers (name, skills, category, description, contact, availability)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (name, skills, category, description, contact, availability))
    conn.commit()
    conn.close()

    flash("Thank you for joining as a volunteer solver!", "success")
    return redirect(url_for("help_network_page") + "#tab-helpersDirectory")


@app.route("/help-network/express-interest", methods=["POST"])
def express_help_interest_action():
    """Allows a solver to express interest in fulfilling a specific help request."""
    help_request_id = request.form.get("help_request_id", type=int)
    helper_name = request.form.get("helper_name", "").strip()
    helper_email = request.form.get("helper_email", "").strip()
    skills = request.form.get("skills", "").strip()
    message = request.form.get("message", "").strip()

    if not help_request_id or not helper_name or not helper_email:
        flash("Name and email are required to offer help.", "danger")
        return redirect(url_for("help_network_page"))

    conn = database.get_db_connection()
    conn.execute("""
    INSERT INTO helper_interests (help_request_id, helper_name, helper_email, skills, message)
    VALUES (?, ?, ?, ?, ?)
    """, (help_request_id, helper_name, helper_email, skills, message))

    # Mark help request as In Progress if it was Open
    conn.execute("UPDATE help_requests SET status = 'In Progress' WHERE id = ?", (help_request_id,))

    conn.commit()
    conn.close()

    flash("Your offer of assistance has been recorded! The project lead has been notified.", "success")
    return redirect(url_for("help_network_page"))


@app.route("/about")
def about_page():
    """
    About IMPACT LAB:
    Presents the platform philosophy, the 5-step problem-to-impact journey,
    architectural modules, mathematical formulations for TF-IDF and MCDA, and FAQ.
    """
    return render_template("about.html")


# ==============================================================================
# REST API Endpoints (Backward Compatible with original prototype & scripts)
# ==============================================================================

@app.route("/api/problems", methods=["GET"])
def api_get_problems():
    """Returns all problems from SQLite database."""
    problems = database.get_all_problems()
    return jsonify(problems)


@app.route("/api/problems", methods=["POST"])
def api_create_problem():
    """JSON API to submit a problem into SQLite."""
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    category = data.get("category", "").strip()
    proposed_solution = data.get("proposed_solution", "").strip()
    user_type = data.get("user_type", "Help Seeker").strip()
    keywords = data.get("keywords", "").strip()
    location = data.get("location", "").strip()
    expected_impact = data.get("expected_impact", "").strip()
    constraints = data.get("constraints", "").strip()

    if not title or not description or not category:
        return jsonify({"error": "Please complete all required fields."}), 400

    if not keywords:
        auto_kws = nlp_engine.extract_keywords(f"{title} {description}", top_n=6)
        keywords = ", ".join(auto_kws)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO problems (title, description, category, keywords, location, expected_impact, constraints, proposed_solution, user_type, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open')
    """, (title, description, category, keywords, location, expected_impact, constraints, proposed_solution, user_type))
    problem_id = cursor.lastrowid
    conn.commit()
    conn.close()

    problem = database.get_problem_by_id(problem_id)
    return jsonify({
        "message": "Problem submitted successfully!",
        "problem": problem
    }), 201


@app.route("/api/helpers", methods=["GET"])
def api_get_helpers():
    """Returns all registered helpers."""
    conn = database.get_db_connection()
    helpers = conn.execute("SELECT * FROM helpers ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(h) for h in helpers])


@app.route("/api/helpers", methods=["POST"])
def api_create_helper():
    """JSON API to register a help giver."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    skills = data.get("skills", "").strip()
    description = data.get("description", "").strip()
    contact = data.get("contact", "").strip()

    if not name or not skills:
        return jsonify({"error": "Name and skills are required."}), 400

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO helpers (name, skills, description, contact)
    VALUES (?, ?, ?, ?)
    """, (name, skills, description, contact))
    helper_id = cursor.lastrowid
    conn.commit()
    
    helper = conn.execute("SELECT * FROM helpers WHERE id = ?", (helper_id,)).fetchone()
    conn.close()

    return jsonify({
        "message": "Help Giver registered successfully!",
        "helper": dict(helper)
    }), 201


@app.route("/api/solutions", methods=["GET"])
def api_get_solutions():
    """Returns all proposed solutions."""
    solutions = database.get_all_solutions()
    return jsonify(solutions)


@app.route("/api/solutions", methods=["POST"])
def api_create_solution():
    """JSON API to submit a proposed solution."""
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id")
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    author_name = data.get("author_name", "Community Solver").strip()

    if not title or not description:
        return jsonify({"error": "Solution title and description are required."}), 400

    if not isinstance(problem_id, int):
        return jsonify({"error": "A valid problem ID is required."}), 400

    problem = database.get_problem_by_id(problem_id)
    if problem is None:
        return jsonify({"error": "Problem not found."}), 404

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO solutions (problem_id, title, description, category, author_name, status)
    VALUES (?, ?, ?, ?, ?, 'Proposed')
    """, (problem_id, title, description, problem["category"], author_name))
    sol_id = cursor.lastrowid
    conn.commit()
    sol = conn.execute("SELECT * FROM solutions WHERE id = ?", (sol_id,)).fetchone()
    conn.close()

    return jsonify({
        "message": "Solution submitted successfully!",
        "solution": dict(sol)
    }), 201


@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """JSON API returning platform statistics."""
    stats = database.get_platform_statistics()
    return jsonify(stats)


@app.route("/api/dashboard", methods=["GET"])
def api_get_dashboard():
    """JSON API returning full platform metrics and breakdown data for dashboards."""
    stats = database.get_platform_statistics()
    return jsonify(stats)


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate_solution():
    """JSON API to evaluate a solution idea via MCDA."""
    data = request.get_json(silent=True) or {}
    result = feasibility_engine.calculate_feasibility(data)
    return jsonify(result)


@app.route("/api/discover", methods=["POST"])
def api_discover_solutions():
    """JSON API to run semantic TF-IDF matching on an arbitrary query."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query text is required."}), 400

    all_solutions = database.get_all_solutions()
    ranked = nlp_engine.rank_matching_solutions(query, all_solutions)
    return jsonify({
        "query": query,
        "extracted_keywords": nlp_engine.extract_keywords(query),
        "results_count": len(ranked),
        "results": ranked
    })


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template(
        "problems.html",
        problems=database.get_all_problems(),
        search_query="",
        selected_category="All",
        selected_status="All"
    ), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error occurred."}), 500


if __name__ == "__main__":
    # Runs locally at http://127.0.0.1:5000/ and across local network
    app.run(debug=True, host="0.0.0.0", port=5000)
