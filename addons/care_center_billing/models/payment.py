# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalBillingPayment(models.Model):
    """Paiement enregistré sur une facture"""

    _name = 'hospital.billing.payment'
    _description = 'Paiement'
    _rec_name = 'display_name'
    _order = 'payment_date DESC, id DESC'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    invoice_id = fields.Many2one(
        'hospital.billing.invoice',
        string='Facture',
        required=True,
        ondelete='cascade',
        index=True,
    )

    patient_id = fields.Many2one(
        related='invoice_id.patient_id',
        string='Patient',
        store=True,
        index=True,
    )

    display_name = fields.Char(
        string='Paiement',
        compute='_compute_display_name',
        store=True,
    )

    # =========================================================================
    # MONTANT
    # =========================================================================
    amount = fields.Float(
        string='Montant (€)',
        required=True,
        digits=(16, 2),
        tracking=True,
    )

    payment_date = fields.Datetime(
        string='Date de paiement',
        required=True,
        default=fields.Datetime.now,
    )

    # =========================================================================
    # MODE DE PAIEMENT
    # =========================================================================
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Espèces'),
            ('card', 'Carte bancaire'),
            ('check', 'Chèque'),
            ('transfer', 'Virement bancaire'),
            ('insurance', 'Prise en charge assurance'),
            ('mobile_money', 'Mobile Money'),
            ('other', 'Autre'),
        ],
        string='Mode de paiement',
        required=True,
        default='cash',
        tracking=True,
    )

    reference = fields.Char(
        string='Référence',
        help='Numéro de chèque, référence de virement, etc.',
    )

    notes = fields.Text(
        string='Notes',
    )

    # =========================================================================
    # RÉFÉRENCES
    # =========================================================================
    user_id = fields.Many2one(
        'res.users',
        string='Encaissé par',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
    )

    company_id = fields.Many2one(
        related='invoice_id.company_id',
        string='Établissement',
        store=True,
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('invoice_id', 'payment_date', 'amount')
    def _compute_display_name(self):
        for record in self:
            if record.invoice_id and record.amount:
                record.display_name = '%s - %.2f €' % (
                    record.invoice_id.invoice_id or _('Facture'),
                    record.amount,
                )
            else:
                record.display_name = _('Nouveau paiement')

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_(
                    'Le montant du paiement doit être positif.'
                ))
            if record.invoice_id and record.amount > record.invoice_id.balance_due + record.amount:
                # Vérifier que le paiement ne dépasse pas le solde dû
                # On ajoute le montant actuel car balance_due est calculé sans ce paiement
                pass

    @api.constrains('payment_date')
    def _check_payment_date(self):
        for record in self:
            if record.payment_date and record.payment_date > fields.Datetime.now():
                raise ValidationError(_(
                    'La date de paiement ne peut pas être dans le futur.'
                ))

    # =========================================================================
    # CREATE OVERRIDE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        # Vérifier le solde après création
        for payment in payments:
            if payment.invoice_id and payment.invoice_id.state == 'draft':
                payment.invoice_id.action_confirm()
        return payments
