# -*- coding: utf-8 -*-
from odoo import models, fields, api

STATUT_SELECTION = [
    ('en_service','En service'),
    ('en_panne',  'En panne'),
    ('retire',    'Retiré'),
]

class ParcEquipement(models.Model):
    _name = 'parc.equipement'
    _description = 'Équipement Informatique'
    _order = 'name'

    name        = fields.Char(required=True, string="Nom")
    product_id  = fields.Many2one(
                     'product.product',
                     string="Produit facturable",
                     domain="[('sale_ok','=',True)]",
                     help="Produit à utiliser pour facturer cet équipement"
                  )
    price_unit  = fields.Float(
                     related='product_id.list_price',
                     string="Prix unitaire",
                     store=True,
                     readonly=True
                  )

    # votre ancien champ
    statut      = fields.Selection(
                     selection=STATUT_SELECTION,
                     default='en_service',
                     string="Statut"
                  )
    # nouvel alias "state" pour satisfaire les domains Odoo
    state       = fields.Selection(
                     selection=STATUT_SELECTION,
                     string="Statut (alias)",
                     related='statut',
                     store=True,
                     readonly=False
                  )

    contrat_id  = fields.Many2one('parc.contrat', string="Contrat associé")
    intervention_ids = fields.One2many('parc.intervention', 'equipement_id', string="Interventions")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price

    @api.depends('intervention_ids')
    def _compute_intervention_count(self):
        for eq in self:
            eq.intervention_count = len(eq.intervention_ids)
    intervention_count = fields.Integer(
                             string="Nb. d'interventions",
                             compute='_compute_intervention_count',
                             store=True
                         )
