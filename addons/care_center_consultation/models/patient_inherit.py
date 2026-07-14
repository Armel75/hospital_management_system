# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class HospitalPatient(models.Model):
    """Héritage du modèle patient pour ajouter les consultations"""

    _inherit = 'hospital.patient'

    # =========================================================================
    # RELATION VERS LES CONSULTATIONS
    # =========================================================================
    consultation_ids = fields.One2many(
        'hospital.consultation',
        'patient_id',
        string='Consultations',
    )

    # =========================================================================
    # STATISTIQUES REELLES
    # =========================================================================
    @api.depends('consultation_ids.state', 'consultation_ids.consultation_date')
    def _compute_statistics(self):
        for record in self:
            consultations = record.consultation_ids.filtered(
                lambda c: c.state == 'done'
            )
            record.total_consultations = len(consultations)
            record.last_consultation_date = (
                consultations[:1].consultation_date.date()
                if consultations and consultations[:1].consultation_date
                else False
            )
