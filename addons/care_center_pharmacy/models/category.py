# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HospitalPharmacyCategory(models.Model):
    """Catégorie de médicaments (structure arborescente)"""

    _name = 'hospital.pharmacy.category'
    _description = 'Catégorie de médicaments'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'display_name'
    _order = 'sequence, name'

    name = fields.Char(
        string='Catégorie',
        required=True,
        translate=True,
    )

    display_name = fields.Char(
        string='Nom complet',
        compute='_compute_display_name',
        store=True,
    )

    parent_id = fields.Many2one(
        'hospital.pharmacy.category',
        string='Catégorie parente',
        index=True,
        ondelete='cascade',
    )

    parent_path = fields.Char(
        string='Chemin',
        index=True,
    )

    child_ids = fields.One2many(
        'hospital.pharmacy.category',
        'parent_id',
        string='Sous-catégories',
    )

    description = fields.Text(
        string='Description',
        translate=True,
    )

    sequence = fields.Integer(
        string='Séquence',
        default=10,
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    medicament_count = fields.Integer(
        string='Nombre de médicaments',
        compute='_compute_medicament_count',
    )

    @api.depends('name', 'parent_id.display_name')
    def _compute_display_name(self):
        for record in self:
            if record.parent_id:
                record.display_name = '%s / %s' % (record.parent_id.display_name, record.name)
            else:
                record.display_name = record.name

    @api.depends()
    def _compute_medicament_count(self):
        Medicament = self.env['hospital.pharmacy.medicament']
        for record in self:
            record.medicament_count = Medicament.search_count(
                [('category_id', 'child_of', record.id)]
            )
