# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError

class ParcTicket(models.Model):
    _name = 'parc.ticket'
    _description = 'Ticket Front-Office'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_open desc'

    name          = fields.Char(string="Objet", required=True, tracking=True)
    partner_id    = fields.Many2one(
        'res.partner', string="Client",
        default=lambda self: self.env.user.partner_id,
        readonly=True
    )
    user_id       = fields.Many2one('res.users', string="Assigné à", tracking=True)
    date_open     = fields.Datetime(
        string="Ouverture", default=fields.Datetime.now, readonly=True
    )
    date_deadline = fields.Datetime(string="Échéance")
    state         = fields.Selection([
                        ('open',    'Ouvert'),
                        ('pending', 'En attente'),
                        ('done',    'Résolu'),
                        ('cancel',  'Annulé'),
                    ], default='open', string="Statut", tracking=True)
    description   = fields.Text(string="Description", help="Détail du problème")

    @api.model
    def create(self, vals):
        # restreindre la création aux portal users
        if self.env.user.has_group('base.group_portal'):
            vals['partner_id'] = self.env.user.partner_id.id
        return super().create(vals)

    def action_ticket_close(self):
        """Passe le ticket en 'done' si l'utilisateur a le droit."""
        for ticket in self:
            if not self.env.user.has_group('base.group_user'):
                raise AccessError("Vous n'avez pas le droit de clôturer ce ticket.")
            ticket.state = 'done'
        return True
