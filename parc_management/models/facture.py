# parc_management/models/facture.py
from odoo import models, fields, api
from datetime import date, timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    contrat_id    = fields.Many2one('parc.contrat', string="Contrat lié", ondelete='cascade')
    client_id     = fields.Many2one(related='contrat_id.client_id', store=True, readonly=True, string="Client")
    equipement_id = fields.Many2one('parc.equipement', string="Équipement", readonly=True)
    montant_total = fields.Monetary(compute='_compute_montant_total', store=True, string="Montant total")

    @api.depends('invoice_line_ids.price_subtotal')
    def _compute_montant_total(self):
        for inv in self:
            inv.montant_total = sum(inv.invoice_line_ids.mapped('price_subtotal'))

    @api.onchange('contrat_id')
    def _onchange_contrat_id(self):
        for inv in self:
            # vider les anciennes lignes
            inv.invoice_line_ids = [(5, 0, 0)]
            inv.equipement_id = False
            if inv.contrat_id and inv.contrat_id.equipment_ids:
                eq = inv.contrat_id.equipment_ids[0]
                inv.equipement_id = eq.id
                # créer la ligne de facture
                inv.invoice_line_ids = [(0, 0, {
                    'name':       eq.name,
                    'product_id': eq.product_id.id,
                    'quantity':   1,
                    'price_unit': eq.price_unit,
                })]

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        # même logique si création en code
        for inv in moves:
            if inv.contrat_id and not inv.invoice_line_ids and inv.contrat_id.equipment_ids:
                eq = inv.contrat_id.equipment_ids[0]
                inv.equipement_id = eq.id
                inv.write({
                    'invoice_line_ids': [(0,0,{
                        'name':       eq.name,
                        'product_id': eq.product_id.id,
                        'quantity':   1,
                        'price_unit': eq.price_unit,
                    })]
                })
        return moves
