# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalConsultation(models.Model):
    """Consultation médicale d'un patient avec un médecin"""

    _name = 'hospital.consultation'
    _description = 'Consultation Médicale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'consultation_date DESC, id DESC'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    consultation_id = fields.Char(
        string='N° Consultation',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('Nouveau'),
    )

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )

    doctor_id = fields.Many2one(
        'res.users',
        string='Médecin',
        required=True,
        default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self._get_doctor_group_ids())],
        tracking=True,
    )

    consultation_date = fields.Datetime(
        string='Date de consultation',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )

    duration_minutes = fields.Integer(
        string='Durée (min)',
        default=30,
        help='Durée estimée ou effective de la consultation en minutes',
    )

    # =========================================================================
    # MOTIF & ANAMNÈSE
    # =========================================================================
    reason = fields.Text(
        string='Motif de la consultation',
        required=True,
        tracking=True,
    )

    symptoms = fields.Text(
        string='Symptômes rapportés',
        tracking=True,
    )

    anamnesis = fields.Text(
        string='Anamnèse',
        help='Interrogatoire médical, histoire de la maladie',
    )

    # =========================================================================
    # DIAGNOSTIC & TRAITEMENT
    # =========================================================================
    diagnosis = fields.Text(
        string='Diagnostic',
        tracking=True,
    )

    treatment_plan = fields.Text(
        string='Plan de traitement',
        help='Prescriptions, examens complémentaires, recommandations',
    )

    notes = fields.Text(
        string='Notes internes',
    )

    # =========================================================================
    # CONSTANTES VITALES
    # =========================================================================
    blood_pressure_systolic = fields.Integer(
        string='Tension systolique (mmHg)',
        help='Pression artérielle systolique en mmHg',
        tracking=True,
    )

    blood_pressure_diastolic = fields.Integer(
        string='Tension diastolique (mmHg)',
        help='Pression artérielle diastolique en mmHg',
        tracking=True,
    )

    blood_pressure_display = fields.Char(
        string='Tension artérielle',
        compute='_compute_blood_pressure_display',
    )

    heart_rate = fields.Integer(
        string='Fréquence cardiaque (bpm)',
        help='Pouls en battements par minute',
        tracking=True,
    )

    temperature = fields.Float(
        string='Température (°C)',
        help='Température corporelle en degrés Celsius',
        tracking=True,
    )

    respiratory_rate = fields.Integer(
        string='Fréquence respiratoire (resp/min)',
        help='Nombre de respirations par minute',
    )

    oxygen_saturation = fields.Integer(
        string='Saturation O₂ (%)',
        help='Saturation en oxygène en pourcentage (SpO₂)',
        tracking=True,
    )

    weight = fields.Float(
        string='Poids (kg)',
        help='Poids du patient en kilogrammes',
        tracking=True,
    )

    height = fields.Float(
        string='Taille (cm)',
        help='Taille du patient en centimètres',
    )

    bmi = fields.Float(
        string='IMC',
        compute='_compute_bmi',
        store=True,
        help='Indice de Masse Corporelle calculé à partir du poids et de la taille',
    )

    glycemia = fields.Float(
        string='Glycémie (g/L)',
        help='Glycémie capillaire en grammes par litre',
    )

    # =========================================================================
    # WORKFLOW
    # =========================================================================
    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('in_progress', 'En cours'),
            ('done', 'Terminé'),
            ('cancelled', 'Annulé'),
        ],
        string='Statut',
        required=True,
        default='draft',
        tracking=True,
    )

    # =========================================================================
    # LIENS DME (Dossier Médical Électronique)
    # =========================================================================
    medical_record_ids = fields.Many2many(
        'hospital.medical.record',
        'hospital_consultation_medical_record_rel',
        'consultation_id',
        'medical_record_id',
        string='Entrées DME créées',
        help='Entrées du dossier médical électronique créées depuis cette consultation',
        readonly=True,
        copy=False,
    )

    # =========================================================================
    # RÉFÉRENCES
    # =========================================================================
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

    display_name = fields.Char(
        string='Affichage',
        compute='_compute_display_name',
        store=True,
    )

    # =========================================================================
    # CHAMPS STATISTIQUES (affichage)
    # =========================================================================
    patient_age_at_consultation = fields.Integer(
        string='Âge du patient',
        compute='_compute_patient_info',
    )

    patient_sex = fields.Selection(
        related='patient_id.sex',
        string='Sexe',
        readonly=True,
    )

    # =========================================================================
    # MÉTHODES COMPUTED
    # =========================================================================
    @api.depends('consultation_id', 'patient_id', 'patient_id.display_name')
    def _compute_display_name(self):
        for record in self:
            if record.consultation_id and record.patient_id:
                record.display_name = '%s - %s' % (
                    record.consultation_id,
                    record.patient_id.display_name,
                )
            else:
                record.display_name = _('Nouvelle consultation')

    @api.depends('blood_pressure_systolic', 'blood_pressure_diastolic')
    def _compute_blood_pressure_display(self):
        for record in self:
            if record.blood_pressure_systolic and record.blood_pressure_diastolic:
                record.blood_pressure_display = '%d / %d mmHg' % (
                    record.blood_pressure_systolic,
                    record.blood_pressure_diastolic,
                )
            else:
                record.blood_pressure_display = ''

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for record in self:
            if record.weight and record.height and record.height > 0:
                height_m = record.height / 100.0
                record.bmi = round(record.weight / (height_m ** 2), 1)
            else:
                record.bmi = 0.0

    @api.depends('patient_id', 'consultation_date')
    def _compute_patient_info(self):
        for record in self:
            if record.patient_id and record.patient_id.birthdate and record.consultation_date:
                birth = record.patient_id.birthdate
                cons_date = record.consultation_date.date()
                age = cons_date.year - birth.year
                if (cons_date.month, cons_date.day) < (birth.month, birth.day):
                    age -= 1
                record.patient_age_at_consultation = age
            else:
                record.patient_age_at_consultation = 0

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('blood_pressure_systolic', 'blood_pressure_diastolic')
    def _check_blood_pressure(self):
        for record in self:
            if record.blood_pressure_systolic and record.blood_pressure_diastolic:
                if record.blood_pressure_systolic <= record.blood_pressure_diastolic:
                    raise ValidationError(_(
                        'La tension systolique doit être supérieure à la tension diastolique.'
                    ))

    @api.constrains('temperature')
    def _check_temperature(self):
        for record in self:
            if record.temperature and (record.temperature < 34.0 or record.temperature > 42.0):
                raise ValidationError(_(
                    'La température semble incohérente (%s °C). Veuillez vérifier.'
                ) % record.temperature)

    @api.constrains('oxygen_saturation')
    def _check_oxygen_saturation(self):
        for record in self:
            if record.oxygen_saturation and (record.oxygen_saturation < 50 or record.oxygen_saturation > 100):
                raise ValidationError(_(
                    'La saturation en oxygène doit être comprise entre 50 et 100%%.'
                ))

    @api.constrains('consultation_date')
    def _check_consultation_date(self):
        for record in self:
            if record.consultation_date and record.consultation_date > fields.Datetime.now():
                raise ValidationError(_(
                    'La date de consultation ne peut pas être dans le futur.'
                ))

    # =========================================================================
    # MÉTHODES DE CRÉATION/ÉCRITURE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('consultation_id'):
                vals['consultation_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.consultation'
                ) or _('Nouveau')
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            for record in self:
                if vals['state'] == 'done':
                    record._create_medical_record_entries()
                elif vals['state'] == 'cancelled':
                    record._remove_medical_record_entries()
        return res

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_start(self):
        """Démarrer la consultation"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    'Seules les consultations en brouillon peuvent être démarrées.'
                ))
            if not record.consultation_date:
                record.consultation_date = fields.Datetime.now()
        self.write({'state': 'in_progress'})

    def action_done(self):
        """Terminer la consultation"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_(
                    'Seules les consultations en cours peuvent être terminées.'
                ))
        self.write({'state': 'done'})

    def action_cancel(self):
        """Annuler la consultation"""
        for record in self:
            if record.state == 'done':
                raise ValidationError(_(
                    'Impossible d\'annuler une consultation déjà terminée.'
                ))
        self.write({'state': 'cancelled'})

    def action_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    # =========================================================================
    # CRÉATION AUTOMATIQUE DANS LE DME
    # =========================================================================
    def _create_medical_record_entries(self):
        """Crée les entrées dans le DME lors de la finalisation de la consultation"""
        MedicalRecord = self.env['hospital.medical.record']
        for record in self:
            existing = record.medical_record_ids
            new_records = self.env['hospital.medical.record']

            # 1. Créer une entrée pour le diagnostic
            if record.diagnosis:
                diagnosis_entry = MedicalRecord.create({
                    'patient_id': record.patient_id.id,
                    'record_type': 'diagnosis',
                    'pathology': record.diagnosis[:256],
                    'description': record.diagnosis,
                    'date_recorded': fields.Datetime.now(),
                    'date_onset': record.consultation_date.date() if record.consultation_date else False,
                    'doctor_id': record.doctor_id.id,
                    'severity': 'medium',
                })
                new_records += diagnosis_entry

            # 2. Créer une entrée pour le plan de traitement
            if record.treatment_plan:
                treatment_entry = MedicalRecord.create({
                    'patient_id': record.patient_id.id,
                    'record_type': 'treatment',
                    'pathology': 'Plan de traitement',
                    'description': record.treatment_plan,
                    'date_recorded': fields.Datetime.now(),
                    'date_onset': record.consultation_date.date() if record.consultation_date else False,
                    'doctor_id': record.doctor_id.id,
                    'severity': 'medium',
                })
                new_records += treatment_entry

            # 3. Créer une entrée récapitulative
            summary_parts = []
            if record.reason:
                summary_parts.append('Motif: %s' % record.reason)
            if record.symptoms:
                summary_parts.append('Symptômes: %s' % record.symptoms)

            if summary_parts:
                summary_entry = MedicalRecord.create({
                    'patient_id': record.patient_id.id,
                    'record_type': 'other',
                    'pathology': 'Compte-rendu de consultation',
                    'description': '\n'.join(summary_parts),
                    'date_recorded': fields.Datetime.now(),
                    'date_onset': record.consultation_date.date() if record.consultation_date else False,
                    'doctor_id': record.doctor_id.id,
                    'severity': 'low',
                })
                new_records += summary_entry

            # Lier les nouvelles entrées à la consultation
            if new_records:
                record.medical_record_ids = [(4, entry.id) for entry in new_records]

    def _remove_medical_record_entries(self):
        """Supprime les entrées DME créées lorsque la consultation est annulée"""
        for record in self:
            if record.medical_record_ids:
                record.medical_record_ids.unlink()
                record.medical_record_ids = [(5, 0, 0)]

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_open_patient(self):
        """Ouvre la fiche du patient"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Patient'),
            'res_model': 'hospital.patient',
            'view_mode': 'form',
            'res_id': self.patient_id.id,
        }

    def action_open_medical_record(self):
        """Ouvre le DME du patient filtré par cette consultation"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dossier Médical'),
            'res_model': 'hospital.medical.record',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.medical_record_ids.ids)] if self.medical_record_ids else [('id', '=', False)],
        }

    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    @api.model
    def _get_doctor_group_ids(self):
        """Retourne les IDs des groupes ayant le droit de consulter"""
        DoctorGroup = self.env.ref('care_center_base.group_hospital_doctor', raise_if_not_found=False)
        AdminGroup = self.env.ref('care_center_base.group_hospital_admin', raise_if_not_found=False)
        ManagerGroup = self.env.ref('care_center_base.group_hospital_manager', raise_if_not_found=False)

        group_ids = []
        if DoctorGroup:
            group_ids.append(DoctorGroup.id)
        if AdminGroup:
            group_ids.append(AdminGroup.id)
        if ManagerGroup:
            group_ids.append(ManagerGroup.id)
        return group_ids
