# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HospitalBillingRate(models.Model):
    """Grille tarifaire des actes médicaux et prestations"""

    _name = 'hospital.billing.rate'
    _description = 'Grille tarifaire'
    _rec_name = 'display_name'
    _order = 'category, code'

    name = fields.Char(
        string='Libellé',
        required=True,
        translate=True,
    )

    code = fields.Char(
        string='Code acte',
        required=True,
    )

    display_name = fields.Char(
        string='Affichage',
        compute='_compute_display_name',
        store=True,
    )

    category = fields.Selection(
        selection=[
            ('consultation', 'Consultation'),
            ('specialty', 'Consultation spécialisée'),
            ('emergency', 'Urgence'),
            ('procedure', 'Acte technique'),
            ('pharmacy', 'Pharmacie'),
            ('hospitalization', 'Hospitalisation'),
            ('imaging', 'Imagerie'),
            ('laboratory', 'Laboratoire'),
            ('other', 'Autre'),
        ],
        string='Catégorie',
        required=True,
        default='consultation',
    )

    default_price = fields.Float(
        string='Prix par défaut (€)',
        required=True,
        digits=(16, 2),
    )

    description = fields.Text(
        string='Description',
        translate=True,
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = '[%s] %s' % (record.code, record.name)

    @api.model
    def get_price(self, category, default=0.0):
        """Retourne le prix par défaut pour une catégorie donnée"""
        rate = self.search([('category', '=', category)], limit=1)
        return rate.default_price if rate else default
