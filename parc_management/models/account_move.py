# models/account_move_extension.py
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Lien vers le contrat
    contrat_id = fields.Many2one(
        'parc.contrat',
        string="Contrat lié",
        ondelete='cascade',
    )
    # Client repris depuis le contrat
    client_id = fields.Many2one(
        related='contrat_id.client_id',
        string="Client",
        store=True,
        readonly=True,
    )

    # lien vers l'équipement (optionnel)
    equipement_id = fields.Many2one('parc.equipement', string="Équipement")

    # Montant total de la facture
    montant_total = fields.Float(
        string="Montant Total",
        compute='_compute_montant_total',
        store=True,
    )

    @api.depends('invoice_line_ids.price_subtotal')
    def _compute_montant_total(self):
        for inv in self:
            inv.montant_total = sum(line.price_subtotal for line in inv.invoice_line_ids)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Sélection de l'équipement, limité au client de la facture
    equipement_id = fields.Many2one(
        'parc.equipement',
        string="Équipement",
        domain="[('client_id','=', move_id.client_id)]",
        help="Choisissez un équipement déjà attribué à ce client.",
    )

    @api.onchange('equipement_id')
    def _onchange_equipement_id(self):
        for line in self:
            if line.equipement_id:
                # on remplit automatiquement la description
                line.name = line.equipement_id.name
                # si vous avez un champ 'product_id' sur l'équipement :
                if hasattr(line.equipement_id, 'product_id') and line.equipement_id.product_id:
                    line.product_id = line.equipement_id.product_id.id
                # si vous avez un champ de prix sur l'équipement (ex: purchase_price ou prix)
                prix = getattr(line.equipement_id, 'purchase_price', None) or getattr(line.equipement_id, 'prix', None)
                if prix is not None:
                    line.price_unit = prix
