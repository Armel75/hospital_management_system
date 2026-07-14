# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HospitalMedicalRecord(models.Model):
    """Héritage du DME pour ajouter le type 'diagnosis'"""

    _inherit = 'hospital.medical.record'

    # =========================================================================
    # Extension des types d'enregistrement
    # =========================================================================
    record_type = fields.Selection(
        selection_add=[
            ('diagnosis', 'Diagnostic'),
        ],
        ondelete={
            'diagnosis': 'cascade',
        },
    )
