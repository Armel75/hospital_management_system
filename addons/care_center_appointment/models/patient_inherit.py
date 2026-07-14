# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HospitalPatient(models.Model):
    """Héritage du modèle patient pour ajouter les rendez-vous"""

    _inherit = 'hospital.patient'

    # =========================================================================
    # RELATION VERS LES RENDEZ-VOUS
    # =========================================================================
    appointment_ids = fields.One2many(
        'hospital.appointment',
        'patient_id',
        string='Rendez-vous',
    )

    next_appointment_date = fields.Datetime(
        string='Prochain rendez-vous',
        compute='_compute_next_appointment',
        store=True,
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('appointment_ids.state', 'appointment_ids.appointment_date')
    def _compute_next_appointment(self):
        for record in self:
            future_appointments = record.appointment_ids.filtered(
                lambda a: a.state in ('draft', 'confirmed')
                and a.appointment_date > fields.Datetime.now()
            ).sorted(key=lambda a: a.appointment_date)
            record.next_appointment_date = (
                future_appointments[:1].appointment_date
                if future_appointments
                else False
            )
