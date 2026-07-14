# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalPharmacyMedicament(models.Model):
    """Catalogue de médicaments / produits pharmaceutiques"""

    _name = 'hospital.pharmacy.medicament'
    _description = 'Médicament'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'name'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    name = fields.Char(
        string='Nom commercial',
        required=True,
        tracking=True,
    )

    display_name = fields.Char(
        string='Nom affiché',
        compute='_compute_display_name',
        store=True,
    )

    active_ingredient = fields.Char(
        string='Principe actif (DCI)',
        help='Dénomination Commune Internationale',
        tracking=True,
    )

    dosage = fields.Char(
        string='Dosage',
        help='Ex: 500 mg, 10 mg/ml, 5%',
        tracking=True,
    )

    # =========================================================================
    # CLASSIFICATION
    # =========================================================================
    category_id = fields.Many2one(
        'hospital.pharmacy.category',
        string='Catégorie',
        required=True,
        tracking=True,
    )

    form = fields.Selection(
        selection=[
            ('tablet', 'Comprimé'),
            ('capsule', 'Gélule'),
            ('syrup', 'Sirop'),
            ('suspension', 'Suspension'),
            ('injectable', 'Injectable'),
            ('ointment', 'Pommade'),
            ('cream', 'Crème'),
            ('gel', 'Gel'),
            ('drops_eye', 'Collyre'),
            ('drops_ear', 'Gouttes auriculaires'),
            ('drops_oral', 'Gouttes buvables'),
            ('spray', 'Spray'),
            ('aerosol', 'Aérosol'),
            ('suppository', 'Suppositoire'),
            ('powder', 'Poudre'),
            ('solution', 'Solution'),
            ('patch', 'Patch transdermique'),
            ('other', 'Autre'),
        ],
        string='Forme galénique',
        required=True,
        tracking=True,
    )

    administration_route = fields.Selection(
        selection=[
            ('oral', 'Orale'),
            ('sublingual', 'Sublinguale'),
            ('intravenous', 'Intraveineuse (IV)'),
            ('intramuscular', 'Intramusculaire (IM)'),
            ('subcutaneous', 'Sous-cutanée (SC)'),
            ('topical', 'Topique'),
            ('rectal', 'Rectale'),
            ('inhalation', 'Inhalation'),
            ('ophthalmic', 'Ophtalmique'),
            ('otic', 'Otique'),
            ('nasal', 'Nasale'),
            ('other', 'Autre'),
        ],
        string="Voie d'administration",
        required=True,
        tracking=True,
    )

    atc_code = fields.Char(
        string='Code ATC',
        help='Code de classification Anatomique Thérapeutique Chimique',
    )

    # =========================================================================
    # FABRICANT & RÉGLEMENTATION
    # =========================================================================
    manufacturer = fields.Char(
        string='Laboratoire',
        tracking=True,
    )

    prescription_required = fields.Boolean(
        string='Sur prescription',
        default=True,
        help='Ce médicament nécessite une prescription médicale',
        tracking=True,
    )

    storage_conditions = fields.Selection(
        selection=[
            ('ambient', 'Température ambiante'),
            ('refrigerated', 'Réfrigéré (2-8°C)'),
            ('frozen', 'Congelé (-18°C)'),
            ('light_sensitive', 'Sensible à la lumière'),
        ],
        string='Conditions de stockage',
        default='ambient',
    )

    # =========================================================================
    # PRIX
    # =========================================================================
    unit_price = fields.Float(
        string='Prix unitaire (€)',
        digits=(16, 4),
        tracking=True,
        help='Prix de vente unitaire toutes taxes comprises',
    )

    # =========================================================================
    # STOCK
    # =========================================================================
    total_stock = fields.Float(
        string='Stock total',
        compute='_compute_stock',
        store=True,
        digits=(16, 2),
    )

    alert_threshold = fields.Float(
        string='Seuil d\'alerte',
        default=10.0,
        help='En dessous de ce stock, une alerte visuelle est affichée',
    )

    stock_alert = fields.Boolean(
        string='Stock bas',
        compute='_compute_stock_alert',
        search='_search_stock_alert',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    description = fields.Text(
        string='Description',
        translate=True,
    )

    # =========================================================================
    # RELATIONS
    # =========================================================================
    lot_ids = fields.One2many(
        'hospital.pharmacy.lot',
        'medicament_id',
        string='Lots',
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('name', 'dosage', 'active_ingredient')
    def _compute_display_name(self):
        for record in self:
            parts = [record.name]
            if record.dosage:
                parts.append(record.dosage)
            if record.active_ingredient:
                parts.append('(%s)' % record.active_ingredient)
            record.display_name = ' '.join(parts) if parts else _('Nouveau médicament')

    @api.depends('lot_ids', 'lot_ids.current_quantity')
    def _compute_stock(self):
        for record in self:
            record.total_stock = sum(record.lot_ids.mapped('current_quantity'))

    @api.depends('total_stock', 'alert_threshold')
    def _compute_stock_alert(self):
        for record in self:
            record.stock_alert = (
                record.total_stock < record.alert_threshold
                if record.alert_threshold > 0
                else False
            )

    @api.model
    def _search_stock_alert(self, operator, value):
        if operator == '=' and value:
            return [('total_stock', '<', 10)]
        return []

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('unit_price')
    def _check_unit_price(self):
        for record in self:
            if record.unit_price and record.unit_price < 0:
                raise ValidationError(_(
                    'Le prix unitaire ne peut pas être négatif.'
                ))

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_open_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lots - %s') % self.display_name,
            'res_model': 'hospital.pharmacy.lot',
            'view_mode': 'tree,form',
            'domain': [('medicament_id', '=', self.id)],
            'context': {'default_medicament_id': self.id},
        }
