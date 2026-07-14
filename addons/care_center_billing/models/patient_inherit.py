# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HospitalPatient(models.Model):
    """Héritage patient pour ajouter les infos de facturation"""

    _inherit = 'hospital.patient'

    # =========================================================================
    # ASSURANCE
    # =========================================================================
    insurance_id = fields.Many2one(
        'hospital.billing.insurance',
        string='Assurance / Mutuelle',
        tracking=True,
        help='Assurance ou mutuelle du patient',
    )

    insurance_number = fields.Char(
        string="N° d'adhérent",
        help="Numéro d'affiliation à l'assurance",
    )

    # =========================================================================
    # FACTURATION
    # =========================================================================
    invoice_ids = fields.One2many(
        'hospital.billing.invoice',
        'patient_id',
        string='Factures',
    )

    invoice_count = fields.Integer(
        string='Nombre de factures',
        compute='_compute_invoice_count',
        store=True,
    )

    total_invoiced = fields.Float(
        string='Total facturé (€)',
        compute='_compute_invoice_totals',
        digits=(16, 2),
    )

    total_unpaid = fields.Float(
        string='Impayé (€)',
        compute='_compute_invoice_totals',
        digits=(16, 2),
    )

    @api.depends('invoice_ids.state', 'invoice_ids.payment_status')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids.filtered(
                lambda i: i.state == 'confirmed'
            ))

    @api.depends('invoice_ids.total_amount', 'invoice_ids.balance_due',
                 'invoice_ids.state')
    def _compute_invoice_totals(self):
        for record in self:
            confirmed = record.invoice_ids.filtered(lambda i: i.state == 'confirmed')
            record.total_invoiced = sum(confirmed.mapped('total_amount'))
            record.total_unpaid = sum(confirmed.mapped('balance_due'))
