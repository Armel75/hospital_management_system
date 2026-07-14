{
    'name': 'Centre Hospitalier - Pharmacie',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Gestion de la pharmacie hospitalière',
    'description': """
        Gestion de la Pharmacie Hospitalière
        =====================================
        Ce module étend le socle hospitalier avec la gestion complète
        de la pharmacie et des délivrances de médicaments.

        Fonctionnalités :
        - Catalogue de médicaments avec DCI, dosage, forme galénique
        - Catégories arborescentes de classification
        - Traçabilité par lots avec numéros de lot et dates de péremption
        - Mouvements de stock tracés (entrées, sorties, ajustements)
        - Délivrances aux patients avec sélection du lot
        - Contrôle automatique du stock disponible
        - Génération automatique des mouvements de stock à la délivrance
        - Alertes de stock bas et de péremption imminente
        - Prix unitaire prêt pour le module de facturation
        - Données de démonstration (catégories + médicaments courants)
    """,
    'author': 'Top 1% Odoo Healthcare',
    'website': 'https://www.care-center.com',
    'depends': [
        'care_center_base',
        'care_center_consultation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/pharmacy_data.xml',
        'views/pharmacy_views.xml',
        'views/dispensing_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 4,
}
