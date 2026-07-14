# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class HospitalPharmacyLot(models.Model):
    """Lot de médicaments avec traçabilité et péremption"""

    _name = 'hospital.pharmacy.lot'
    _description = 'Lot de médicaments'
    _rec_name = 'display_name'
    _order = 'expiry_date, lot_number'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    medicament_id = fields.Many2one(
        'hospital.pharmacy.medicament',
        string='Médicament',
        required=True,
        ondelete='cascade',
        index=True,
    )

    lot_number = fields.Char(
        string='Numéro de lot',
        required=True,
        tracking=True,
    )

    display_name = fields.Char(
        string='Lot',
        compute='_compute_display_name',
        store=True,
    )

    # =========================================================================
    # DATES
    # =========================================================================
    manufacturing_date = fields.Date(
        string='Date de fabrication',
    )

    expiry_date = fields.Date(
        string='Date d\'expiration',
        required=True,
        tracking=True,
    )

    days_until_expiry = fields.Integer(
        string='Jours restants',
        compute='_compute_days_until_expiry',
        store=True,
    )

    is_expired = fields.Boolean(
        string='Périmé',
        compute='_compute_days_until_expiry',
        store=True,
    )

    # =========================================================================
    # QUANTITÉS
    # =========================================================================
    initial_quantity = fields.Float(
        string='Quantité initiale',
        required=True,
        digits=(16, 2),
        tracking=True,
    )

    current_quantity = fields.Float(
        string='Quantité restante',
        required=True,
        digits=(16, 2),
        default=0.0,
        tracking=True,
        help='Quantité encore disponible. Mise à jour automatiquement par les mouvements de stock.',
    )

    # =========================================================================
    # PRIX
    # =========================================================================
    purchase_price = fields.Float(
        string="Prix d'achat (€)",
        digits=(16, 4),
        help="Prix d'achat du lot",
    )

    # =========================================================================
    # STOCKAGE
    # =========================================================================
    location = fields.Char(
        string='Emplacement',
        help='Localisation dans la pharmacie (ex: A-12, Réfrigérateur 2)',
    )

    state = fields.Selection(
        selection=[
            ('in_stock', 'En stock'),
            ('low_stock', 'Stock faible'),
            ('depleted', 'Épuisé'),
            ('expired', 'Périmé'),
            ('quarantined', 'En quarantaine'),
        ],
        string='État',
        compute='_compute_state',
        store=True,
        default='in_stock',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    notes = fields.Text(
        string='Notes',
    )

    # =========================================================================
    # RELATIONS
    # =========================================================================
    stock_move_ids = fields.One2many(
        'hospital.pharmacy.stock.move',
        'lot_id',
        string='Mouvements de stock',
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('medicament_id', 'lot_number')
    def _compute_display_name(self):
        for record in self:
            if record.medicament_id and record.lot_number:
                record.display_name = '%s - Lot %s' % (
                    record.medicament_id.display_name,
                    record.lot_number,
                )
            else:
                record.display_name = _('Nouveau lot')

    @api.depends('expiry_date')
    def _compute_days_until_expiry(self):
        today = date.today()
        for record in self:
            if record.expiry_date:
                delta = (record.expiry_date - today).days
                record.days_until_expiry = delta
                record.is_expired = delta < 0
            else:
                record.days_until_expiry = 0
                record.is_expired = False

    @api.depends('current_quantity', 'is_expired')
    def _compute_state(self):
        for record in self:
            if record.is_expired:
                record.state = 'expired'
            elif record.current_quantity <= 0:
                record.state = 'depleted'
            elif record.current_quantity < 10:
                record.state = 'low_stock'
            else:
                record.state = 'in_stock'

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        for record in self:
            if record.expiry_date and record.expiry_date < date.today():
                raise ValidationError(_(
                    'La date d\'expiration est déjà dépassée. '
                    'Utilisez l\'état "Périmé" ou vérifiez la date.'
                ))

    @api.constrains('current_quantity', 'initial_quantity')
    def _check_quantities(self):
        for record in self:
            if record.current_quantity < 0:
                raise ValidationError(_(
                    'La quantité restante ne peut pas être négative. '
                    'Vérifiez les mouvements de stock.'
                ))
            if record.initial_quantity < 0:
                raise ValidationError(_(
                    'La quantité initiale ne peut pas être négative.'
                ))

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_open_stock_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mouvements - %s') % self.display_name,
            'res_model': 'hospital.pharmacy.stock.move',
            'view_mode': 'tree,form',
            'domain': [('lot_id', '=', self.id)],
        }

    def action_receive_stock(self):
        """Assistant rapide pour réceptionner du stock"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Réceptionner du stock'),
            'res_model': 'hospital.pharmacy.stock.move',
            'view_mode': 'form',
            'context': {
                'default_lot_id': self.id,
                'default_move_type': 'inbound',
                'default_quantity': 0,
            },
        }
