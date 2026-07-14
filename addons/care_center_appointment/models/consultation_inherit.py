# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HospitalConsultation(models.Model):
    """Héritage du modèle consultation pour ajouter le lien vers le rendez-vous"""

    _inherit = 'hospital.consultation'

    # =========================================================================
    # LIEN VERS LE RENDEZ-VOUS
    # =========================================================================
    appointment_id = fields.Many2one(
        'hospital.appointment',
        string='Rendez-vous source',
        readonly=True,
        copy=False,
        help='Rendez-vous à l\'origine de cette consultation',
    )
