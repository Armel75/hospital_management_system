# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HospitalPatient(models.Model):
    """Héritage du modèle patient pour ajouter l'historique des délivrances"""

    _inherit = 'hospital.patient'

    dispensing_ids = fields.One2many(
        'hospital.pharmacy.dispensing',
        'patient_id',
        string='Délivrances',
    )

    dispensing_count = fields.Integer(
        string='Nombre de délivrances',
        compute='_compute_dispensing_count',
        store=True,
    )

    @api.depends('dispensing_ids.state')
    def _compute_dispensing_count(self):
        for record in self:
            record.dispensing_count = len(record.dispensing_ids.filtered(
                lambda d: d.state == 'done'
            ))
