# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalBillingInvoice(models.Model):
    """Facture patient"""

    _name = 'hospital.billing.invoice'
    _description = 'Facture'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'invoice_date DESC, id DESC'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    invoice_id = fields.Char(
        string='N° Facture',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('Nouveau'),
    )

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )

    invoice_date = fields.Date(
        string='Date de facture',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )

    date_due = fields.Date(
        string='Date d\'échéance',
        required=True,
        compute='_compute_date_due',
        store=True,
        readonly=False,
    )

    # =========================================================================
    # SOURCE (consultation ou délivrance)
    # =========================================================================
    consultation_id = fields.Many2one(
        'hospital.consultation',
        string='Consultation',
        readonly=True,
        copy=False,
        tracking=True,
    )

    dispensing_id = fields.Many2one(
        'hospital.pharmacy.dispensing',
        string='Délivrance',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # =========================================================================
    # ASSURANCE
    # =========================================================================
    insurance_id = fields.Many2one(
        'hospital.billing.insurance',
        string='Assurance / Mutuelle',
        tracking=True,
    )

    insurance_number = fields.Char(
        string='N° d\'adhérent',
        help='Numéro d\'affiliation du patient',
    )

    coverage_rate = fields.Float(
        string='Taux de prise en charge',
        related='insurance_id.coverage_rate',
        readonly=True,
    )

    # =========================================================================
    # LIGNES DE FACTURE
    # =========================================================================
    line_ids = fields.One2many(
        'hospital.billing.invoice.line',
        'invoice_id',
        string='Lignes de facture',
        copy=True,
    )

    # =========================================================================
    # MONTANTS
    # =========================================================================
    total_amount = fields.Float(
        string='Montant total (€)',
        compute='_compute_amounts',
        store=True,
        digits=(16, 2),
        tracking=True,
    )

    insurance_amount = fields.Float(
        string='Part assurance (€)',
        compute='_compute_amounts',
        store=True,
        digits=(16, 2),
    )

    patient_amount = fields.Float(
        string='Part patient (€)',
        compute='_compute_amounts',
        store=True,
        digits=(16, 2),
    )

    # =========================================================================
    # PAIEMENTS
    # =========================================================================
    payment_ids = fields.One2many(
        'hospital.billing.payment',
        'invoice_id',
        string='Paiements',
    )

    paid_amount = fields.Float(
        string='Montant payé (€)',
        compute='_compute_payment_status',
        store=True,
        digits=(16, 2),
    )

    balance_due = fields.Float(
        string='Solde dû (€)',
        compute='_compute_payment_status',
        store=True,
        digits=(16, 2),
    )

    payment_status = fields.Selection(
        selection=[
            ('unpaid', 'Impayée'),
            ('partial', 'Partiellement payée'),
            ('paid', 'Payée'),
        ],
        string='Statut paiement',
        compute='_compute_payment_status',
        store=True,
        default='unpaid',
    )

    # =========================================================================
    # WORKFLOW
    # =========================================================================
    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('confirmed', 'Confirmée'),
            ('cancelled', 'Annulée'),
        ],
        string='Statut',
        required=True,
        default='draft',
        tracking=True,
    )

    notes = fields.Text(
        string='Notes',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Établissement',
        required=True,
        default=lambda self: self.env.company,
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    display_name = fields.Char(
        string='Affichage',
        compute='_compute_display_name',
        store=True,
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('invoice_id', 'patient_id', 'patient_id.display_name')
    def _compute_display_name(self):
        for record in self:
            if record.invoice_id and record.patient_id:
                record.display_name = '%s - %s' % (
                    record.invoice_id,
                    record.patient_id.display_name,
                )
            else:
                record.display_name = _('Nouvelle facture')

    @api.depends('invoice_date')
    def _compute_date_due(self):
        for record in self:
            if record.invoice_date:
                from datetime import timedelta
                record.date_due = record.invoice_date + timedelta(days=30)
            else:
                record.date_due = False

    @api.depends('line_ids', 'line_ids.subtotal', 'insurance_id')
    def _compute_amounts(self):
        for record in self:
            total = sum(record.line_ids.mapped('subtotal'))
            record.total_amount = total
            if record.insurance_id:
                record.insurance_amount = record.insurance_id.compute_coverage_amount(total)
                record.patient_amount = total - record.insurance_amount
            else:
                record.insurance_amount = 0.0
                record.patient_amount = total

    @api.depends('payment_ids', 'payment_ids.amount', 'total_amount')
    def _compute_payment_status(self):
        for record in self:
            paid = sum(record.payment_ids.mapped('amount'))
            record.paid_amount = paid
            balance = record.total_amount - paid
            record.balance_due = balance if balance > 0 else 0.0
            if record.total_amount == 0:
                record.payment_status = 'unpaid'
            elif paid >= record.total_amount:
                record.payment_status = 'paid'
            elif paid > 0:
                record.payment_status = 'partial'
            else:
                record.payment_status = 'unpaid'

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('line_ids')
    def _check_lines(self):
        for record in self:
            if record.state in ('confirmed',) and not record.line_ids:
                raise ValidationError(_(
                    'Une facture doit contenir au moins une ligne.'
                ))

    # =========================================================================
    # MÉTHODES DE CRÉATION/ÉCRITURE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('invoice_id'):
                vals['invoice_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.billing.invoice'
                ) or _('Nouveau')
        return super().create(vals_list)

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_confirm(self):
        """Confirmer la facture"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    'Seules les factures en brouillon peuvent être confirmées.'
                ))
            if not record.line_ids:
                raise ValidationError(_(
                    'Ajoutez au moins une ligne avant de confirmer la facture.'
                ))
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        """Annuler la facture"""
        for record in self:
            if record.payment_status == 'paid':
                raise ValidationError(_(
                    'Impossible d\'annuler une facture déjà payée. '
                    'Créez un avoir ou un remboursement.'
                ))
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    def action_register_payment(self):
        """Ouvre l'assistant de paiement"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Enregistrer un paiement'),
            'res_model': 'hospital.billing.payment',
            'view_mode': 'form',
            'context': {
                'default_invoice_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_amount': self.balance_due,
            },
        }

    # =========================================================================
    # GÉNÉRATION DEPUIS UNE CONSULTATION
    # =========================================================================
    @api.model
    def generate_from_consultation(self, consultation):
        """Génère une facture à partir d'une consultation"""
        Rate = self.env['hospital.billing.rate']
        line_vals = []

        # Ligne pour la consultation
        consultation_price = Rate.get_price('consultation', 25.0)
        line_vals.append((0, 0, {
            'description': _('Consultation médicale du %s') % (
                consultation.consultation_date.strftime('%d/%m/%Y') if consultation.consultation_date else ''
            ),
            'quantity': 1.0,
            'unit_price': consultation_price,
            'source_model': 'consultation',
            'source_id': consultation.id,
        }))

        # Lignes pour les médicaments délivrés pendant la consultation
        if consultation.consultation_id:
            # Lier via le rendez-vous ou les délivrances manuelles
            dispensing = self.env['hospital.pharmacy.dispensing'].search([
                ('consultation_id', '=', consultation.id),
                ('state', '=', 'done'),
            ])
            for disp in dispensing:
                for line in disp.line_ids:
                    line_vals.append((0, 0, {
                        'description': _('Délivrance %s - %s') % (
                            disp.dispensing_id, line.medicament_id.display_name
                        ),
                        'quantity': line.quantity,
                        'unit_price': line.unit_price,
                        'source_model': 'dispensing',
                        'source_id': disp.id,
                    }))

        invoice = self.create({
            'patient_id': consultation.patient_id.id,
            'consultation_id': consultation.id,
            'invoice_date': fields.Date.today(),
            'insurance_id': consultation.patient_id.insurance_id.id if consultation.patient_id.insurance_id else False,
            'insurance_number': consultation.patient_id.insurance_number if consultation.patient_id.insurance_number else False,
            'line_ids': line_vals,
        })
        return invoice

    # =========================================================================
    # GÉNÉRATION DEPUIS UNE DÉLIVRANCE
    # =========================================================================
    @api.model
    def generate_from_dispensing(self, dispensing):
        """Génère une facture à partir d'une délivrance"""
        line_vals = []
        for line in dispensing.line_ids:
            line_vals.append((0, 0, {
                'description': _('%s - %s') % (
                    line.medicament_id.display_name,
                    line.posology or '',
                ),
                'quantity': line.quantity,
                'unit_price': line.unit_price,
                'source_model': 'dispensing_line',
                'source_id': line.id,
            }))

        invoice = self.create({
            'patient_id': dispensing.patient_id.id,
            'dispensing_id': dispensing.id,
            'invoice_date': fields.Date.today(),
            'insurance_id': dispensing.patient_id.insurance_id.id if dispensing.patient_id.insurance_id else False,
            'insurance_number': dispensing.patient_id.insurance_number if dispensing.patient_id.insurance_number else False,
            'line_ids': line_vals,
        })
        return invoice

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_open_patient(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Patient'),
            'res_model': 'hospital.patient',
            'view_mode': 'form',
            'res_id': self.patient_id.id,
        }


class HospitalBillingInvoiceLine(models.Model):
    """Ligne de facture"""

    _name = 'hospital.billing.invoice.line'
    _description = 'Ligne de facture'
    _order = 'id'

    invoice_id = fields.Many2one(
        'hospital.billing.invoice',
        string='Facture',
        required=True,
        ondelete='cascade',
        index=True,
    )

    description = fields.Char(
        string='Description',
        required=True,
    )

    quantity = fields.Float(
        string='Quantité',
        required=True,
        default=1.0,
        digits=(16, 2),
    )

    unit_price = fields.Float(
        string='Prix unitaire (€)',
        required=True,
        digits=(16, 4),
    )

    subtotal = fields.Float(
        string='Sous-total (€)',
        compute='_compute_subtotal',
        store=True,
        digits=(16, 2),
    )

    source_model = fields.Char(
        string='Modèle source',
        help='Nom technique du modèle source (consultation, dispensing, etc.)',
    )

    source_id = fields.Integer(
        string='ID source',
        help='ID de l\'enregistrement source',
    )

    company_id = fields.Many2one(
        related='invoice_id.company_id',
        string='Établissement',
        store=True,
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.unit_price
