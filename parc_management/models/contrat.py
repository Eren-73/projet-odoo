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

class ParcContratLine(models.Model):
    _name = 'parc.contrat.line'
    _description = 'Ligne d’équipement du contrat'

    contrat_id = fields.Many2one(
        'parc.contrat', string='Contrat',
        ondelete='cascade', required=True,
    )
    equipment_id = fields.Many2one(
        'parc.equipement', string='Équipement', required=True,
        domain=[('statut','=','en_service')],
        help="Choisissez un équipement à facturer"
    )  # ou tout autre filtre que vous voulez

    product_id = fields.Many2one(
        'product.product', string='Produit', related='equipment_id.product_id', store=True
    )
    quantity = fields.Float(
        string='Quantité', default=1.0, required=True,
    )
    price_unit = fields.Float(
        string='Prix unitaire',
        related='equipment_id.price_unit', readonly=True, store=True,
    )
    subtotal = fields.Float(
        string='Sous-total',
        compute='_compute_subtotal', store=True,
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit


class ParcContrat(models.Model):
    _name = 'parc.contrat'
    _description = 'Contrat de Gestion de Parc'

    name               = fields.Char(required=True, string='Nom du Contrat')
    client_id          = fields.Many2one(
                            'parc.client', string='Client',
                            ondelete='cascade', required=True)
    equipment_line_ids = fields.One2many(
                            'parc.contrat.line', 'contrat_id',
                            string='Lignes d’équipement')
    amount_total       = fields.Float(
                            string='Montant total',
                            compute='_compute_amount_total', store=True)

    date_debut         = fields.Date(required=True, string='Date de Début')
    date_fin           = fields.Date(required=True, string='Date de Fin')
    frequence          = fields.Selection([
                            ('mensuel','Mensuel'),
                            ('bimestriel','Bimestriel'),
                            ('trimestriel','Trimestriel'),
                            ('semestriel','Semestriel'),
                            ('annuel','Annuel'),
                        ], default='mensuel', required=True,
                        string='Fréquence')
    statut             = fields.Selection([
                            ('en_attente','En attente'),
                            ('actif','Actif'),
                            ('expire','Expiré'),
                        ], compute='_compute_statut', store=True,
                        readonly=True, string='Statut')
    next_invoice_date  = fields.Date(string='Prochaine échéance',
                            help='Date de génération de la prochaine facture',
                            store=True)
    description        = fields.Text(string='Description')
    facture_ids        = fields.One2many(
                            'account.move', 'contrat_id',
                            string='Factures liées', readonly=True)
    facture_count      = fields.Integer(
                            compute='_compute_facture_count', store=True,
                            readonly=True, string='Nombre de Factures')

    @api.depends('equipment_line_ids.subtotal')
    def _compute_amount_total(self):
        for ctr in self:
            ctr.amount_total = sum(line.subtotal for line in ctr.equipment_line_ids)

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
            if vals.get('date_debut') and not vals.get('date_fin'):
                delta = FREQ_MAP.get(vals.get('frequence', 'mensuel'))
                if delta:
                    vals['date_fin'] = (fields.Date.from_string(vals['date_debut']) +
                                        relativedelta(**delta))
            if vals.get('date_debut'):
                vals.setdefault('next_invoice_date', vals['date_debut'])
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'date_debut' in vals or 'frequence' in vals:
            for rec in self:
                if rec.date_debut and rec.frequence:
                    delta = FREQ_MAP.get(rec.frequence)
                    rec.date_fin = (rec.date_debut +
                                    relativedelta(**delta)) if delta else False
        return res

    @api.depends('facture_ids')
    def _compute_facture_count(self):
        for rec in self:
            rec.facture_count = len(rec.facture_ids)

    def generate_invoice(self):
        self.ensure_one()
        if self.statut != 'actif' or not self.next_invoice_date or \
           self.next_invoice_date > date.today():
            return
        lines = []
        for ln in self.equipment_line_ids:
            lines.append((0, 0, {
                'name':       ln.product_id.display_name,
                'product_id': ln.product_id.id,
                'quantity':   ln.quantity,
                'price_unit': ln.price_unit,
            }))
        if not lines and self.product_id:
            lines.append((0, 0, {
                'name':       self.name,
                'product_id': self.product_id.id,
                'quantity':   1,
                'price_unit': self.montant,
            }))
        if not lines:
            raise UserError(
                _('Aucun produit/service sélectionné pour générer la facture.')
            )
        invoice = self.env['account.move'].create({
            'move_type':        'out_invoice',
            'partner_id':       self.client_id.id,
            'contrat_id':       self.id,
            'invoice_date':     self.next_invoice_date,
            'invoice_date_due': self.next_invoice_date + relativedelta(days=30),
            'invoice_line_ids': lines,
        })
        delta = FREQ_MAP.get(self.frequence)
        if delta:
            suivante = (fields.Date.from_string(self.next_invoice_date) +
                        relativedelta(**delta))
            self.next_invoice_date = (suivante
                if suivante and suivante <= self.date_fin else False)
        else:
            self.next_invoice_date = False
        return invoice

    def unlink(self):
        for contrat in self:
            contrat.facture_ids.unlink()
        return super().unlink()

    @api.model
    def _cron_generate_invoices(self):
        today = date.today()
        contrats = self.search([
            ('statut', '=', 'actif'),
            ('next_invoice_date', '<=', today),
        ])
        for contrat in contrats:
            contrat.generate_invoice()
