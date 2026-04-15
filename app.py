from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
import os
import sqlite3
from datetime import datetime, date
from functools import wraps
from database import init_db, seed_db, get_db, check_password
from outreach import generate_email, generate_dm, generate_whatsapp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "octo-vision-secret-2024")


# ─── Auth helpers ─────────────────────────────────────────────────────────────


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    return {
        "id":        session.get("user_id"),
        "username":  session.get("username"),
        "full_name": session.get("full_name"),
        "role":      session.get("role"),
    } if session.get("user_id") else None


@app.context_processor
def inject_user():
    """Injecte current_user dans tous les templates automatiquement."""
    return {"current_user": get_current_user()}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def row_to_dict(row):
    d = dict(row)
    if isinstance(d.get("services_needed"), str):
        try:
            d["services_needed"] = json.loads(d["services_needed"])
        except Exception:
            d["services_needed"] = []
    return d


def get_score_label(score):
    if score >= 70:
        return "Très chaud", "hot"
    elif score >= 45:
        return "Chaud", "warm"
    elif score >= 20:
        return "Tiède", "lukewarm"
    else:
        return "Froid", "cold"


def build_vulnerabilities(p):
    vulnerabilities = []
    if not p["has_website"]:
        vulnerabilities.append({"icon": "globe", "label": "Pas de site web",
            "detail": "Aucun site web. 80% des clients cherchent en ligne avant de se déplacer.",
            "severity": "critical"})
    elif p["seo_score"] < 30:
        vulnerabilities.append({"icon": "search", "label": f"SEO très faible ({p['seo_score']}/100)",
            "detail": "Site web pratiquement invisible sur Google.", "severity": "critical"})
    elif p["seo_score"] < 50:
        vulnerabilities.append({"icon": "search", "label": f"SEO insuffisant ({p['seo_score']}/100)",
            "detail": "Le référencement peut être significativement amélioré.", "severity": "warning"})

    if not p["has_instagram"]:
        vulnerabilities.append({"icon": "camera", "label": "Absent sur Instagram",
            "detail": "Instagram est la plateforme n°1 pour les restaurants. Absence totale détectée.",
            "severity": "critical"})
    elif p["instagram_followers"] < 1000:
        vulnerabilities.append({"icon": "camera", "label": f"Instagram faible ({p['instagram_followers']} abonnés)",
            "detail": "Présence Instagram insuffisante pour générer de la visibilité.", "severity": "warning"})

    days = p["last_post_days_ago"]
    if days > 60:
        vulnerabilities.append({"icon": "calendar", "label": f"Inactif depuis {days} jours",
            "detail": "Aucune publication récente. L'audience se perd et l'algorithme pénalise.",
            "severity": "critical"})
    elif days > 30:
        vulnerabilities.append({"icon": "calendar", "label": f"Peu actif ({days} jours sans post)",
            "detail": "Fréquence de publication insuffisante pour maintenir l'engagement.",
            "severity": "warning"})

    if p["review_count"] < 50:
        vulnerabilities.append({"icon": "star", "label": f"Peu d'avis Google ({p['review_count']} avis)",
            "detail": "Un faible nombre d'avis réduit la crédibilité et le SEO local.", "severity": "warning"})

    if p["google_rating"] < 4.0 and p["review_count"] > 0:
        vulnerabilities.append({"icon": "alert", "label": f"Note Google faible ({p['google_rating']}/5)",
            "detail": "Une note en dessous de 4.0 dissuade fortement les nouveaux clients.",
            "severity": "critical"})

    if not p["has_facebook"] and not p["has_instagram"]:
        vulnerabilities.append({"icon": "phone", "label": "Aucun réseau social",
            "detail": "Absence totale sur les réseaux sociaux.", "severity": "critical"})

    if not p.get("email"):
        vulnerabilities.append({"icon": "mail", "label": "Pas d'email professionnel",
            "detail": "Aucun email de contact trouvé.", "severity": "info"})

    # Design graphique
    if not p.get("has_modern_menu"):
        quality = p.get("menu_board_quality", "unknown")
        if quality == "inexistant":
            vulnerabilities.append({"icon": "design", "label": "Aucun menu board / carte visuelle",
                "detail": "Pas de menu mural ni de carte graphique professionnelle. Opportunité directe de vente design.",
                "severity": "critical"})
        else:
            vulnerabilities.append({"icon": "design", "label": "Menu board / carte obsolète ou illisible",
                "detail": "La carte actuelle est ancienne, peu lisible ou peu attrayante. Un menu board moderne multiplie les commandes.",
                "severity": "warning"})

    if not p.get("has_pro_logo"):
        vulnerabilities.append({"icon": "logo", "label": "Identité visuelle inexistante ou amateure",
            "detail": "Pas de logo professionnel détecté. L'image de marque est un levier de confiance et de fidélisation.",
            "severity": "warning"})

    if not p.get("has_gmaps_photos"):
        vulnerabilities.append({"icon": "camera", "label": "Photos Google Maps insuffisantes ou absentes",
            "detail": "Les visuels Google Maps sont anciens ou inexistants. Les clients décident en 3 secondes selon les photos.",
            "severity": "warning"})

    return vulnerabilities


PIPELINE_STAGES = [
    ("new",           "Nouveau",        "#3b82f6"),
    ("contacted",     "Contacté",       "#f59e0b"),
    ("interested",    "Intéressé",      "#8b5cf6"),
    ("proposal_sent", "Devis envoyé",   "#ec4899"),
    ("closed_won",    "Gagné",          "#10b981"),
    ("closed_lost",   "Perdu",          "#ef4444"),
]

INTERACTION_TYPES = [
    ("appel",     "Appel téléphonique", "📞"),
    ("email",     "Email",              "📧"),
    ("reunion",   "Réunion",            "🤝"),
    ("dm",        "DM Instagram/FB",    "📱"),
    ("whatsapp",  "WhatsApp",           "💬"),
    ("note",      "Note interne",       "📝"),
]

OUTCOMES = [
    ("positif",      "Positif"),
    ("neutre",       "Neutre"),
    ("negatif",      "Négatif"),
    ("sans_reponse", "Sans réponse"),
    ("rappel",       "À rappeler"),
]

PRIORITY_CONFIG = {
    "urgent": ("Urgent",  "#ef4444"),
    "high":   ("Élevée",  "#f59e0b"),
    "medium": ("Normale", "#6366f1"),
    "low":    ("Faible",  "#6b7280"),
}


# ─── Login / Logout ───────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password(password, user["password_hash"]):
            session["user_id"]   = user["id"]
            session["username"]  = user["username"]
            session["full_name"] = user["full_name"]
            session["role"]      = user["role"]
            return redirect(url_for("dashboard"))
        error = "Identifiant ou mot de passe incorrect."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    role = session.get("role", "commercial")
    # Commercial gets their own action-focused view
    if role == "commercial":
        return _dashboard_commercial()
    return _dashboard_admin()


def _dashboard_admin():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM prospects WHERE status != 'archived'")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE status='closed_won'")
    won = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE status NOT IN ('new','closed_won','closed_lost','archived')")
    in_pipeline = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(estimated_value),0) FROM prospects WHERE status='closed_won' AND country='TN'")
    revenue_tnd = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(estimated_value),0) FROM prospects WHERE status='closed_won' AND country='FR'")
    revenue_eur = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE status='archived'")
    archived_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE next_follow_up != '' AND next_follow_up <= ? AND status NOT IN ('closed_won','closed_lost','archived')", (date.today().isoformat(),))
    overdue = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(estimated_value),0) FROM prospects WHERE status NOT IN ('new','closed_won','closed_lost','archived')")
    pipeline_value = c.fetchone()[0]

    status_filter   = request.args.get("status", "all")
    sort_by         = request.args.get("sort", "score")
    priority_filter = request.args.get("priority", "all")
    search          = request.args.get("search", "")

    query  = "SELECT * FROM prospects WHERE status != 'archived'"
    params = []
    if status_filter != "all":
        query += " AND status = ?"; params.append(status_filter)
    if priority_filter != "all":
        query += " AND priority = ?"; params.append(priority_filter)
    if search:
        query += " AND (name LIKE ? OR category LIKE ? OR address LIKE ?)"
        like = f"%{search}%"; params.extend([like, like, like])
    order = {"score":"score DESC","rating":"google_rating DESC","name":"name ASC","value":"estimated_value DESC"}.get(sort_by,"score DESC")
    query += f" ORDER BY {order}"

    c.execute(query, params)
    prospects = [row_to_dict(r) for r in c.fetchall()]
    conn.close()
    for p in prospects:
        p["score_label"], p["score_class"] = get_score_label(p["score"])

    stats = {
        "total": total, "won": won, "in_pipeline": in_pipeline,
        "revenue_tnd": revenue_tnd, "revenue_eur": revenue_eur,
        "archived": archived_count, "overdue": overdue,
        "pipeline_value": pipeline_value,
    }
    return render_template(
        "dashboard.html",
        prospects=prospects, stats=stats,
        pipeline_stages=PIPELINE_STAGES,
        current_status=status_filter, current_sort=sort_by,
        current_priority=priority_filter, search=search,
        today=date.today().isoformat(),
    )


def _dashboard_commercial():
    conn = get_db()
    c = conn.cursor()
    today_str = date.today().isoformat()

    # Relances en retard ou aujourd'hui
    c.execute("""SELECT * FROM prospects WHERE next_follow_up != '' AND next_follow_up <= ?
                 AND status NOT IN ('closed_won','closed_lost','archived')
                 ORDER BY next_follow_up ASC""", (today_str,))
    followups = [row_to_dict(r) for r in c.fetchall()]

    # Prospects chauds à contacter (score élevé, status=new)
    c.execute("SELECT * FROM prospects WHERE status='new' ORDER BY score DESC LIMIT 8")
    hot_prospects = [row_to_dict(r) for r in c.fetchall()]

    # Prospects en cours de négociation
    c.execute("SELECT * FROM prospects WHERE status IN ('contacted','interested','proposal_sent') ORDER BY score DESC")
    active = [row_to_dict(r) for r in c.fetchall()]

    # Mes stats perso
    c.execute("SELECT COUNT(*) FROM prospects WHERE status != 'archived'")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE status='new'")
    to_contact = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE status IN ('contacted','interested','proposal_sent')")
    in_progress = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM interactions WHERE interaction_date = ?", (today_str,))
    actions_today = c.fetchone()[0]

    conn.close()

    for p in followups + hot_prospects + active:
        p["score_label"], p["score_class"] = get_score_label(p["score"])

    stats = {
        "total": total, "to_contact": to_contact,
        "in_progress": in_progress, "actions_today": actions_today,
        "followups_count": len(followups),
    }
    return render_template(
        "dashboard_commercial.html",
        followups=followups, hot_prospects=hot_prospects, active=active,
        stats=stats, pipeline_stages=PIPELINE_STAGES,
        today=today_str,
    )


# ─── Prospect Detail ──────────────────────────────────────────────────────────

@app.route("/prospect/<int:pid>")
@login_required
def prospect_detail(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Prospect introuvable", 404
    p = row_to_dict(row)

    c.execute("SELECT * FROM interactions WHERE prospect_id = ? ORDER BY interaction_date DESC, created_at DESC LIMIT 3", (pid,))
    recent_interactions = [dict(r) for r in c.fetchall()]

    c.execute("SELECT COUNT(*) FROM interactions WHERE prospect_id = ?", (pid,))
    interaction_count = c.fetchone()[0]

    c.execute("SELECT * FROM pipeline_notes WHERE prospect_id = ? ORDER BY created_at DESC LIMIT 5", (pid,))
    notes = [dict(n) for n in c.fetchall()]
    conn.close()

    p["score_label"], p["score_class"] = get_score_label(p["score"])
    vulnerabilities = build_vulnerabilities(p)

    type_map = {t[0]: (t[1], t[2]) for t in INTERACTION_TYPES}

    return render_template(
        "prospect_detail.html",
        prospect=p, vulnerabilities=vulnerabilities, notes=notes,
        recent_interactions=recent_interactions, interaction_count=interaction_count,
        pipeline_stages=PIPELINE_STAGES, type_map=type_map,
        priority_config=PRIORITY_CONFIG,
    )


# ─── Activity ─────────────────────────────────────────────────────────────────

@app.route("/prospect/<int:pid>/activity")
@login_required
def activity(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Prospect introuvable", 404
    p = row_to_dict(row)

    c.execute("SELECT * FROM interactions WHERE prospect_id = ? ORDER BY interaction_date DESC, created_at DESC", (pid,))
    interactions = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM pipeline_notes WHERE prospect_id = ? ORDER BY created_at DESC", (pid,))
    notes = [dict(n) for n in c.fetchall()]

    # Stats
    stats = {
        "total": len(interactions),
        "calls": sum(1 for i in interactions if i["type"] == "appel"),
        "meetings": sum(1 for i in interactions if i["type"] == "reunion"),
        "positive": sum(1 for i in interactions if i["outcome"] == "positif"),
    }
    conn.close()

    type_map = {t[0]: (t[1], t[2]) for t in INTERACTION_TYPES}
    outcome_map = {o[0]: o[1] for o in OUTCOMES}

    return render_template(
        "activity.html",
        prospect=p, interactions=interactions, notes=notes,
        stats=stats, interaction_types=INTERACTION_TYPES, outcomes=OUTCOMES,
        type_map=type_map, outcome_map=outcome_map,
        pipeline_stages=PIPELINE_STAGES,
        today=date.today().isoformat(),
    )


# ─── Outreach ─────────────────────────────────────────────────────────────────

@app.route("/prospect/<int:pid>/outreach")
@login_required
def outreach(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Prospect introuvable", 404
    p = row_to_dict(row)
    conn.close()

    subject, email_body = generate_email(p)
    dm_body           = generate_dm(p)
    whatsapp_body     = generate_whatsapp(p)

    return render_template(
        "outreach.html",
        prospect=p, email_subject=subject,
        email_body=email_body, dm_body=dm_body, whatsapp_body=whatsapp_body,
    )


# ─── Pipeline ─────────────────────────────────────────────────────────────────

@app.route("/pipeline")
@login_required
def pipeline():
    conn = get_db()
    c = conn.cursor()
    stages_data = {}
    for stage_key, stage_label, color in PIPELINE_STAGES:
        c.execute("SELECT * FROM prospects WHERE status = ? ORDER BY score DESC", (stage_key,))
        rows = [row_to_dict(r) for r in c.fetchall()]
        for r in rows:
            r["score_label"], r["score_class"] = get_score_label(r["score"])
        stages_data[stage_key] = {"label": stage_label, "color": color, "prospects": rows,
                                   "total_value": sum(r.get("estimated_value", 0) for r in rows)}
    conn.close()
    return render_template("pipeline.html", stages_data=stages_data, pipeline_stages=PIPELINE_STAGES)


# ─── Marché Tunisie ───────────────────────────────────────────────────────────

@app.route("/marche/tunisie")
@login_required
def marche_tunisie():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM prospects WHERE country='TN' AND status!='archived'")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='TN' AND status='closed_won'")
    won = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='TN' AND status NOT IN ('new','closed_won','closed_lost','archived')")
    in_pipeline = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(estimated_value),0) FROM prospects WHERE country='TN' AND status='closed_won'")
    revenue = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='TN' AND has_modern_menu=0 AND status!='archived'")
    no_modern_menu = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='TN' AND has_pro_logo=0 AND status!='archived'")
    no_pro_logo = c.fetchone()[0]

    search   = request.args.get("search", "")
    status_f = request.args.get("status", "all")
    sort_by  = request.args.get("sort", "score")
    priority_f = request.args.get("priority", "all")

    query  = "SELECT * FROM prospects WHERE country='TN' AND status!='archived'"
    params = []
    if status_f != "all":
        query += " AND status=?"; params.append(status_f)
    if priority_f != "all":
        query += " AND priority=?"; params.append(priority_f)
    if search:
        query += " AND (name LIKE ? OR category LIKE ? OR address LIKE ?)"
        like = f"%{search}%"; params.extend([like, like, like])
    order = {"score":"score DESC","rating":"google_rating DESC","name":"name ASC","value":"estimated_value DESC"}.get(sort_by,"score DESC")
    query += f" ORDER BY {order}"

    c.execute(query, params)
    prospects = [row_to_dict(r) for r in c.fetchall()]
    conn.close()

    for p in prospects:
        p["score_label"], p["score_class"] = get_score_label(p["score"])

    stats = {"total": total, "won": won, "in_pipeline": in_pipeline, "revenue": revenue,
             "no_modern_menu": no_modern_menu, "no_pro_logo": no_pro_logo}
    return render_template(
        "marche_tunisie.html",
        prospects=prospects, stats=stats,
        pipeline_stages=PIPELINE_STAGES,
        current_status=status_f, current_sort=sort_by,
        current_priority=priority_f, search=search,
        today=date.today().isoformat(),
    )


# ─── Marché France ────────────────────────────────────────────────────────────

@app.route("/marche/france")
@login_required
def marche_france():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND status!='archived'")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND status='closed_won'")
    won = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND status NOT IN ('new','closed_won','closed_lost','archived')")
    in_pipeline = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND has_digital_menu=0 AND status!='archived'")
    no_menu = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND has_website=0 AND status!='archived'")
    no_website = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND has_online_booking=0 AND status!='archived'")
    no_booking = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND has_modern_menu=0 AND status!='archived'")
    no_modern_menu = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE country='FR' AND has_pro_logo=0 AND status!='archived'")
    no_pro_logo = c.fetchone()[0]

    search   = request.args.get("search", "")
    status_f = request.args.get("status", "all")
    city_f   = request.args.get("city", "all")
    sort_by  = request.args.get("sort", "score")

    # Get distinct cities for filter
    c.execute("SELECT DISTINCT city FROM prospects WHERE country='FR' AND city!='' ORDER BY city")
    cities = [r[0] for r in c.fetchall()]

    query  = "SELECT * FROM prospects WHERE country='FR' AND status!='archived'"
    params = []
    if status_f != "all":
        query += " AND status=?"; params.append(status_f)
    if city_f != "all":
        query += " AND city=?"; params.append(city_f)
    if search:
        query += " AND (name LIKE ? OR category LIKE ? OR city LIKE ?)"
        like = f"%{search}%"; params.extend([like, like, like])
    order = {"score":"score DESC","rating":"google_rating DESC","name":"name ASC"}.get(sort_by,"score DESC")
    query += f" ORDER BY {order}"

    c.execute(query, params)
    prospects = [row_to_dict(r) for r in c.fetchall()]
    conn.close()

    for p in prospects:
        p["score_label"], p["score_class"] = get_score_label(p["score"])

    stats = {
        "total": total, "won": won, "in_pipeline": in_pipeline,
        "no_menu": no_menu, "no_website": no_website, "no_booking": no_booking,
        "no_modern_menu": no_modern_menu, "no_pro_logo": no_pro_logo,
    }
    return render_template(
        "marche_france.html",
        prospects=prospects, stats=stats,
        pipeline_stages=PIPELINE_STAGES,
        current_status=status_f, current_sort=sort_by,
        current_city=city_f, cities=cities, search=search,
        today=date.today().isoformat(),
    )


# ─── Archive ──────────────────────────────────────────────────────────────────

@app.route("/archive")
@login_required
def archive():
    conn = get_db()
    c = conn.cursor()
    search = request.args.get("search", "")
    reason = request.args.get("reason", "all")

    query  = "SELECT * FROM prospects WHERE status = 'archived'"
    params = []
    if search:
        query += " AND (name LIKE ? OR category LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    query += " ORDER BY created_at DESC"

    c.execute(query, params)
    archived = [row_to_dict(r) for r in c.fetchall()]

    for p in archived:
        p["score_label"], p["score_class"] = get_score_label(p["score"])

    c.execute("SELECT COUNT(*) FROM prospects WHERE status='archived'")
    total = c.fetchone()[0]
    conn.close()

    return render_template(
        "archive.html", archived=archived, total=total,
        search=search, pipeline_stages=PIPELINE_STAGES,
    )


# ─── AI Insights ──────────────────────────────────────────────────────────────

@app.route("/ai-insights")
@login_required
def ai_insights():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE status NOT IN ('archived','closed_lost') ORDER BY score DESC LIMIT 5")
    top_prospects = [row_to_dict(r) for r in c.fetchall()]
    for p in top_prospects:
        p["score_label"], p["score_class"] = get_score_label(p["score"])

    c.execute("SELECT COUNT(*) FROM prospects WHERE status NOT IN ('archived')")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prospects WHERE status='closed_won'")
    won = c.fetchone()[0]
    conversion_rate = round((won / total * 100) if total else 0, 1)
    conn.close()

    return render_template("ai_insights.html", top_prospects=top_prospects,
                           conversion_rate=conversion_rate, total=total, won=won)


@app.route("/prospect/<int:pid>/ai-analysis")
@login_required
def ai_analysis(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Prospect introuvable", 404
    p = row_to_dict(row)
    conn.close()
    p["score_label"], p["score_class"] = get_score_label(p["score"])
    vulnerabilities = build_vulnerabilities(p)
    return render_template("ai_analysis.html", prospect=p, vulnerabilities=vulnerabilities)


# ─── API ──────────────────────────────────────────────────────────────────────

@app.route("/api/prospect/<int:pid>/status", methods=["POST"])
@login_required
def update_status(pid):
    data = request.get_json()
    new_status = data.get("status")
    note       = data.get("note", "")
    valid = [s[0] for s in PIPELINE_STAGES] + ["archived"]
    if new_status not in valid:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    old_status = row["status"]
    c.execute("UPDATE prospects SET status = ? WHERE id = ?", (new_status, pid))
    if note or old_status != new_status:
        c.execute(
            "INSERT INTO pipeline_notes (prospect_id, note, status_change) VALUES (?, ?, ?)",
            (pid, note, f"{old_status} → {new_status}")
        )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/note", methods=["POST"])
@login_required
def add_note(pid):
    data = request.get_json()
    note = data.get("note", "").strip()
    if not note:
        return jsonify({"error": "Note vide"}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO pipeline_notes (prospect_id, note, status_change) VALUES (?, ?, ?)", (pid, note, ""))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/interaction", methods=["POST"])
@login_required
def add_interaction(pid):
    data = request.get_json()
    required = ["type", "interaction_date", "summary"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"Champ requis: {f}"}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO interactions
        (prospect_id, type, interaction_date, duration_min, contact_name, summary, outcome, next_action, next_action_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pid,
        data["type"],
        data["interaction_date"],
        data.get("duration_min", 0),
        data.get("contact_name", ""),
        data["summary"],
        data.get("outcome", "neutre"),
        data.get("next_action", ""),
        data.get("next_action_date", ""),
    ))

    # Update last_contact_date and next_follow_up on prospect
    c.execute("UPDATE prospects SET last_contact_date = ? WHERE id = ?", (data["interaction_date"], pid))
    if data.get("next_action_date"):
        c.execute("UPDATE prospects SET next_follow_up = ? WHERE id = ?", (data["next_action_date"], pid))

    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/interaction/<int:iid>", methods=["DELETE"])
@login_required
def delete_interaction(pid, iid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM interactions WHERE id = ? AND prospect_id = ?", (iid, pid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/archive", methods=["POST"])
@login_required
def archive_prospect(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    old = row["status"]
    c.execute("UPDATE prospects SET status = 'archived' WHERE id = ?", (pid,))
    c.execute("INSERT INTO pipeline_notes (prospect_id, note, status_change) VALUES (?, ?, ?)",
              (pid, "Prospect archivé", f"{old} → archived"))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/restore", methods=["POST"])
@login_required
def restore_prospect(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE prospects SET status = 'new' WHERE id = ?", (pid,))
    c.execute("INSERT INTO pipeline_notes (prospect_id, note, status_change) VALUES (?, ?, ?)",
              (pid, "Prospect restauré depuis l'archive", "archived → new"))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/priority", methods=["POST"])
@login_required
def update_priority(pid):
    data = request.get_json()
    priority = data.get("priority")
    if priority not in ["urgent", "high", "medium", "low"]:
        return jsonify({"error": "Invalid priority"}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE prospects SET priority = ? WHERE id = ?", (priority, pid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/prospect/<int:pid>/follow-up", methods=["POST"])
@login_required
def set_follow_up(pid):
    data = request.get_json()
    follow_up = data.get("next_follow_up", "")
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE prospects SET next_follow_up = ? WHERE id = ?", (follow_up, pid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/stats")
@login_required
def api_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) as count FROM prospects GROUP BY status")
    by_status = {r["status"]: r["count"] for r in c.fetchall()}
    c.execute("SELECT category, COUNT(*) as count FROM prospects WHERE status!='archived' GROUP BY category ORDER BY count DESC LIMIT 6")
    by_category = [{"category": r["category"], "count": r["count"]} for r in c.fetchall()]
    c.execute("SELECT AVG(score) as avg, MAX(score) as max, MIN(score) as min FROM prospects WHERE status!='archived'")
    score_stats = dict(c.fetchone())
    c.execute("SELECT COALESCE(SUM(estimated_value),0) FROM prospects WHERE status='closed_won'")
    total_revenue = c.fetchone()[0]
    conn.close()
    return jsonify({"by_status": by_status, "by_category": by_category,
                    "score_stats": score_stats, "total_revenue": total_revenue})


@app.route("/api/ai/analyze/<int:pid>")
@login_required
def ai_analyze(pid):
    """Mock AI analysis endpoint — will be replaced with Claude API."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE id = ?", (pid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    p = row_to_dict(row)
    conn.close()

    # Mock AI analysis (will be Claude API later)
    services = p["services_needed"]
    score = p["score"]
    top_service = services[0] if services else "présence digitale"

    conversion_prob = min(95, max(20, score + 10)) if score > 50 else max(15, score - 5)
    best_channel = "Email froid" if p.get("email") else ("WhatsApp" if p.get("phone") else "DM Instagram")

    analysis = {
        "conversion_probability": conversion_prob,
        "best_channel": best_channel,
        "best_time": "Mardi-Jeudi, 10h-11h ou 14h30-16h",
        "pitch_focus": top_service,
        "estimated_deal_value": p.get("estimated_value", 1500),
        "urgency_level": p.get("priority", "medium"),
        "key_insight": f"{p['name']} présente {len(services)} gaps digitaux critiques. Le manque de {top_service.lower()} est l'argument d'accroche le plus fort.",
        "recommended_approach": "Commencer par un audit gratuit pour montrer la valeur concrète, puis proposer un pack mensuel.",
        "competitor_analysis": "Vos concurrents directs dans ce quartier ont en moyenne 2.3x plus de visibilité en ligne.",
        "expected_roi": f"Un investissement de {p.get('estimated_value', 1500)} TND/mois peut générer +40% de nouveaux clients selon nos benchmarks.",
        "generated_at": datetime.now().isoformat(),
        "model": "Claude API (non connecté — aperçu)",
    }
    return jsonify(analysis)


init_db()
seed_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Octo Vision Prospection Platform running at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=port)
