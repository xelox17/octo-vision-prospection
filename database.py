import sqlite3
import json
from datetime import datetime, date

DB_PATH = "prospection.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            google_rating REAL DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            has_website INTEGER DEFAULT 0,
            website_url TEXT,
            has_instagram INTEGER DEFAULT 0,
            instagram_handle TEXT,
            instagram_followers INTEGER DEFAULT 0,
            has_facebook INTEGER DEFAULT 0,
            last_post_days_ago INTEGER DEFAULT 999,
            seo_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            notes TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            services_needed TEXT DEFAULT '[]',
            priority TEXT DEFAULT 'medium',
            estimated_value INTEGER DEFAULT 0,
            next_follow_up TEXT DEFAULT '',
            last_contact_date TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrate: add new columns to existing DB gracefully
    migrations = [
        ("priority",           "TEXT DEFAULT 'medium'"),
        ("estimated_value",    "INTEGER DEFAULT 0"),
        ("next_follow_up",     "TEXT DEFAULT ''"),
        ("last_contact_date",  "TEXT DEFAULT ''"),
        ("country",              "TEXT DEFAULT 'TN'"),
        ("has_digital_menu",     "INTEGER DEFAULT 0"),
        ("has_online_booking",   "INTEGER DEFAULT 0"),
        ("has_qr_menu",          "INTEGER DEFAULT 0"),
        ("city",                 "TEXT DEFAULT ''"),
        ("has_modern_menu",      "INTEGER DEFAULT 0"),
        ("has_pro_logo",         "INTEGER DEFAULT 0"),
        ("has_gmaps_photos",     "INTEGER DEFAULT 0"),
        ("menu_board_quality",   "TEXT DEFAULT 'unknown'"),
    ]
    for col_name, col_def in migrations:
        try:
            c.execute(f"ALTER TABLE prospects ADD COLUMN {col_name} {col_def}")
        except sqlite3.OperationalError:
            pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER NOT NULL,
            type TEXT NOT NULL DEFAULT 'note',
            interaction_date TEXT NOT NULL,
            duration_min INTEGER DEFAULT 0,
            contact_name TEXT DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            outcome TEXT DEFAULT 'neutre',
            next_action TEXT DEFAULT '',
            next_action_date TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES prospects(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            note TEXT,
            status_change TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES prospects(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS outreach_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            message_type TEXT,
            subject TEXT,
            body TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES prospects(id)
        )
    """)

    conn.commit()
    conn.close()


MOCK_PROSPECTS = [
    {
        "name": "Restaurant Le Carthage",
        "category": "Restaurant",
        "address": "Avenue Habib Bourguiba, Tunis Centre",
        "phone": "+216 71 234 567",
        "email": None,
        "google_rating": 3.8,
        "review_count": 42,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 90, "seo_score": 12,
        "priority": "urgent", "estimated_value": 2800,
    },
    {
        "name": "Dar El Jeld",
        "category": "Restaurant Traditionnel",
        "address": "Rue Dar El Jeld, Médina de Tunis",
        "phone": "+216 71 560 916",
        "email": "contact@dareljeld.tn",
        "google_rating": 4.6, "review_count": 312,
        "has_website": 1, "website_url": "dareljeld.tn",
        "has_instagram": 1, "instagram_handle": "@dareljeld", "instagram_followers": 4800,
        "has_facebook": 1, "last_post_days_ago": 7, "seo_score": 58,
        "priority": "low", "estimated_value": 1200,
    },
    {
        "name": "Pizza Napoli Tunis",
        "category": "Pizzeria",
        "address": "Rue de Marseille, La Marsa",
        "phone": "+216 71 774 321",
        "email": None,
        "google_rating": 4.1, "review_count": 87,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@pizzanapoli_tunis", "instagram_followers": 920,
        "has_facebook": 1, "last_post_days_ago": 45, "seo_score": 20,
        "priority": "high", "estimated_value": 2200,
    },
    {
        "name": "Café Saf Saf",
        "category": "Café & Snack",
        "address": "Avenue de la Liberté, Tunis",
        "phone": "+216 71 890 123",
        "email": None,
        "google_rating": 3.2, "review_count": 18,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 0,
        "priority": "urgent", "estimated_value": 3200,
    },
    {
        "name": "Sushi Zen Carthage",
        "category": "Restaurant Japonais",
        "address": "Rue Hannibal, Les Berges du Lac",
        "phone": "+216 71 963 852",
        "email": "info@sushizen.tn",
        "google_rating": 4.4, "review_count": 156,
        "has_website": 1, "website_url": "sushizen.tn",
        "has_instagram": 1, "instagram_handle": "@sushizen_tn", "instagram_followers": 2300,
        "has_facebook": 1, "last_post_days_ago": 3, "seo_score": 45,
        "priority": "medium", "estimated_value": 900,
    },
    {
        "name": "Snack Brik & More",
        "category": "Snack Tunisien",
        "address": "Rue Ibn Khaldoun, Bab Souika",
        "phone": "+216 23 456 789",
        "email": None,
        "google_rating": 4.0, "review_count": 63,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@brikandmore", "instagram_followers": 450,
        "has_facebook": 0, "last_post_days_ago": 120, "seo_score": 8,
        "priority": "high", "estimated_value": 1800,
    },
    {
        "name": "Le Gourmet Tunis",
        "category": "Restaurant Gastronomique",
        "address": "Avenue Mohamed V, Mutuelle Ville",
        "phone": "+216 71 345 678",
        "email": "reservation@legourmet.tn",
        "google_rating": 4.2, "review_count": 94,
        "has_website": 1, "website_url": "legourmet-tunis.tn",
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 60, "seo_score": 32,
        "priority": "high", "estimated_value": 2500,
    },
    {
        "name": "Café Maure Ennejma Ezzahra",
        "category": "Café Traditionnel",
        "address": "Sidi Bou Said, Tunis",
        "phone": "+216 71 747 000",
        "email": None,
        "google_rating": 4.7, "review_count": 521,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@cafemaure_sidibousaid", "instagram_followers": 8100,
        "has_facebook": 1, "last_post_days_ago": 14, "seo_score": 25,
        "priority": "medium", "estimated_value": 1500,
    },
    {
        "name": "Burger House Tunis",
        "category": "Fast Food",
        "address": "Rue du Lac Biwa, Les Berges du Lac II",
        "phone": "+216 71 963 741",
        "email": None,
        "google_rating": 3.6, "review_count": 201,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@burgerhouse_tn", "instagram_followers": 3200,
        "has_facebook": 1, "last_post_days_ago": 5, "seo_score": 18,
        "priority": "high", "estimated_value": 2000,
    },
    {
        "name": "Restaurant El Foundouk",
        "category": "Restaurant Traditionnel",
        "address": "Médina, Tunis",
        "phone": "+216 71 558 888",
        "email": None,
        "google_rating": 3.9, "review_count": 33,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 5,
        "priority": "urgent", "estimated_value": 3500,
    },
    {
        "name": "Patisserie Masmoudi",
        "category": "Pâtisserie",
        "address": "Avenue Farhat Hached, Centre Ville",
        "phone": "+216 71 242 000",
        "email": "contact@masmoudi.tn",
        "google_rating": 4.8, "review_count": 843,
        "has_website": 1, "website_url": "masmoudi.tn",
        "has_instagram": 1, "instagram_handle": "@masmoudi_tn", "instagram_followers": 22000,
        "has_facebook": 1, "last_post_days_ago": 1, "seo_score": 72,
        "priority": "low", "estimated_value": 500,
    },
    {
        "name": "Taco Loco Tunis",
        "category": "Restaurant Mexicain",
        "address": "Rue du Lac Windermere, Lac II",
        "phone": "+216 71 862 530",
        "email": None,
        "google_rating": 4.3, "review_count": 77,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@tacoloco_tn", "instagram_followers": 1100,
        "has_facebook": 1, "last_post_days_ago": 30, "seo_score": 14,
        "priority": "medium", "estimated_value": 1600,
    },
    {
        "name": "Chez Slama",
        "category": "Restaurant Populaire",
        "address": "Rue Mongi Slim, Bab El Bhar",
        "phone": "+216 71 332 211",
        "email": None,
        "google_rating": 4.5, "review_count": 178,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 200, "seo_score": 3,
        "priority": "high", "estimated_value": 2100,
    },
    {
        "name": "Cloud Kitchen Délices",
        "category": "Dark Kitchen",
        "address": "Ariana, Grand Tunis",
        "phone": "+216 55 123 456",
        "email": "commandes@clouddelices.tn",
        "google_rating": 3.4, "review_count": 29,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@clouddelices", "instagram_followers": 680,
        "has_facebook": 1, "last_post_days_ago": 10, "seo_score": 10,
        "priority": "high", "estimated_value": 1900,
    },
    {
        "name": "Le Pêcheur Gourmet",
        "category": "Restaurant de Poisson",
        "address": "Port de La Goulette, Tunis",
        "phone": "+216 71 735 000",
        "email": None,
        "google_rating": 4.1, "review_count": 112,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 75, "seo_score": 7,
        "priority": "high", "estimated_value": 2400,
    },
    {
        "name": "Healthy Bowl Tunis",
        "category": "Restaurant Bio & Healthy",
        "address": "Rue du Lac Turkana, Les Berges du Lac",
        "phone": "+216 71 964 852",
        "email": "hello@healthybowl.tn",
        "google_rating": 4.6, "review_count": 234,
        "has_website": 1, "website_url": "healthybowl.tn",
        "has_instagram": 1, "instagram_handle": "@healthybowl_tn", "instagram_followers": 6700,
        "has_facebook": 1, "last_post_days_ago": 2, "seo_score": 55,
        "priority": "low", "estimated_value": 800,
    },
    {
        "name": "Brasserie 1956",
        "category": "Brasserie",
        "address": "Avenue de Paris, Centre Ville Tunis",
        "phone": "+216 71 333 444",
        "email": None,
        "google_rating": 3.7, "review_count": 55,
        "has_website": 1, "website_url": "brasserie1956.tn",
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 22,
        "priority": "high", "estimated_value": 2200,
    },
    {
        "name": "Crêperie de Carthage",
        "category": "Crêperie",
        "address": "Avenue de Carthage, Salammbô",
        "phone": "+216 71 720 888",
        "email": None,
        "google_rating": 4.3, "review_count": 91,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@creperie_carthage", "instagram_followers": 1350,
        "has_facebook": 1, "last_post_days_ago": 20, "seo_score": 16,
        "priority": "medium", "estimated_value": 1700,
    },
    {
        "name": "Kebab Palace",
        "category": "Fast Food",
        "address": "Rue de Turquie, Montplaisir",
        "phone": "+216 71 890 765",
        "email": None,
        "google_rating": 3.5, "review_count": 14,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 0,
        "priority": "urgent", "estimated_value": 3000,
    },
    {
        "name": "Traiteur El Hana",
        "category": "Traiteur & Événementiel",
        "address": "Menzah 6, Tunis",
        "phone": "+216 71 752 963",
        "email": "elhana@traiteur.tn",
        "google_rating": 4.0, "review_count": 48,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@elhana_traiteur", "instagram_followers": 870,
        "has_facebook": 1, "last_post_days_ago": 35, "seo_score": 11,
        "priority": "medium", "estimated_value": 1500,
    },
]


def compute_score_and_services(p):
    score = 0
    services = []

    if not p.get("has_website"):
        score += 25
        services.append("Création de Site Web")

    if p.get("seo_score", 0) < 30:
        score += 15
        services.append("Référencement SEO")
    elif p.get("seo_score", 0) < 50:
        score += 8
        services.append("Référencement SEO")

    if not p.get("has_instagram"):
        score += 15
        services.append("Gestion des Réseaux Sociaux")
    elif p.get("instagram_followers", 0) < 1000:
        score += 8
        if "Gestion des Réseaux Sociaux" not in services:
            services.append("Gestion des Réseaux Sociaux")

    if p.get("last_post_days_ago", 999) > 60:
        score += 10
        if "Création de Contenu" not in services:
            services.append("Création de Contenu")
    elif p.get("last_post_days_ago", 999) > 30:
        score += 5
        if "Création de Contenu" not in services:
            services.append("Création de Contenu")

    if p.get("review_count", 0) < 50:
        score += 8
        services.append("Publicité Payante (Google Ads)")
    elif p.get("google_rating", 5) < 4.0:
        score += 5
        services.append("Gestion de Réputation")

    if not p.get("has_facebook") and "Gestion des Réseaux Sociaux" not in services:
        score += 4
        services.append("Gestion des Réseaux Sociaux")

    # Design graphique
    if not p.get("has_modern_menu"):
        score += 12
        services.append("Design Menu & Carte")
    if not p.get("has_pro_logo"):
        score += 8
        services.append("Identité Visuelle & Logo")
    if not p.get("has_gmaps_photos"):
        score += 8
        services.append("Photos & Visuels Google Maps")

    return min(score, 100), list(dict.fromkeys(services))


def compute_france_score_and_services(p):
    """Scoring spécifique France : focus menu digital, site vitrine, réservation en ligne."""
    score = 0
    services = []

    if not p.get("has_website"):
        score += 30
        services.append("Site Vitrine Restaurant")

    if not p.get("has_digital_menu"):
        score += 30
        services.append("Menu Digital QR Code")

    if not p.get("has_online_booking"):
        score += 20
        services.append("Réservation en Ligne")

    if not p.get("has_instagram"):
        score += 10
        services.append("Gestion des Réseaux Sociaux")
    elif p.get("instagram_followers", 0) < 500:
        score += 5
        if "Gestion des Réseaux Sociaux" not in services:
            services.append("Gestion des Réseaux Sociaux")

    if p.get("review_count", 0) < 50:
        score += 5
        services.append("Optimisation Google My Business")
    if p.get("google_rating", 5) < 4.0:
        score += 5
        if "Optimisation Google My Business" not in services:
            services.append("Optimisation Google My Business")

    if p.get("seo_score", 0) < 30:
        score += 5
        services.append("Référencement SEO Local")

    # Design graphique — aussi important en France
    if not p.get("has_modern_menu"):
        score += 10
        services.append("Design Menu Board & Carte")
    if not p.get("has_pro_logo"):
        score += 5
        services.append("Identité Visuelle & Logo")
    if not p.get("has_gmaps_photos"):
        score += 5
        services.append("Photos & Visuels Google Maps")
    if p.get("menu_board_quality") in ("mauvais", "inexistant", "unknown"):
        if "Design Menu Board & Carte" not in services:
            services.append("Design Menu Board & Carte")

    return min(score, 100), list(dict.fromkeys(services))


MOCK_FRANCE = [
    {
        "name": "Le Bistrot du Marché",
        "category": "Bistrot Français",
        "city": "Paris 11e",
        "address": "23 Rue de la Roquette, Paris 11e",
        "phone": "+33 1 43 55 12 34",
        "email": None,
        "google_rating": 4.2, "review_count": 87,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@bistrotdumarche", "instagram_followers": 430,
        "has_facebook": 1, "last_post_days_ago": 25, "seo_score": 12,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 149,
    },
    {
        "name": "Chez Michel",
        "category": "Restaurant Traditionnel",
        "city": "Lyon 1er",
        "address": "8 Rue Pizay, Lyon 1er",
        "phone": "+33 4 78 28 11 47",
        "email": None,
        "google_rating": 4.5, "review_count": 312,
        "has_website": 1, "website_url": "chezmichel-lyon.fr",
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 90, "seo_score": 28,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 99,
    },
    {
        "name": "La Table de Provence",
        "category": "Restaurant Provençal",
        "city": "Marseille 6e",
        "address": "14 Cours Julien, Marseille 6e",
        "phone": "+33 4 91 48 22 10",
        "email": "contact@tabledefrovence.fr",
        "google_rating": 4.0, "review_count": 156,
        "has_website": 1, "website_url": "tabledefrovence.fr",
        "has_instagram": 1, "instagram_handle": "@tabledeprovence", "instagram_followers": 820,
        "has_facebook": 1, "last_post_days_ago": 12, "seo_score": 41,
        "has_digital_menu": 0, "has_online_booking": 1, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 79,
    },
    {
        "name": "Brasserie des Capucins",
        "category": "Brasserie",
        "city": "Bordeaux Centre",
        "address": "Place des Capucins, Bordeaux",
        "phone": "+33 5 56 91 33 44",
        "email": None,
        "google_rating": 3.7, "review_count": 43,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 5,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 149,
    },
    {
        "name": "Le Comptoir Niçois",
        "category": "Restaurant Méditerranéen",
        "city": "Nice Vieux-Ville",
        "address": "12 Cours Saleya, Nice",
        "phone": "+33 4 93 85 71 22",
        "email": "info@comptoirnicois.fr",
        "google_rating": 4.6, "review_count": 521,
        "has_website": 1, "website_url": "comptoirnicois.fr",
        "has_instagram": 1, "instagram_handle": "@comptoirnicois", "instagram_followers": 2800,
        "has_facebook": 1, "last_post_days_ago": 3, "seo_score": 55,
        "has_digital_menu": 0, "has_online_booking": 1, "has_qr_menu": 0,
        "priority": "medium", "estimated_value": 79,
    },
    {
        "name": "Pizzeria Napolitana",
        "category": "Pizzeria",
        "city": "Toulouse Capitole",
        "address": "7 Rue Saint-Rome, Toulouse",
        "phone": "+33 5 61 21 88 50",
        "email": None,
        "google_rating": 4.3, "review_count": 198,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@pizzanapolitana_tlse", "instagram_followers": 670,
        "has_facebook": 1, "last_post_days_ago": 8, "seo_score": 14,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 149,
    },
    {
        "name": "Au Crocodile",
        "category": "Restaurant Gastronomique",
        "city": "Strasbourg Centre",
        "address": "10 Rue de l'Outre, Strasbourg",
        "phone": "+33 3 88 32 13 02",
        "email": "reservation@aucrocodile.fr",
        "google_rating": 4.7, "review_count": 445,
        "has_website": 1, "website_url": "aucrocodile.fr",
        "has_instagram": 1, "instagram_handle": "@aucrocodile", "instagram_followers": 3200,
        "has_facebook": 1, "last_post_days_ago": 5, "seo_score": 62,
        "has_digital_menu": 1, "has_online_booking": 1, "has_qr_menu": 0,
        "priority": "low", "estimated_value": 49,
    },
    {
        "name": "La Crêperie Bretonne",
        "category": "Crêperie",
        "city": "Nantes Centre",
        "address": "3 Rue de la Juiverie, Nantes",
        "phone": "+33 2 40 47 22 11",
        "email": None,
        "google_rating": 4.4, "review_count": 267,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@creperie_bretonne_nantes", "instagram_followers": 1100,
        "has_facebook": 1, "last_post_days_ago": 15, "seo_score": 18,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 149,
    },
    {
        "name": "L'Estaminet du Vieux-Lille",
        "category": "Estaminet Flamand",
        "city": "Lille Vieux-Lille",
        "address": "60 Rue de Gand, Lille",
        "phone": "+33 3 20 15 01 59",
        "email": None,
        "google_rating": 4.1, "review_count": 78,
        "has_website": 1, "website_url": "estaminetlille.fr",
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 120, "seo_score": 22,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 99,
    },
    {
        "name": "Sushi Fusion Montpellier",
        "category": "Restaurant Japonais",
        "city": "Montpellier",
        "address": "8 Place de la Comédie, Montpellier",
        "phone": "+33 4 67 60 44 10",
        "email": "hello@sushifusion34.fr",
        "google_rating": 4.2, "review_count": 134,
        "has_website": 1, "website_url": "sushifusion34.fr",
        "has_instagram": 1, "instagram_handle": "@sushifusion_mtp", "instagram_followers": 1650,
        "has_facebook": 1, "last_post_days_ago": 7, "seo_score": 38,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 99,
    },
    {
        "name": "Le Petit Rennes",
        "category": "Bistrot",
        "city": "Rennes Centre",
        "address": "19 Rue Saint-Michel, Rennes",
        "phone": "+33 2 99 79 44 32",
        "email": None,
        "google_rating": 3.8, "review_count": 32,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 0,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 149,
    },
    {
        "name": "Brasserie Georges",
        "category": "Grande Brasserie",
        "city": "Lyon 2e",
        "address": "30 Cours de Verdun, Lyon 2e",
        "phone": "+33 4 72 56 54 54",
        "email": "contact@brasseriegeorges.com",
        "google_rating": 4.3, "review_count": 1240,
        "has_website": 1, "website_url": "brasseriegeorges.com",
        "has_instagram": 1, "instagram_handle": "@brasseriegeorges", "instagram_followers": 8900,
        "has_facebook": 1, "last_post_days_ago": 2, "seo_score": 71,
        "has_digital_menu": 1, "has_online_booking": 1, "has_qr_menu": 1,
        "priority": "low", "estimated_value": 49,
    },
    {
        "name": "Le Jardin d'en Face",
        "category": "Restaurant Bistronomique",
        "city": "Paris 5e",
        "address": "12 Rue de Buci, Paris 6e",
        "phone": "+33 1 43 26 19 02",
        "email": None,
        "google_rating": 4.0, "review_count": 56,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@jardindface", "instagram_followers": 290,
        "has_facebook": 0, "last_post_days_ago": 60, "seo_score": 9,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 149,
    },
    {
        "name": "La Pataterie Grenoble",
        "category": "Restaurant Convivial",
        "city": "Grenoble",
        "address": "11 Rue Chenoise, Grenoble",
        "phone": "+33 4 76 43 20 11",
        "email": None,
        "google_rating": 3.9, "review_count": 91,
        "has_website": 1, "website_url": "lapataterie38.fr",
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 180, "seo_score": 17,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 99,
    },
    {
        "name": "Le Pub Saint-Germain",
        "category": "Bar & Restaurant",
        "city": "Paris 6e",
        "address": "17 Rue de l'Ancienne Comédie, Paris 6e",
        "phone": "+33 1 56 81 18 18",
        "email": "pub@saintgermain.fr",
        "google_rating": 4.1, "review_count": 223,
        "has_website": 1, "website_url": "pubsaintgermain.fr",
        "has_instagram": 1, "instagram_handle": "@pubsaintgermain", "instagram_followers": 1800,
        "has_facebook": 1, "last_post_days_ago": 10, "seo_score": 44,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "medium", "estimated_value": 99,
    },
    {
        "name": "Trattoria Roma",
        "category": "Restaurant Italien",
        "city": "Aix-en-Provence",
        "address": "3 Rue des Cordeliers, Aix-en-Provence",
        "phone": "+33 4 42 27 90 12",
        "email": None,
        "google_rating": 4.4, "review_count": 178,
        "has_website": 0, "website_url": None,
        "has_instagram": 1, "instagram_handle": "@trattoriaroma_aix", "instagram_followers": 760,
        "has_facebook": 1, "last_post_days_ago": 20, "seo_score": 11,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "high", "estimated_value": 149,
    },
    {
        "name": "Le Relais de Bourgogne",
        "category": "Restaurant Bourguignon",
        "city": "Dijon Centre",
        "address": "18 Rue Bannelier, Dijon",
        "phone": "+33 3 80 30 21 00",
        "email": None,
        "google_rating": 4.6, "review_count": 302,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 1, "last_post_days_ago": 45, "seo_score": 8,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 149,
    },
    {
        "name": "Kebab & Grill du Centre",
        "category": "Fast Food",
        "city": "Clermont-Ferrand",
        "address": "22 Place de Jaude, Clermont-Ferrand",
        "phone": "+33 4 73 36 00 80",
        "email": None,
        "google_rating": 3.6, "review_count": 41,
        "has_website": 0, "website_url": None,
        "has_instagram": 0, "instagram_handle": None, "instagram_followers": 0,
        "has_facebook": 0, "last_post_days_ago": 999, "seo_score": 0,
        "has_digital_menu": 0, "has_online_booking": 0, "has_qr_menu": 0,
        "priority": "urgent", "estimated_value": 79,
    },
]


def seed_db():
    conn = get_db()
    c = conn.cursor()

    # Design fields mock values — assigned based on existing data quality signals
    DESIGN_MOCK = {
        # TN prospects — most lack modern menus and pro logos
        "Restaurant Le Carthage":        {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Dar El Jeld":                   {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "Pizza Napoli Tunis":            {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Café Saf Saf":                  {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Sushi Zen Carthage":            {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "Snack Brik & More":             {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Le Gourmet Tunis":              {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Café Maure Ennejma Ezzahra":    {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Burger House Tunis":            {"has_modern_menu": 1, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Restaurant El Foundouk":        {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Patisserie Masmoudi":           {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "Taco Loco Tunis":               {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Chez Slama":                    {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Cloud Kitchen Délices":         {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Le Pêcheur Gourmet":            {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Healthy Bowl Tunis":            {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "Brasserie 1956":                {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 0, "menu_board_quality": "mauvais"},
        "Crêperie de Carthage":          {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Kebab Palace":                  {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Traiteur El Hana":              {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        # FR prospects
        "Le Bistrot du Marché":          {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Chez Michel":                   {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "La Table de Provence":          {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Brasserie des Capucins":        {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Le Comptoir Niçois":            {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "Pizzeria Napolitana":           {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Au Crocodile":                  {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "La Crêperie Bretonne":          {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "L'Estaminet du Vieux-Lille":    {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 0, "menu_board_quality": "mauvais"},
        "Sushi Fusion Montpellier":      {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Le Petit Rennes":               {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Brasserie Georges":             {"has_modern_menu": 1, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "bon"},
        "Le Jardin d'en Face":           {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "La Pataterie Grenoble":         {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 0, "menu_board_quality": "mauvais"},
        "Le Pub Saint-Germain":          {"has_modern_menu": 0, "has_pro_logo": 1, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Trattoria Roma":                {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 1, "menu_board_quality": "mauvais"},
        "Le Relais de Bourgogne":        {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
        "Kebab & Grill du Centre":       {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "inexistant"},
    }

    # Build normalized lookup for accented characters
    _design_norm = {k.lower(): v for k, v in DESIGN_MOCK.items()}

    def _get_design(name):
        return _design_norm.get(name.lower(),
               {"has_modern_menu": 0, "has_pro_logo": 0, "has_gmaps_photos": 0, "menu_board_quality": "unknown"})

    c.execute("SELECT COUNT(*) FROM prospects WHERE country = 'TN'")
    if c.fetchone()[0] == 0:
        for p in MOCK_PROSPECTS:
            d = _get_design(p["name"])
            p_full = {**p, **d}
            score, services = compute_score_and_services(p_full)
            c.execute("""
                INSERT INTO prospects (
                    name, category, address, phone, email,
                    google_rating, review_count, has_website, website_url,
                    has_instagram, instagram_handle, instagram_followers,
                    has_facebook, last_post_days_ago, seo_score,
                    status, score, services_needed, priority, estimated_value,
                    country, city,
                    has_modern_menu, has_pro_logo, has_gmaps_photos, menu_board_quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["name"], p["category"], p["address"], p["phone"], p["email"],
                p["google_rating"], p["review_count"], p["has_website"], p.get("website_url"),
                p["has_instagram"], p.get("instagram_handle"), p["instagram_followers"],
                p["has_facebook"], p["last_post_days_ago"], p["seo_score"],
                "new", score, json.dumps(services),
                p.get("priority", "medium"), p.get("estimated_value", 0),
                "TN", p.get("city", "Tunis"),
                d["has_modern_menu"], d["has_pro_logo"], d["has_gmaps_photos"], d["menu_board_quality"]
            ))
        print(f"[DB] Seeded {len(MOCK_PROSPECTS)} Tunisian prospects.")

    c.execute("SELECT COUNT(*) FROM prospects WHERE country = 'FR'")
    if c.fetchone()[0] == 0:
        for p in MOCK_FRANCE:
            d = _get_design(p["name"])
            p_full = {**p, **d}
            score, services = compute_france_score_and_services(p_full)
            c.execute("""
                INSERT INTO prospects (
                    name, category, address, phone, email,
                    google_rating, review_count, has_website, website_url,
                    has_instagram, instagram_handle, instagram_followers,
                    has_facebook, last_post_days_ago, seo_score,
                    status, score, services_needed, priority, estimated_value,
                    country, city, has_digital_menu, has_online_booking, has_qr_menu,
                    has_modern_menu, has_pro_logo, has_gmaps_photos, menu_board_quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["name"], p["category"], p["address"], p["phone"], p["email"],
                p["google_rating"], p["review_count"], p["has_website"], p.get("website_url"),
                p["has_instagram"], p.get("instagram_handle"), p["instagram_followers"],
                p["has_facebook"], p["last_post_days_ago"], p["seo_score"],
                "new", score, json.dumps(services),
                p.get("priority", "medium"), p.get("estimated_value", 0),
                "FR", p.get("city", ""),
                p.get("has_digital_menu", 0), p.get("has_online_booking", 0), p.get("has_qr_menu", 0),
                d["has_modern_menu"], d["has_pro_logo"], d["has_gmaps_photos"], d["menu_board_quality"]
            ))
        print(f"[DB] Seeded {len(MOCK_FRANCE)} French prospects.")

    conn.commit()
    conn.close()
