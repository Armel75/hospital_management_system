# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
import re


class HospitalPatient(models.Model):
    """Fiche patient du système de gestion hospitalière"""

    _name = 'hospital.patient'
    _description = 'Patient Hospitalier'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _rec_name = 'display_name'
    _order = 'create_date DESC'

    # =========================================================================
    # IDENTITÉ & ÉTAT CIVIL
    # =========================================================================
    patient_id = fields.Char(
        string='N° Patient',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('Nouveau'),
    )

    title = fields.Many2one(
        'res.partner.title',
        string='Civilité',
        required=True,
        tracking=True,
    )

    firstname = fields.Char(
        string='Prénom',
        required=True,
        tracking=True,
    )

    lastname = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
    )

    display_name = fields.Char(
        string='Nom complet',
        compute='_compute_display_name',
        store=True,
        index=True,
    )

    birthdate = fields.Date(
        string='Date de naissance',
        required=True,
        tracking=True,
    )

    age = fields.Integer(
        string='Âge',
        compute='_compute_age',
        store=True,
    )

    age_display = fields.Char(
        string='Âge (affichage)',
        compute='_compute_age_display',
    )

    sex = fields.Selection(
        selection=[
            ('male', 'Masculin'),
            ('female', 'Féminin'),
        ],
        string='Sexe',
        required=True,
        tracking=True,
    )

    # =========================================================================
    # IDENTIFIANTS ADMINISTRATIFS
    # =========================================================================
    nss = fields.Char(
        string='N° Sécurité Sociale',
        required=True,
        copy=False,
        tracking=True,
    )

    nss_key = fields.Char(
        string='Clé NSS',
        compute='_compute_nss_key',
    )

    nss_valid = fields.Boolean(
        string='NSS Valide',
        compute='_compute_nss_valid',
        store=True,
    )

    # =========================================================================
    # COORDONNÉES
    # =========================================================================
    mobile = fields.Char(
        string='Téléphone mobile',
        required=True,
        tracking=True,
    )

    phone = fields.Char(
        string='Téléphone fixe',
        tracking=True,
    )

    email = fields.Char(
        string='Email',
        tracking=True,
    )

    street = fields.Char(
        string='Rue',
    )

    street2 = fields.Char(
        string='Rue (suite)',
    )

    zip = fields.Char(
        string='Code postal',
    )

    city = fields.Char(
        string='Ville',
    )

    country_id = fields.Many2one(
        'res.country',
        string='Pays',
    )

    # =========================================================================
    # INFORMATIONS MÉDICALES DE BASE
    # =========================================================================
    blood_group = fields.Selection(
        selection=[
            ('a+', 'A+'),
            ('a-', 'A-'),
            ('b+', 'B+'),
            ('b-', 'B-'),
            ('ab+', 'AB+'),
            ('ab-', 'AB-'),
            ('o+', 'O+'),
            ('o-', 'O-'),
        ],
        string='Groupe sanguin',
        tracking=True,
    )

    rhesus_factor = fields.Selection(
        selection=[
            ('positive', 'Positif (+)'),
            ('negative', 'Négatif (-)'),
        ],
        string='Facteur Rhésus',
        tracking=True,
    )

    weight = fields.Float(
        string='Poids (kg)',
        help='Poids actuel du patient en kilogrammes',
    )

    height = fields.Float(
        string='Taille (cm)',
        help='Taille du patient en centimètres',
    )

    bmi = fields.Float(
        string='IMC',
        compute='_compute_bmi',
        store=True,
        help='Indice de Masse Corporelle',
    )

    profession = fields.Char(
        string='Profession',
    )

    marital_status = fields.Selection(
        selection=[
            ('single', 'Célibataire'),
            ('married', 'Marié(e)'),
            ('divorced', 'Divorcé(e)'),
            ('widowed', 'Veuf/Veuve'),
        ],
        string='Situation familiale',
    )

    # =========================================================================
    # RELATIONS
    # =========================================================================
    medical_record_ids = fields.One2many(
        'hospital.medical.record',
        'patient_id',
        string='Dossier médical',
    )

    # Les champs consultation_ids et appointment_ids seront ajoutés
    # par les modules care_center_consultation et care_center_appointment
    # via un champ Related ou un héritage de modèle

    # =========================================================================
    # COMPTES & SOCIÉTÉ
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

    notes = fields.Text(
        string='Notes internes',
    )

    # =========================================================================
    # CHAMPS STATISTIQUES
    # =========================================================================
    total_consultations = fields.Integer(
        string='Nombre de consultations',
        compute='_compute_statistics',
        store=True,
    )

    last_consultation_date = fields.Date(
        string='Dernière consultation',
        compute='_compute_statistics',
        store=True,
    )

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends('firstname', 'lastname', 'title')
    def _compute_display_name(self):
        for record in self:
            parts = []
            if record.title:
                parts.append(record.title.name)
            if record.firstname:
                parts.append(record.firstname)
            if record.lastname:
                parts.append(record.lastname.upper())
            record.display_name = ' '.join(parts) if parts else _('Patient sans nom')

    @api.depends('birthdate')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.birthdate:
                age = today.year - record.birthdate.year
                # Ajustement si l'anniversaire n'est pas encore passé
                if (today.month, today.day) < (record.birthdate.month, record.birthdate.day):
                    age -= 1
                record.age = age
            else:
                record.age = 0

    @api.depends('age')
    def _compute_age_display(self):
        for record in self:
            if record.age:
                record.age_display = _('%d ans') % record.age
            else:
                record.age_display = _('Non renseigné')

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for record in self:
            if record.weight and record.height and record.height > 0:
                height_m = record.height / 100.0
                record.bmi = round(record.weight / (height_m ** 2), 1)
            else:
                record.bmi = 0.0

    @api.depends('nss')
    def _compute_nss_key(self):
        for record in self:
            record.nss_key = record._get_nss_key()

    @api.depends('nss')
    def _compute_nss_valid(self):
        for record in self:
            record.nss_valid = record._validate_nss()

    @api.depends()
    def _compute_statistics(self):
        for record in self:
            record.total_consultations = 0
            record.last_consultation_date = False

    # =========================================================================
    # API CONSTRAINTS
    # =========================================================================
    @api.constrains('birthdate')
    def _check_birthdate(self):
        for record in self:
            if record.birthdate and record.birthdate > date.today():
                raise ValidationError(
                    _('La date de naissance ne peut pas être dans le futur.')
                )
            if record.birthdate:
                age = date.today().year - record.birthdate.year
                if age > 120:
                    raise ValidationError(
                        _('L\'âge calculé est incohérent. Vérifiez la date de naissance.')
                    )

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.email):
                    raise ValidationError(
                        _("L'adresse email '%s' n'est pas valide.") % record.email
                    )

    @api.constrains('mobile')
    def _check_phone(self):
        for record in self:
            if record.mobile:
                # Format français : 0X XX XX XX XX ou +33X XX XX XX XX
                cleaned = record.mobile.replace(' ', '').replace('.', '').replace('-', '')
                if not re.match(r'^(?:\+33|0)[1-9]\d{8}$', cleaned):
                    raise ValidationError(
                        _("Le numéro de téléphone '%s' n'est pas valide. "
                          "Format attendu : 0612345678 ou +33612345678")
                        % record.mobile
                    )

    @api.constrains('nss')
    def _check_nss(self):
        for record in self:
            if not record._validate_nss():
                raise ValidationError(
                    _("Le N° de Sécurité Sociale '%s' n'est pas valide. "
                      "Le format attendu est : 1 99 99 99 999 999 99")
                    % record.nss
                )
            # Vérifier l'unicité du NSS
            duplicate = self.search([
                ('nss', '=', record.nss),
                ('id', '!=', record.id),
                ('company_id', '=', record.company_id.id),
            ])
            if duplicate:
                raise ValidationError(
                    _("Le N° de Sécurité Sociale '%s' est déjà attribué à un autre patient "
                      "dans cet établissement.") % record.nss
                )

    # =========================================================================
    # VALIDATION NSS (France)
    # =========================================================================
    def _validate_nss(self):
        """Valide un NSS français selon la règle de la clé de contrôle"""
        self.ensure_one()
        if not self.nss:
            return False

        # Nettoyer le NSS : enlever espaces et tirets
        nss = self.nss.replace(' ', '').replace('-', '').replace('.', '')

        # Longueur doit être 15 chiffres (13 + clé à 2 chiffres)
        if not nss.isdigit() or len(nss) != 15:
            return False

        # Extraction des 13 premiers chiffres et de la clé
        nss_base = int(nss[:13])
        nss_key = int(nss[13:])

        # Calcul de la clé : 97 - (valeur_mod_97)
        calculated_key = 97 - (nss_base % 97)

        return calculated_key == nss_key

    def _get_nss_key(self):
        """Calcule et retourne la clé de contrôle du NSS"""
        self.ensure_one()
        if not self.nss:
            return ''

        nss = self.nss.replace(' ', '').replace('-', '').replace('.', '')
        if not nss.isdigit() or len(nss) < 13:
            return ''

        nss_base = int(nss[:13])
        calculated_key = 97 - (nss_base % 97)
        return str(calculated_key).zfill(2)

    # =========================================================================
    # FONCTIONS DE CRÉATION/ÉCRITURE
    # =========================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('patient_id'):
                vals['patient_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.patient'
                ) or _('Nouveau')
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    def unlink(self):
        # Empêcher la suppression des patients ayant des dossiers médicaux
        for record in self:
            if record.medical_record_ids:
                raise ValidationError(
                    _("Impossible de supprimer le patient '%s' car il possède "
                      "un dossier médical associé.") % record.display_name
                )
        return super().unlink()

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_open_medical_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dossier médical'),
            'res_model': 'hospital.medical.record',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {
                'default_patient_id': self.id,
            },
        }
