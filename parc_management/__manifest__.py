# -*- coding: utf-8 -*-
{
    'name': 'Parc Management - Client',
    'version': '1.0',
    'summary': 'Gestion des clients du parc informatique',
    'description': """
Module de gestion des clients pour le parc informatique.
""",
    'author': 'Traore Husseni',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cron.xml',
        'views/menu_views.xml',
        'views/client_views.xml',
        'views/equipement_views.xml',       # <-- ajouté
        'views/intervention_views.xml',     # <-- ajouté
        'views/contrat_views.xml',
        'views/facture_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
