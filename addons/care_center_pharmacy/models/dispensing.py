# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalPharmacyDispensing(models.Model):
    """Délivrance de médicaments à un patient"""

    _name = 'hospital.pharmacy.dispensing'
    _description = 'Délivrance de médicaments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'dispensing_date DESC, id DESC'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    dispensing_id = fields.Char(
        string='N° Délivrance',
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

    doctor_id = fields.Many2one(
        'res.users',
        string='Médecin prescripteur',
        domain=lambda self: [('groups_id', 'in', self._get_doctor_group_ids())],
        tracking=True,
    )

    pharmacist_id = fields.Many2one(
        'res.users',
        string='Pharmacien(ne)',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )

    consultation_id = fields.Many2one(
        'hospital.consultation',
        string='Consultation',
        help='Consultation liée (optionnelle)',
        tracking=True,
    )

    dispensing_date = fields.Datetime(
        string='Date de délivrance',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )

    # =========================================================================
    # LIGNES DE DÉLIVRANCE
    # =========================================================================
    line_ids = fields.One2many(
        'hospital.pharmacy.dispensing.line',
        'dispensing_id',
        string='Médicaments délivrés',
        copy=True,
    )

    line_count = fields.Integer(
        string='Nombre de lignes',
        compute='_compute_line_count',
        store=True,
    )

    total_amount = fields.Float(
        string='Montant total (€)',
        compute='_compute_total_amount',
        store=True,
        digits=(16, 2),
    )

    # =========================================================================
    # WORKFLOW
    # =========================================================================
    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('confirmed', 'Confirmé'),
            ('done', 'Délivré'),
            ('cancelled', 'Annulé'),
        ],
        string='Statut',
        required=True,
        default='draft',
        tracking=True,
    )

    # =========================================================================
    # NOTES
    # =========================================================================
    notes = fields.Text(
        string='Notes',
    )

    # =========================================================================
    # RÉFÉRENCES
    # =========================================================================
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
    @api.depends('dispensing_id', 'patient_id', 'patient_id.display_name')
    def _compute_display_name(self):
        for record in self:
            if record.dispensing_id and record.patient_id:
                record.display_name = '%s - %s' % (
                    record.dispensing_id,
                    record.patient_id.display_name,
                )
            else:
                record.display_name = _('Nouvelle délivrance')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    @api.depends('line_ids', 'line_ids.subtotal')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('subtotal'))

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('dispensing_date')
    def _check_dispensing_date(self):
        for record in self:
            if record.dispensing_date and record.dispensing_date > fields.Datetime.now():
                raise ValidationError(_(
                    'La date de délivrance ne peut pas être dans le futur.'
                ))

    @api.constrains('line_ids')
    def _check_lines(self):
        for record in self:
            if record.state in ('confirmed', 'done') and not record.line_ids:
                raise ValidationError(_(
                    'Une délivrance doit contenir au moins un médicament.'
                ))

    # =========================================================================
    # MÉTHODES DE CRÉATION/ÉCRITURE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('dispensing_id'):
                vals['dispensing_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.pharmacy.dispensing'
                ) or _('Nouveau')
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            for record in self:
                if vals['state'] == 'confirmed':
                    # Réserver le stock (marquer comme confirmé)
                    pass
                elif vals['state'] == 'done':
                    record._create_stock_moves()
                elif vals['state'] == 'cancelled':
                    record._reverse_stock_moves()
        return res

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_confirm(self):
        """Confirmer la délivrance"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    'Seules les délivrances en brouillon peuvent être confirmées.'
                ))
            if not record.line_ids:
                raise ValidationError(_(
                    'Ajoutez au moins un médicament avant de confirmer.'
                ))
            record._check_stock_availability()
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Marquer comme délivré et générer les mouvements de stock"""
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_(
                    'Seules les délivrances confirmées peuvent être marquées comme délivrées.'
                ))
        self.write({'state': 'done'})

    def action_cancel(self):
        """Annuler la délivrance"""
        for record in self:
            if record.state == 'done':
                raise ValidationError(_(
                    'Impossible d\'annuler une délivrance déjà effectuée. '
                    'Créez un retour de stock manuel.'
                ))
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    # =========================================================================
    # STOCK MANAGEMENT
    # =========================================================================
    def _check_stock_availability(self):
        """Vérifie que le stock est suffisant pour toutes les lignes"""
        for record in self:
            for line in record.line_ids:
                if line.quantity > line.lot_id.current_quantity:
                    raise ValidationError(_(
                        'Stock insuffisant pour %s (Lot %s). '
                        'Demandé: %s, Disponible: %s'
                    ) % (
                        line.medicament_id.display_name,
                        line.lot_id.lot_number,
                        line.quantity,
                        line.lot_id.current_quantity,
                    ))

    def _create_stock_moves(self):
        """Crée les mouvements de stock de sortie pour chaque ligne"""
        StockMove = self.env['hospital.pharmacy.stock.move']
        for record in self:
            for line in record.line_ids:
                StockMove.create({
                    'lot_id': line.lot_id.id,
                    'move_type': 'outbound',
                    'quantity': -line.quantity,
                    'reference': record.dispensing_id,
                    'date': fields.Datetime.now(),
                    'notes': 'Délivrance patient: %s' % record.patient_id.display_name,
                })

    def _reverse_stock_moves(self):
        """Inverse les mouvements de stock si la délivrance est annulée après confirmation"""
        StockMove = self.env['hospital.pharmacy.stock.move']
        for record in self:
            existing_moves = StockMove.search([
                ('reference', '=', record.dispensing_id),
            ])
            if existing_moves:
                raise ValidationError(_(
                    'Des mouvements de stock existent déjà pour cette délivrance. '
                    'Utilisez l\'interface de stock pour effectuer un ajustement.'
                ))

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

    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    @api.model
    def _get_doctor_group_ids(self):
        DoctorGroup = self.env.ref('care_center_base.group_hospital_doctor', raise_if_not_found=False)
        AdminGroup = self.env.ref('care_center_base.group_hospital_admin', raise_if_not_found=False)
        group_ids = []
        if DoctorGroup:
            group_ids.append(DoctorGroup.id)
        if AdminGroup:
            group_ids.append(AdminGroup.id)
        return group_ids


class HospitalPharmacyDispensingLine(models.Model):
    """Ligne de délivrance : médicament, lot, quantité, prix"""

    _name = 'hospital.pharmacy.dispensing.line'
    _description = 'Ligne de délivrance'
    _rec_name = 'display_name'
    _order = 'id'

    # =========================================================================
    # RELATION
    # =========================================================================
    dispensing_id = fields.Many2one(
        'hospital.pharmacy.dispensing',
        string='Délivrance',
        required=True,
        ondelete='cascade',
        index=True,
    )

    company_id = fields.Many2one(
        related='dispensing_id.company_id',
        string='Établissement',
        store=True,
    )

    # =========================================================================
    # MÉDICAMENT
    # =========================================================================
    medicament_id = fields.Many2one(
        'hospital.pharmacy.medicament',
        string='Médicament',
        required=True,
        domain=[('active', '=', True)],
        tracking=True,
    )

    display_name = fields.Char(
        string='Affichage',
        compute='_compute_display_name',
        store=True,
    )

    # =========================================================================
    # LOT
    # =========================================================================
    lot_id = fields.Many2one(
        'hospital.pharmacy.lot',
        string='Lot',
        required=True,
        domain=[('state', 'not in', ('expired', 'depleted', 'quarantined')), ('current_quantity', '>', 0)],
        tracking=True,
    )

    lot_expiry = fields.Date(
        string='Péremption',
        related='lot_id.expiry_date',
        readonly=True,
        store=True,
    )

    lot_available = fields.Float(
        string='Disponible',
        related='lot_id.current_quantity',
        readonly=True,
    )

    # =========================================================================
    # QUANTITÉ & PRIX
    # =========================================================================
    quantity = fields.Float(
        string='Quantité',
        required=True,
        digits=(16, 2),
        default=1.0,
        tracking=True,
    )

    unit_price = fields.Float(
        string='Prix unitaire (€)',
        required=True,
        digits=(16, 4),
        tracking=True,
    )

    subtotal = fields.Float(
        string='Sous-total (€)',
        compute='_compute_subtotal',
        store=True,
        digits=(16, 2),
    )

    # =========================================================================
    # POSOLOGIE
    # =========================================================================
    posology = fields.Char(
        string='Posologie',
        help='Ex: 1 comprimé 3x/jour pendant 7 jours',
    )

    duration_days = fields.Integer(
        string='Durée (jours)',
        help='Durée du traitement en jours',
    )

    notes = fields.Text(
        string='Notes',
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('medicament_id', 'lot_id')
    def _compute_display_name(self):
        for record in self:
            parts = []
            if record.medicament_id:
                parts.append(record.medicament_id.display_name)
            if record.lot_id:
                parts.append('Lot: %s' % record.lot_id.lot_number)
            record.display_name = ' - '.join(parts) if parts else _('Nouvelle ligne')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.unit_price

    # =========================================================================
    # ONCHANGE
    # =========================================================================
    @api.onchange('medicament_id')
    def _onchange_medicament_id(self):
        if self.medicament_id:
            # Pré-remplir le prix unitaire depuis le catalogue
            self.unit_price = self.medicament_id.unit_price or 0.0

            # Filtrer les lots disponibles pour ce médicament
            available_lots = self.env['hospital.pharmacy.lot'].search([
                ('medicament_id', '=', self.medicament_id.id),
                ('state', 'not in', ('expired', 'depleted', 'quarantined')),
                ('current_quantity', '>', 0),
            ])
            if len(available_lots) == 1:
                self.lot_id = available_lots.id
            elif available_lots:
                return {
                    'domain': {
                        'lot_id': [('id', 'in', available_lots.ids)],
                    },
                    'warning': {
                        'title': _('Plusieurs lots disponibles'),
                        'message': _(
                            'Plusieurs lots sont disponibles pour %s. '
                            'Veuillez sélectionner le lot souhaité.'
                        ) % self.medicament_id.display_name,
                    },
                }
            else:
                return {
                    'domain': {
                        'lot_id': [('id', '=', False)],
                    },
                    'warning': {
                        'title': _('Stock insuffisant'),
                        'message': _(
                            'Aucun lot disponible pour %s. '
                            'Veuillez approvisionner le stock.'
                        ) % self.medicament_id.display_name,
                    },
                }

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id and self.lot_id.current_quantity < self.quantity:
            return {
                'warning': {
                    'title': _('Stock insuffisant'),
                    'message': _(
                        'La quantité demandée (%s) dépasse le stock disponible (%s) '
                        'pour le lot %s.'
                    ) % (self.quantity, self.lot_id.current_quantity, self.lot_id.lot_number),
                },
            }
