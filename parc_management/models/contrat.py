# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

FREQ_MAP = {
    'mensuel':     {'months': 1},
    'bimestriel':  {'months': 2},
    'trimestriel': {'months': 3},
    'semestriel':  {'months': 6},
    'annuel':      {'years': 1},
}

class ParcContrat(models.Model):
    _name = 'parc.contrat'
    _description = 'Contrat de Gestion de Parc'

    name               = fields.Char(    required=True, string="Nom du Contrat")
    client_id          = fields.Many2one('parc.client', required=True, string="Client")
    product_id         = fields.Many2one('product.product',
                                         string="Produit de Service",
                                         help="Produit à facturer pour ce contrat")
    date_debut         = fields.Date(    required=True, string="Date de Début")
    date_fin           = fields.Date(    required=True, string="Date de Fin")
    montant            = fields.Float(   required=True, string="Montant unitaire")
    frequence          = fields.Selection([
                           ('mensuel','Mensuel'),
                           ('bimestriel','Bimestriel'),
                           ('trimestriel','Trimestriel'),
                           ('semestriel','Semestriel'),
                           ('annuel','Annuel'),
                        ], default='mensuel', required=True, string="Fréquence")
    statut             = fields.Selection([
                           ('en_attente','En attente'),
                           ('actif','Actif'),
                           ('expire','Expiré'),
                        ], compute='_compute_statut', store=True, readonly=True, string="Statut")
    next_invoice_date  = fields.Date(     string="Prochaine échéance",
                                         help="Date de génération de la prochaine facture",
                                         store=True)
    description        = fields.Text(     string="Description")
    facture_ids        = fields.One2many('account.move', 'contrat_id',
                                         string="Factures liées", readonly=True)
    facture_count      = fields.Integer(compute='_compute_facture_count',
                                        store=True, readonly=True,
                                        string="Nombre de Factures")
    equipment_ids      = fields.One2many('parc.equipement', 'contrat_id',
                                         string="Équipements du contrat")

    @api.onchange('date_debut', 'frequence')
    def _onchange_date_debut_frequence(self):
        """Lorsque date_debut ou frequence change, on recalcule date_fin."""
        if self.date_debut and self.frequence:
            delta = FREQ_MAP.get(self.frequence)
            self.date_fin = (fields.Date.from_string(self.date_debut) + relativedelta(**delta)) if delta else False

    @api.depends('date_debut', 'date_fin')
    def _compute_statut(self):
        today = date.today()
        for rec in self:
            if not rec.date_debut or rec.date_debut > today:
                rec.statut = 'en_attente'
            elif rec.date_fin < today:
                rec.statut = 'expire'
            else:
                rec.statut = 'actif'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # calcul automatique de date_fin si pas fourni
            if vals.get('date_debut') and not vals.get('date_fin'):
                delta = FREQ_MAP.get(vals.get('frequence', 'mensuel'))
                if delta:
                    vals['date_fin'] = fields.Date.from_string(vals['date_debut']) + relativedelta(**delta)
            # initialisation de next_invoice_date
            if vals.get('date_debut'):
                vals.setdefault('next_invoice_date', vals['date_debut'])
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        # si date_debut ou frequence changés, on recalcule date_fin
        if 'date_debut' in vals or 'frequence' in vals:
            for rec in self:
                if rec.date_debut and rec.frequence:
                    delta = FREQ_MAP.get(rec.frequence)
                    rec.date_fin = (rec.date_debut + relativedelta(**delta)) if delta else False
        return res

    @api.depends('facture_ids')
    def _compute_facture_count(self):
        for rec in self:
            rec.facture_count = len(rec.facture_ids)

    def generate_invoice(self):
        """Crée une facture pour ce contrat en utilisant les équipements."""
        self.ensure_one()
        if self.statut != 'actif' or not self.next_invoice_date or self.next_invoice_date > date.today():
            return

        # Prépare les lignes de facture
        lines = []
        if self.equipment_ids:
            for eq in self.equipment_ids:
                lines.append((0, 0, {
                    'name':       eq.name,
                    'product_id': eq.product_id.id if eq.product_id else False,
                    'quantity':   1,
                    'price_unit': self.montant,
                }))
        elif self.product_id:
            lines.append((0, 0, {
                'name':       self.name,
                'product_id': self.product_id.id,
                'quantity':   1,
                'price_unit': self.montant,
            }))

        invoice = self.env['account.move'].create({
            'move_type':        'out_invoice',
            'partner_id':       self.client_id.id,
            'contrat_id':       self.id,
            'invoice_date':     self.next_invoice_date,
            'invoice_date_due': self.next_invoice_date + relativedelta(days=30),
            'invoice_line_ids': lines,
        })

        # Mise à jour de la prochaine échéance
        delta = FREQ_MAP.get(self.frequence)
        if delta:
            suivante = fields.Date.from_string(self.next_invoice_date) + relativedelta(**delta)
            self.next_invoice_date = suivante if suivante <= self.date_fin else False
        else:
            self.next_invoice_date = False

        return invoice

    @api.model
    def _cron_generate_invoices(self):
        today = date.today()
        contrats = self.search([
            ('statut', '=', 'actif'),
            ('next_invoice_date', '<=', today),
        ])
        for contrat in contrats:
            contrat.generate_invoice()
