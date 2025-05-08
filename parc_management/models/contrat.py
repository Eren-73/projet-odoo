# parc_management/models/contrat.py
from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import UserError

class ParcContrat(models.Model):
    _name = 'parc.contrat'
    _description = 'Contrat de Gestion de Parc'

    name               = fields.Char(required=True, string="Nom du Contrat")
    client_id          = fields.Many2one('parc.client', required=True, string="Client")
    date_debut         = fields.Date(required=True, string="Date de Début")
    date_fin           = fields.Date(required=True, string="Date de Fin")
    montant            = fields.Float(required=True, string="Montant")
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
    duree              = fields.Integer(compute='_compute_duree', store=True, readonly=True, string="Durée (jours)")
    description        = fields.Text(string="Description")
    montant_a_facturer = fields.Float(compute='_compute_montant_a_facturer', store=True, readonly=True, string="Montant à Facturer")

    facture_ids        = fields.One2many('account.move', 'contrat_id', string="Factures liées", readonly=True)
    facture_count      = fields.Integer(compute='_compute_facture_count', store=True, readonly=True, string="Nombre de Factures")


    next_invoice_date = fields.Date(
        string="Prochaine facturation",
        default=lambda self: self.date_debut or fields.Date.today(),
        readonly=True, copy=False,
        help="Le jour où la prochaine facture doit être générée."
    )


    @api.depends('date_debut','date_fin')
    def _compute_duree(self):
        for r in self:
            r.duree = (r.date_fin - r.date_debut).days if r.date_debut and r.date_fin else 0

    @api.depends('date_debut','date_fin')
    def _compute_statut(self):
        today = date.today()
        for r in self:
            if not r.date_debut or not r.date_fin or r.date_debut > today:
                r.statut = 'en_attente'
            elif r.date_fin < today:
                r.statut = 'expire'
            else:
                r.statut = 'actif'

    @api.depends('montant','frequence')
    def _compute_montant_a_facturer(self):
        coeff = {'mensuel':1,'bimestriel':2,'trimestriel':3,'semestriel':6,'annuel':12}
        for r in self:
            r.montant_a_facturer = r.montant * coeff.get(r.frequence, 0)

    @api.depends('facture_ids')
    def _compute_facture_count(self):
        for r in self:
            r.facture_count = len(r.facture_ids)

    def action_generer_factures(self):
        for contrat in self:
            if contrat.statut != 'actif':
                raise UserError(_("Seuls les contrats 'Actif' peuvent générer des factures."))
            if not contrat.montant_a_facturer:
                raise UserError(_("Le montant à facturer est à 0. Vérifiez le contrat."))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': contrat.client_id.id,
                'contrat_id': contrat.id,
                'invoice_date': date.today(),
                'invoice_date_due': date.today() + timedelta(days=30),
                'invoice_line_ids': [(0, 0, {
                    'name': contrat.name,
                    'quantity': 1,
                    'price_unit': contrat.montant_a_facturer,
                    'account_id': self.env.ref('l10n_syscohada.account_income', False).id or False,
                })]
            })
            # le One2many se met à jour automatiquement, pas besoin de write manuel

    @api.model
    def _cron_generate_invoices(self):
        """Appelée par le cron chaque jour."""
        today = fields.Date.today()
        # On ne traite que les contrats actifs dont next_invoice_date est dans la période
        contrats = self.search([
            ('statut', '=', 'actif'),
            ('next_invoice_date', '<=', today),
            ('next_invoice_date', '<=', 'date_fin'),
        ])
        for c in contrats:
            # Génération de la facture
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': c.client_id.id,
                'contrat_id': c.id,
                'invoice_date': c.next_invoice_date,
                'invoice_date_due': c.next_invoice_date + timedelta(days=30),
                'invoice_line_ids': [(0, 0, {
                    'name': c.name,
                    'quantity': 1,
                    'price_unit': c.montant_a_facturer,
                    'account_id': self.env
                                      .ref('l10n_syscohada.account_income', False)
                                      .id or False,
                })],
            })
            # Avance next_invoice_date selon la fréquence
            delta = {
                'mensuel': relativedelta(months=+1),
                'bimestriel': relativedelta(months=+2),
                'trimestriel': relativedelta(months=+3),
                'semestriel': relativedelta(months=+6),
                'annuel': relativedelta(years=+1),
            }[c.frequence]
            c.next_invoice_date = c.next_invoice_date + delta
            # Si on a dépassé la fin, on ne programme plus
            if c.next_invoice_date > c.date_fin:
                c.statut = 'expire'
