# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HospitalConsultation(models.Model):
    """Héritage consultation pour ajouter la facturation"""

    _inherit = 'hospital.consultation'

    # =========================================================================
    # STATUT FACTURATION
    # =========================================================================
    invoice_status = fields.Selection(
        selection=[
            ('not_invoiced', 'Non facturée'),
            ('invoiced', 'Facturée'),
        ],
        string='Statut facturation',
        compute='_compute_invoice_status',
        store=True,
        default='not_invoiced',
    )

    invoice_ids = fields.One2many(
        'hospital.billing.invoice',
        'consultation_id',
        string='Factures',
    )

    invoice_count = fields.Integer(
        string='Nb factures',
        compute='_compute_invoice_count',
    )

    @api.depends('invoice_ids', 'invoice_ids.state')
    def _compute_invoice_status(self):
        for record in self:
            if record.invoice_ids.filtered(lambda i: i.state == 'confirmed'):
                record.invoice_status = 'invoiced'
            else:
                record.invoice_status = 'not_invoiced'

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    # =========================================================================
    # ACTION GÉNÉRER FACTURE
    # =========================================================================
    def action_generate_invoice(self):
        """Génère une facture pour cette consultation"""
        self.ensure_one()
        Invoice = self.env['hospital.billing.invoice']

        # Vérifier si une facture existe déjà
        existing = self.invoice_ids.filtered(lambda i: i.state != 'cancelled')
        if existing:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Facture existante'),
                'res_model': 'hospital.billing.invoice',
                'view_mode': 'form',
                'res_id': existing[0].id,
            }

        invoice = Invoice.generate_from_consultation(self)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facture'),
            'res_model': 'hospital.billing.invoice',
            'view_mode': 'form',
            'res_id': invoice.id,
        }
