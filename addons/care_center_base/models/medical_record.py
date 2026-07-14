# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HospitalMedicalRecord(models.Model):
    """Dossier médical électronique du patient (antécédents, allergies, traitements)"""

    _name = 'hospital.medical.record'
    _description = 'Dossier Médical Électronique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'date_recorded DESC'

    # =========================================================================
    # CHAMPS PRINCIPAUX
    # =========================================================================
    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )

    record_type = fields.Selection(
        selection=[
            ('antecedent', 'Antécédent médical'),
            ('antecedent_surgical', 'Antécédent chirurgical'),
            ('allergy', 'Allergie'),
            ('chronic_disease', 'Maladie chronique'),
            ('family_history', 'Antécédent familial'),
            ('treatment', 'Traitement en cours'),
            ('vaccination', 'Vaccination'),
            ('other', 'Autre'),
        ],
        string='Type',
        required=True,
        tracking=True,
    )

    pathology = fields.Char(
        string='Pathologie / Intitulé',
        required=True,
        tracking=True,
    )

    description = fields.Text(
        string='Description',
        translate=True,
    )

    date_recorded = fields.Datetime(
        string='Date d\'enregistrement',
        default=fields.Datetime.now,
        required=True,
    )

    date_onset = fields.Date(
        string='Date de début',
        help='Date d\'apparition ou de diagnostic',
    )

    date_resolution = fields.Date(
        string='Date de résolution',
        help='Date de guérison ou de fin du traitement',
    )

    condition_active = fields.Boolean(
        string='Condition active',
        default=True,
        help='Cocher si la condition est toujours active',
    )

    severity = fields.Selection(
        selection=[
            ('low', 'Faible'),
            ('medium', 'Moyen'),
            ('high', 'Élevé'),
            ('critical', 'Critique'),
        ],
        string='Sévérité',
        default='medium',
    )

    notes = fields.Text(
        string='Notes complémentaires',
    )

    # =========================================================================
    # RÉFÉRENCES
    # =========================================================================
    doctor_id = fields.Many2one(
        'res.users',
        string='Médecin traitant / Diagnostiqueur',
        tracking=True,
    )

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Documents joints',
        domain=[('res_model', '=', 'hospital.medical.record')],
    )

    # =========================================================================
    # CHAMPS DIVERS
    # =========================================================================
    display_name = fields.Char(
        string='Affichage',
        compute='_compute_display_name',
        store=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Établissement',
        required=True,
        default=lambda self: self.env.company,
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    # =========================================================================
    # MÉTHODES COMPUTED
    # =========================================================================
    @api.depends('record_type', 'pathology', 'patient_id')
    def _compute_display_name(self):
        for record in self:
            name = '%s - %s' % (
                dict(record._fields['record_type'].selection).get(record.record_type, ''),
                record.pathology or '',
            )
            if record.patient_id:
                name = '[%s] %s' % (record.patient_id.display_name, name)
            record.display_name = name

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_toggle_active(self):
        """Basculer le statut actif/inactif"""
        for record in self:
            record.condition_active = not record.condition_active
