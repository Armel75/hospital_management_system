# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from datetime import datetime


class HospitalPharmacyStockMove(models.Model):
    """Mouvement de stock tracé : entrée, sortie ou ajustement"""

    _name = 'hospital.pharmacy.stock.move'
    _description = 'Mouvement de stock'
    _order = 'date DESC, id DESC'
    _rec_name = 'reference'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    lot_id = fields.Many2one(
        'hospital.pharmacy.lot',
        string='Lot',
        required=True,
        ondelete='cascade',
        index=True,
    )

    medicament_id = fields.Many2one(
        related='lot_id.medicament_id',
        string='Médicament',
        store=True,
        readonly=True,
        index=True,
    )

    move_type = fields.Selection(
        selection=[
            ('inbound', 'Entrée'),
            ('outbound', 'Sortie'),
            ('adjustment', 'Ajustement'),
            ('initial', 'Stock initial'),
        ],
        string='Type de mouvement',
        required=True,
        tracking=True,
    )

    quantity = fields.Float(
        string='Quantité',
        required=True,
        digits=(16, 2),
        tracking=True,
        help='Quantité positive pour une entrée, négative pour une sortie',
    )

    quantity_abs = fields.Float(
        string='Quantité (absolue)',
        compute='_compute_quantity_abs',
        store=False,
    )

    # =========================================================================
    # RÉFÉRENCE
    # =========================================================================
    reference = fields.Char(
        string='Référence',
        help='Document source (ex: DISP-2025-000001, FOURN-2025-000001)',
        index=True,
    )

    date = fields.Datetime(
        string='Date du mouvement',
        required=True,
        default=fields.Datetime.now,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Responsable',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
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

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('quantity')
    def _compute_quantity_abs(self):
        for record in self:
            record.quantity_abs = abs(record.quantity)

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity == 0:
                raise ValidationError(_('La quantité doit être différente de zéro.'))
            if record.move_type in ('outbound',) and record.quantity > 0:
                raise ValidationError(_(
                    'Pour une sortie, la quantité doit être négative.'
                ))
            if record.move_type in ('inbound', 'initial') and record.quantity < 0:
                raise ValidationError(_(
                    'Pour une entrée, la quantité doit être positive.'
                ))

    # =========================================================================
    # MÉTHODES DE CRÉATION/ÉCRITURE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            move._update_lot_quantity()
        return moves

    def write(self, vals):
        # Rejeter la modification des mouvements confirmés
        if vals.get('quantity') or vals.get('lot_id'):
            raise ValidationError(_(
                'Impossible de modifier la quantité ou le lot d\'un mouvement '
                'de stock déjà enregistré. Créez un mouvement correctif.'
            ))
        return super().write(vals)

    def unlink(self):
        # Bloquer la suppression des mouvements
        raise ValidationError(_(
            'Les mouvements de stock ne peuvent pas être supprimés. '
            'Créez un mouvement d\'ajustement pour corriger.'
        ))

    # =========================================================================
    # MISE À JOUR DU LOT
    # =========================================================================
    def _update_lot_quantity(self):
        """Met à jour la quantité restante du lot après création du mouvement"""
        for move in self:
            lot = move.lot_id
            lot.current_quantity += move.quantity

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_open_lot(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lot'),
            'res_model': 'hospital.pharmacy.lot',
            'view_mode': 'form',
            'res_id': self.lot_id.id,
        }

    # =========================================================================
    # VUES PAR DÉFAUT
    # =========================================================================
    @api.model
    def _get_default_move_type(self):
        return 'inbound'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'move_type' in fields_list and 'move_type' not in defaults:
            defaults['move_type'] = 'inbound'
        if 'date' in fields_list and 'date' not in defaults:
            defaults['date'] = datetime.now()
        return defaults
