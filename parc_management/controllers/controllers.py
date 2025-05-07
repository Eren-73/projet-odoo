# -*- coding: utf-8 -*-
# from odoo import http


# class ParcManagement(http.Controller):
#     @http.route('/parc_management/parc_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/parc_management/parc_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('parc_management.listing', {
#             'root': '/parc_management/parc_management',
#             'objects': http.request.env['parc_management.parc_management'].search([]),
#         })

#     @http.route('/parc_management/parc_management/objects/<model("parc_management.parc_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('parc_management.object', {
#             'object': obj
#         })

