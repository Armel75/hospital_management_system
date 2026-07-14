# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from datetime import timedelta


class HospitalAppointment(models.Model):
    """Rendez-vous médical entre un patient et un médecin"""

    _name = 'hospital.appointment'
    _description = 'Rendez-vous Médical'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'appointment_date DESC, id DESC'

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    appointment_id = fields.Char(
        string='N° Rendez-vous',
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
        domain=lambda self: [('groups_id', 'in', self._get_doctor_group_ids())],
        tracking=True,
    )

    appointment_date = fields.Datetime(
        string='Date du rendez-vous',
        required=True,
        tracking=True,
    )

    end_datetime = fields.Datetime(
        string='Fin',
        compute='_compute_end_datetime',
        store=True,
        readonly=True,
    )

    duration_minutes = fields.Integer(
        string='Durée (minutes)',
        required=True,
        default=30,
        tracking=True,
    )

    # =========================================================================
    # TYPE & MOTIF
    # =========================================================================
    appointment_type = fields.Selection(
        selection=[
            ('first_visit', 'Première visite'),
            ('follow_up', 'Consultation de suivi'),
            ('emergency', 'Urgence'),
            ('checkup', 'Examen de routine'),
            ('vaccination', 'Vaccination'),
            ('results', 'Remise de résultats'),
            ('other', 'Autre'),
        ],
        string='Type de rendez-vous',
        required=True,
        default='first_visit',
        tracking=True,
    )

    reason = fields.Text(
        string='Motif du rendez-vous',
        required=True,
        tracking=True,
    )

    notes = fields.Text(
        string='Notes',
    )

    contact_phone = fields.Char(
        string='Téléphone de contact',
        help='Numéro où joindre le patient pour ce rendez-vous',
    )

    # =========================================================================
    # WORKFLOW
    # =========================================================================
    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('confirmed', 'Confirmé'),
            ('in_progress', 'En cours'),
            ('done', 'Terminé'),
            ('cancelled', 'Annulé'),
            ('noshow', 'Non honoré'),
        ],
        string='Statut',
        required=True,
        default='draft',
        tracking=True,
    )

    # =========================================================================
    # LIEN VERS LA CONSULTATION
    # =========================================================================
    consultation_id = fields.Many2one(
        'hospital.consultation',
        string='Consultation générée',
        readonly=True,
        copy=False,
        help='Consultation créée à partir de ce rendez-vous',
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
    # MÉTHODES COMPUTED
    # =========================================================================
    @api.depends('appointment_id', 'patient_id', 'patient_id.display_name')
    def _compute_display_name(self):
        for record in self:
            if record.appointment_id and record.patient_id:
                record.display_name = '%s - %s' % (
                    record.appointment_id,
                    record.patient_id.display_name,
                )
            else:
                record.display_name = _('Nouveau rendez-vous')

    @api.depends('appointment_date', 'duration_minutes')
    def _compute_end_datetime(self):
        for record in self:
            if record.appointment_date and record.duration_minutes:
                record.end_datetime = record.appointment_date + timedelta(
                    minutes=record.duration_minutes
                )
            else:
                record.end_datetime = False

    # =========================================================================
    # API CONSTRAINS
    # =========================================================================
    @api.constrains('appointment_date', 'duration_minutes')
    def _check_appointment_date(self):
        for record in self:
            if record.appointment_date and record.appointment_date < fields.Datetime.now():
                raise ValidationError(_(
                    'La date du rendez-vous ne peut pas être dans le passé.'
                ))

    @api.constrains('duration_minutes')
    def _check_duration(self):
        for record in self:
            if record.duration_minutes and record.duration_minutes < 5:
                raise ValidationError(_(
                    'La durée minimale d\'un rendez-vous est de 5 minutes.'
                ))
            if record.duration_minutes and record.duration_minutes > 480:
                raise ValidationError(_(
                    'La durée maximale d\'un rendez-vous est de 480 minutes (8 heures).'
                ))

    @api.constrains('appointment_date', 'duration_minutes', 'doctor_id')
    def _check_doctor_availability(self):
        """Vérifie que le médecin n'a pas déjà un rendez-vous qui se chevauche"""
        for record in self:
            if not record.appointment_date or not record.duration_minutes or not record.doctor_id:
                continue

            start = record.appointment_date
            end = start + timedelta(minutes=record.duration_minutes)

            # Chercher les conflits
            domain = [
                ('doctor_id', '=', record.doctor_id.id),
                ('id', '!=', record.id),
                ('state', 'not in', ('cancelled', 'noshow')),
                ('appointment_date', '<', end),
                ('end_datetime', '>', start),
            ]

            conflict = self.search_count(domain)
            if conflict:
                raise ValidationError(_(
                    'Le médecin %s a déjà un rendez-vous prévu sur ce créneau '
                    '(de %s à %s). Veuillez choisir un autre horaire.'
                ) % (
                    record.doctor_id.display_name,
                    start.strftime('%H:%M'),
                    end.strftime('%H:%M'),
                ))

    # =========================================================================
    # MÉTHODES DE CRÉATION/ÉCRITURE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('appointment_id'):
                vals['appointment_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.appointment'
                ) or _('Nouveau')
        return super().create(vals_list)

    def write(self, vals):
        # Si le rendez-vous passe en "En cours", générer automatiquement
        # la consultation si elle n'existe pas encore
        res = super().write(vals)
        if vals.get('state') == 'in_progress':
            for record in self:
                if not record.consultation_id:
                    record._generate_consultation()
        return res

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_confirm(self):
        """Confirmer le rendez-vous"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_(
                    'Seuls les rendez-vous en brouillon peuvent être confirmés.'
                ))
        self.write({'state': 'confirmed'})

    def action_start(self):
        """Démarrer le rendez-vous (génère la consultation)"""
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_(
                    'Seuls les rendez-vous confirmés peuvent être démarrés.'
                ))
        # La consultation sera créée automatiquement via write()
        self.write({'state': 'in_progress'})

    def action_done(self):
        """Terminer le rendez-vous"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError(_(
                    'Seuls les rendez-vous en cours peuvent être terminés.'
                ))
        self.write({'state': 'done'})

    def action_cancel(self):
        """Annuler le rendez-vous"""
        for record in self:
            if record.state == 'done':
                raise ValidationError(_(
                    'Impossible d\'annuler un rendez-vous déjà terminé.'
                ))
        self.write({'state': 'cancelled'})

    def action_noshow(self):
        """Marquer le rendez-vous comme non honoré"""
        for record in self:
            if record.state not in ('confirmed', 'in_progress'):
                raise ValidationError(_(
                    'Seuls les rendez-vous confirmés ou en cours peuvent être '
                    'marqués comme non honorés.'
                ))
        self.write({'state': 'noshow'})

    def action_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    # =========================================================================
    # GÉNÉRATION DE LA CONSULTATION
    # =========================================================================
    def _generate_consultation(self):
        """Crée une consultation liée à ce rendez-vous avec pré-remplissage"""
        Consultation = self.env['hospital.consultation']
        for record in self:
            consultation = Consultation.create({
                'patient_id': record.patient_id.id,
                'doctor_id': record.doctor_id.id,
                'consultation_date': record.appointment_date,
                'reason': record.reason,
                'notes': record.notes,
            })
            record.consultation_id = consultation

    def action_open_consultation(self):
        """Ouvre la consultation liée si elle existe"""
        self.ensure_one()
        if not self.consultation_id:
            return self._generate_consultation() and {
                'type': 'ir.actions.act_window',
                'name': _('Consultation'),
                'res_model': 'hospital.consultation',
                'view_mode': 'form',
                'res_id': self.consultation_id.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Consultation'),
            'res_model': 'hospital.consultation',
            'view_mode': 'form',
            'res_id': self.consultation_id.id,
        }

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

    @api.model
    def get_today_appointments(self):
        """Retourne les rendez-vous du jour pour le tableau de bord"""
        today = fields.Datetime.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        return self.search([
            ('appointment_date', '>=', start_of_day),
            ('appointment_date', '<=', end_of_day),
        ])
