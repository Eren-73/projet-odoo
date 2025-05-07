# parc_management/models/facture.py
from odoo import models, fields, api
from datetime import date, timedelta

class ParcFacture(models.Model):
    _name = 'parc.facture'
    _description = 'Facture de Contrat de Gestion de Parc'
    _order = 'date_facture desc'

    name = fields.Char(string="Référence Facture", required=True, readonly=True, default="Nouveau")
    contrat_id = fields.Many2one('parc.contrat', string="Contrat", required=True, ondelete='cascade')
    client_id = fields.Many2one(related='contrat_id.client_id', string="Client", store=True, readonly=True)
    date_facture = fields.Date(string="Date de Facture", default=date.today(), required=True)
    date_echeance = fields.Date(string="Date d'Échéance", required=True)
    montant = fields.Float(string="Montant Total", required=True)
    statut = fields.Selection([
        ('draft', 'Brouillon'),
        ('open', 'Ouverte'),
        ('paid', 'Payée'),
        ('cancelled', 'Annulée')
    ], string="Statut", default="draft")

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('parc.facture') or 'Nouveau'
        return super(ParcFacture, self).create(vals)

    def action_ouvrir(self):
        self.write({'statut': 'open'})

    def action_payer(self):
        self.write({'statut': 'paid'})

    def action_annuler(self):
        self.write({'statut': 'cancelled'})
