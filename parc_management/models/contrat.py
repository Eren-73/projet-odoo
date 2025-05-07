from odoo import models, fields, api
from datetime import date, timedelta


class ParcContrat(models.Model):
    _name = 'parc.contrat'
    _description = 'Contrat de Gestion de Parc'

    name = fields.Char(string="Nom du Contrat", required=True)
    client_id = fields.Many2one('parc.client', string="Client", required=True)
    date_debut = fields.Date(string="Date de Début", required=True)
    date_fin = fields.Date(string="Date de Fin", required=True)
    montant = fields.Float(string="Montant", required=True)

    frequence = fields.Selection([
        ('mensuel', 'Mensuel'),
        ('bimestriel', 'Bimestriel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
    ], string="Fréquence", required=True, default="mensuel")

    statut = fields.Selection([
        ('en_attente', 'En attente'),
        ('actif', 'Actif'),
        ('expire', 'Expiré')
    ], string="Statut", compute="_compute_statut", store=True)

    duree = fields.Integer(string="Durée (jours)", compute="_compute_duree", store=True)
    description = fields.Text(string="Description")
    montant_a_facturer = fields.Float(string="Montant à Facturer", compute="_compute_montant_a_facturer", store=True)

    facture_ids = fields.One2many('account.move', 'contrat_id', string="Factures liées")

    @api.depends('date_debut', 'date_fin')
    def _compute_duree(self):
        for record in self:
            if record.date_debut and record.date_fin:
                record.duree = (record.date_fin - record.date_debut).days
            else:
                record.duree = 0

    @api.depends('date_debut', 'date_fin')
    def _compute_statut(self):
        today = date.today()
        for record in self:
            if not record.date_debut or not record.date_fin:
                record.statut = 'en_attente'
            elif record.date_debut > today:
                record.statut = 'en_attente'
            elif record.date_fin < today:
                record.statut = 'expire'
            else:
                record.statut = 'actif'

    @api.depends('montant', 'frequence')
    def _compute_montant_a_facturer(self):
        for record in self:
            if record.frequence == 'mensuel':
                record.montant_a_facturer = record.montant
            elif record.frequence == 'bimestriel':
                record.montant_a_facturer = record.montant * 2
            elif record.frequence == 'trimestriel':
                record.montant_a_facturer = record.montant * 3
            elif record.frequence == 'semestriel':
                record.montant_a_facturer = record.montant * 6
            elif record.frequence == 'annuel':
                record.montant_a_facturer = record.montant * 12
            else:
                record.montant_a_facturer = 0.0

    def action_generer_factures(self):
        for contrat in self:
            if contrat.statut == 'actif':
                invoice = self.env['account.move'].create({
                    'partner_id': contrat.client_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': date.today(),
                    'invoice_date_due': date.today() + timedelta(days=30),
                    'contrat_id': contrat.id,
                    'invoice_line_ids': [(0, 0, {
                        'name': contrat.name,
                        'quantity': 1,
                        'price_unit': contrat.montant_a_facturer,
                    })]
                })
                contrat.facture_ids = [(4, invoice.id)]
