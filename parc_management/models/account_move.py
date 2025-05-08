# models/account_move_extension.py
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    contrat_id = fields.Many2one('parc.contrat', string="Contrat lié", ondelete='cascade')
