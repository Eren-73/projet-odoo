# parc_management/models/intervention.py
from odoo import models, fields, api
from datetime import datetime

class ParcIntervention(models.Model):
    _name = 'parc.intervention'
    _description = 'Intervention Parc'

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('parc.intervention') or '/'
    )
    client_id = fields.Many2one(
        'parc.client',
        string="Client",
        required=True,
    )
    equipement_id = fields.Many2one(
        'parc.equipement',
        string="Équipement",
        required=True,
    )
    technicien_id = fields.Many2one(
        'res.users',
        string="Technicien",
        help="Utilisateur en charge de l'intervention",
    )
    date_ouverture = fields.Datetime(
        string="Date d'ouverture",
        default=fields.Datetime.now,
        readonly=True,
    )
    date_cloture = fields.Datetime(
        string="Date de clôture",
        readonly=True,
    )
    state = fields.Selection([
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé'),
    ], string="État", default='en_attente', required=True)
    description = fields.Text(
        string="Description de l'incident",
    )
    resolution = fields.Text(
        string="Résolution apportée",
    )

    @api.model
    def create(self, vals):
        # Fixer la date d'ouverture à la création
        vals.setdefault('date_ouverture', datetime.now())
        return super().create(vals)

    def action_resoudre(self):
        for rec in self:
            rec.state = 'resolu'
            rec.date_cloture = datetime.now()

    def action_fermer(self):
        for rec in self:
            rec.state = 'ferme'
