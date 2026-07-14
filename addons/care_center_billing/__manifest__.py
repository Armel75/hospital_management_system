{
    'name': 'Centre Hospitalier - Facturation',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Gestion de la facturation et des paiements',
    'description': """
        Gestion de la Facturation Hospitalière
        =======================================
        Ce module finalise le système de gestion hospitalière avec
        la facturation complète des consultations et délivrances.

        Fonctionnalités :
        - Facturation des consultations et délivrances de médicaments
        - Grille tarifaire des actes médicaux (consultation, spécialiste, urgence...)
        - Gestion des assurances et mutuelles avec calcul automatique
        - Calcul automatique part assurance / part patient
        - Génération automatique de facture depuis une consultation
        - Génération automatique de facture depuis une délivrance
        - Suivi des paiements (espèces, carte, chèque, virement, mobile money)
        - Statut de paiement : impayée / partielle / payée
        - Alertes factures en retard
        - Tableaux de bord et statistiques de facturation
        - Numérotation automatique FAC-YYYY-000001
    """,
    'author': 'Top 1% Odoo Healthcare',
    'website': 'https://www.care-center.com',
    'depends': [
        'care_center_base',
        'care_center_consultation',
        'care_center_pharmacy',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/billing_data.xml',
        'views/billing_views.xml',
        'views/invoice_views.xml',
        'views/inherit_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 5,
}
