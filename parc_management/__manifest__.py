# parc_management/__manifest__.py
{
    'name': 'Parc Management - Client',
    'version': '1.0',
    'summary': 'Gestion des clients du parc informatique',
    'description': """
Module de gestion des clients pour le parc informatique.
""",
    'author': 'Traore Husseni',
    'depends': ['base','account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_facture.xml',
        'views/client_views.xml',
        'views/contrat_views.xml',
        'views/facture_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
