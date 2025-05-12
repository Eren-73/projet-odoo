# controllers/portal.py
from odoo import http
from odoo.http import request

class PortalTicket(http.Controller):

    @http.route(['/my/tickets', '/my/ticket'], type='http', auth="user", website=True)
    def portal_ticket_list(self, **kw):
        tickets = request.env['parc.ticket'].search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ], order='date_open desc')
        return request.render(
            'parc_management.portal_ticket_list',  # correspond à l’ID de votre template
            {'tickets': tickets}
        )
