# -*- coding: utf-8 -*-
{
    'name': 'Parc Management - Client & Portail',
    'version': '1.1',
    'summary': 'Gestion des clients, contrats, équipements, interventions, factures et tickets via un portail',
    'description': """
Module de gestion du parc informatique :
- Back-office : clients, équipements, interventions, contrats, factures
- Portail client : création et suivi de tickets
""",
    'author': 'Traore Husseni',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'portal',
        'website',
    ],
    'data': [
        # sécurité
        'security/ir.model.access.csv',
        # données de base
        'data/sequence.xml',
        'data/cron.xml',
        # menus et vues back-office
        'views/menu_views.xml',
        'views/client_views.xml',
        'views/equipement_views.xml',
        'views/intervention_views.xml',
        'views/contrat_views.xml',
        'views/facture_views.xml',
        'views/ticket_views.xml',
        # QWeb & templates portail
        'views/qweb_views.xml',
        'views/templates.xml',
    ],
    'controllers': [
        'controllers/portal.py',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
