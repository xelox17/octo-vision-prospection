import json


def generate_email(prospect):
    """Generate a personalized cold email for a prospect."""
    name = prospect["name"]
    services = json.loads(prospect["services_needed"]) if isinstance(prospect["services_needed"], str) else prospect["services_needed"]
    category = prospect["category"]

    # Pick the top 2 pain points
    pain_points = []
    if not prospect["has_website"]:
        pain_points.append("l'absence d'un site web professionnel qui limite votre visibilité en ligne")
    if prospect["seo_score"] < 30:
        pain_points.append("un référencement Google très faible qui empêche vos clients potentiels de vous trouver")
    if not prospect["has_instagram"]:
        pain_points.append("l'absence d'une présence sur Instagram, la plateforme numéro 1 pour les restaurants")
    if prospect["last_post_days_ago"] > 60:
        pain_points.append("une inactivité sur les réseaux sociaux qui fait perdre l'engagement de votre audience")
    if prospect["review_count"] < 50:
        pain_points.append("un faible nombre d'avis Google qui freine la confiance des nouveaux clients")

    pain_text = pain_points[0] if pain_points else "un potentiel digital encore inexploité"

    services_text = ", ".join(services[:3]) if services else "nos solutions digitales"

    subject = f"Boostez la visibilité de {name} en ligne — Opportunité exclusive"

    body = f"""Objet : {subject}

Bonjour,

Je m'appelle [Votre Prénom], consultant en marketing digital chez Octo Vision Digital Solutions (octovisiondigitalsolutions.com).

En analysant les établissements de {category.lower()} à Tunis, j'ai remarqué {pain_text} pour {name}.

Dans un marché où 80% des Tunisiens recherchent des restaurants en ligne avant de se déplacer, cette situation représente une perte directe de clients chaque jour.

Chez Octo Vision, nous aidons les restaurants tunisiens à :
✅ Attirer plus de clients grâce à un positionnement Google optimisé
✅ Créer une image professionnelle et mémorable sur les réseaux sociaux
✅ Générer des réservations et commandes en ligne régulières

Pour {name}, nous recommandons spécifiquement : **{services_text}**.

Je vous propose un audit digital GRATUIT de 30 minutes pour vous montrer exactement ce que vous manquez et comment y remédier rapidement.

Êtes-vous disponible cette semaine pour un appel rapide ?

Cordialement,
[Votre Prénom] | Octo Vision Digital Solutions
📧 contact@octovisiondigitalsolutions.com
🌐 octovisiondigitalsolutions.com
📱 +216 XX XXX XXX"""

    return subject, body


def generate_dm(prospect):
    """Generate a personalized Instagram/Facebook DM."""
    name = prospect["name"]
    services = json.loads(prospect["services_needed"]) if isinstance(prospect["services_needed"], str) else prospect["services_needed"]

    if not prospect["has_instagram"] and not prospect["has_facebook"]:
        platform = "message"
    elif prospect["has_instagram"]:
        platform = "Instagram"
    else:
        platform = "Facebook"

    # Short, punchy DM
    if not prospect["has_website"]:
        hook = f"J'ai remarqué que {name} n'a pas encore de site web — en 2024, c'est 30% de clients en moins !"
    elif prospect["last_post_days_ago"] > 60:
        hook = f"Votre dernière publication remonte à plus de {prospect['last_post_days_ago']} jours — vos concurrents en profitent !"
    elif prospect["seo_score"] < 20:
        hook = f"Votre restaurant n'apparaît pratiquement pas sur Google — vos clients ne peuvent pas vous trouver !"
    else:
        hook = f"J'ai analysé la présence digitale de {name} et j'ai repéré des opportunités concrètes à saisir rapidement."

    top_service = services[0] if services else "notre accompagnement digital"

    body = f"""Bonjour {name} ! 👋

{hook}

Nous sommes Octo Vision Digital Solutions, agence de marketing digital spécialisée dans les restaurants tunisiens.

On aide des établissements comme le vôtre à doubler leur visibilité en ligne en moins de 3 mois 🚀

Votre priorité : **{top_service}**

💡 On offre un audit gratuit — pas de prise de tête, juste des résultats concrets.

Intéressé(e) ? Répondez ici ou visitez octovisiondigitalsolutions.com

— L'équipe Octo Vision 🌐"""

    return body


def generate_whatsapp(prospect):
    """Generate a WhatsApp message template."""
    name = prospect["name"]
    services = json.loads(prospect["services_needed"]) if isinstance(prospect["services_needed"], str) else prospect["services_needed"]
    top_service = services[0] if services else "votre présence digitale"

    body = f"""Bonjour ! Je suis [Prénom] de Octo Vision Digital Solutions 👋

J'ai analysé la présence en ligne de *{name}* et j'ai identifié des axes d'amélioration importants, notamment : *{top_service}*.

Nous aidons les restaurants tunisiens à attirer plus de clients via le digital.

Je vous propose un audit gratuit de 20 min cette semaine — ça vous intéresse ?

🌐 octovisiondigitalsolutions.com"""

    return body
