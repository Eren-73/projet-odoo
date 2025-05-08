# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ParcEquipement(models.Model):
    _name = 'parc.equipement'
    _description = 'Équipement Informatique'
    _order = 'name'

    name             = fields.Char(required=True, string="Nom")
    serial_number    = fields.Char(string="N° de série")
    marque           = fields.Char(string="Marque")
    modele           = fields.Char(string="Modèle")
    date_achat       = fields.Date(string="Date d’achat")
    date_fin_garantie= fields.Date(string="Fin de garantie")

    client_id        = fields.Many2one('parc.client', string="Client")
    contrat_id       = fields.Many2one('parc.contrat', string="Contrat lié")
    user_id          = fields.Many2one('res.users', string="Utilisateur assigné")
    statut           = fields.Selection([
                          ('en_service','En service'),
                          ('en_panne','En panne'),
                          ('retire','Retiré'),
                        ], default='en_service', string="Statut")

    intervention_count = fields.Integer(
        string="Nb. d'interventions",
        compute='_compute_intervention_count',
        store=True)

    @api.depends('intervention_ids')
    def _compute_intervention_count(self):
        for eq in self:
            eq.intervention_count = len(eq.intervention_ids)

    # relation inverse vers les interventions
    intervention_ids = fields.One2many(
        'parc.intervention', 'equipement_id', string="Interventions")
