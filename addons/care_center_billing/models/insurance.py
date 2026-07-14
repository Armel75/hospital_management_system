# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalBillingInsurance(models.Model):
    """Compagnie d'assurance / mutuelle"""

    _name = 'hospital.billing.insurance'
    _description = 'Assurance / Mutuelle'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
    )

    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
    )

    coverage_rate = fields.Float(
        string='Taux de prise en charge (%)',
        required=True,
        default=70.0,
        tracking=True,
        help='Pourcentage du montant total pris en charge par l\'assurance',
    )

    coverage_type = fields.Selection(
        selection=[
            ('percentage', 'Pourcentage du total'),
            ('fixed', 'Forfait fixe'),
        ],
        string='Type de couverture',
        required=True,
        default='percentage',
    )

    fixed_amount = fields.Float(
        string='Montant forfaitaire (€)',
        digits=(16, 2),
        help='Montant fixe pris en charge (si type = Forfait fixe)',
    )

    phone = fields.Char(
        string='Téléphone',
    )

    email = fields.Char(
        string='Email',
    )

    address = fields.Text(
        string='Adresse',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    invoice_count = fields.Integer(
        string='Factures liées',
        compute='_compute_invoice_count',
    )

    @api.depends()
    def _compute_invoice_count(self):
        Invoice = self.env['hospital.billing.invoice']
        for record in self:
            record.invoice_count = Invoice.search_count([('insurance_id', '=', record.id)])

    @api.constrains('coverage_rate')
    def _check_coverage_rate(self):
        for record in self:
            if record.coverage_rate < 0 or record.coverage_rate > 100:
                raise ValidationError(_(
                    'Le taux de prise en charge doit être compris entre 0 et 100%%.'
                ))

    def compute_coverage_amount(self, total_amount):
        """Calcule le montant pris en charge selon le type de couverture"""
        self.ensure_one()
        if self.coverage_type == 'percentage':
            return total_amount * (self.coverage_rate / 100.0)
        else:
            return min(self.fixed_amount, total_amount)
