# parc_management/models/facture.py
from odoo import models, fields, api
from datetime import date, timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    contrat_id    = fields.Many2one('parc.contrat', string="Contrat lié", ondelete='cascade')
    client_id     = fields.Many2one(related='contrat_id.client_id', store=True, readonly=True, string="Client")
    montant_total = fields.Monetary(compute='_compute_montant_total', store=True, string="Montant Total")

    @api.depends('invoice_line_ids.price_subtotal')
    def _compute_montant_total(self):
        for inv in self:
            inv.montant_total = sum(inv.invoice_line_ids.mapped('price_subtotal'))


    def action_generer_facture_manuellement(self):
        """
        Cette méthode génère une facture pour le contrat sélectionné de manière manuelle.
        """
        for record in self:
            if record.contrat_id and record.contrat_id.statut == 'actif':
                self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': record.client_id.id,
                    'contrat_id': record.contrat_id.id,
                    'invoice_date': date.today(),
                    'invoice_date_due': date.today() + timedelta(days=30),
                    'invoice_line_ids': [(0, 0, {
                        'name': f'Facture pour le contrat {record.contrat_id.name}',
                        'quantity': 1,
                        'price_unit': record.contrat_id.montant,
                    })]
                })
