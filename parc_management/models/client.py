# parc_management/models/client.py
from odoo import models, fields, api

class ParcClient(models.Model):
    _name = 'parc.client'
    _description = 'Client du Parc'

    name = fields.Char(string='Nom', required=True)
    adresse = fields.Char(string='Adresse')
    contact = fields.Char(string='Contact')
    email = fields.Char(string='Email')
    telephone = fields.Char(string='Téléphone')
    image_128 = fields.Binary(string="Image", attachment=True)
    contrat_ids = fields.One2many('parc.contrat', 'client_id', string="Contrats")
    contrat_count = fields.Integer(string="Nombre de Contrats", compute="_compute_contrat_count")

    @api.depends('contrat_ids')
    def _compute_contrat_count(self):
        for record in self:
            record.contrat_count = len(record.contrat_ids)

    def action_open_contrat_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouveau Contrat',
            'res_model': 'parc.contrat',
            'view_mode': 'form',
            'context': {
                'default_client_id': self.id,
            },
            'target': 'new'
        }
