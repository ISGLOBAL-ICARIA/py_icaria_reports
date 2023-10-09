TRIAL_ALL_EVENT_NAMES = {
    'epipenta1_v0_recru_arm_1': 'PENTA1',
    'epipenta2_v1_iptis_arm_1': 'PENTA2',
    'epipenta3_v2_iptis_arm_1': 'PENTA3',
    'epivita_v3_iptisp3_arm_1': 'VITA-6M',
    'epimvr1_v4_iptisp4_arm_1': 'MRV1',
    'epivita_v5_iptisp5_arm_1': 'VITA-12M',
    'epimvr2_v6_iptisp6_arm_1': 'MRV2',
    'hhafter_1st_dose_o_arm_1': 'HHA1D',
    'cohort_after_mrv_2_arm_1': 'COHAMRV2',
    'after_1_month_from_arm_1': 'AFTERPENTA1',
    'after_1_month_from_arm_1b': 'AFTERVITA6M',
    'after_1_month_from_arm_1c': 'AFTERMRV1',
    'after_1_month_from_arm_1d': 'AFTERVITA12M',
    'after_1_month_from_arm_1e': 'AFTERMRV2',
    'adverse_events_arm_1': 'AE',
    'out_of_schedule_arm_1': 'OUTSCH'
}

HF_DICT = {
    'HF01': ['HF01.01', 'HF01.02'],
    'HF02': ['HF02.01', 'HF02.02'],
    'HF03': ['HF03'],
    'HF04': ['HF04'],
    'HF05': ['HF05.01', 'HF05.02'],
    'HF06': ['HF06'],
    'HF08': ['HF08.01', 'HF08.02', 'HF08.03', 'HF08.04'],
    'HF10': ['HF10'],
    'HF11': ['HF11.01', 'HF11.02'],
    'HF12': ['HF12.01', 'HF12.02'],
    'HF13': ['HF13'],
    'HF15': ['HF15'],
    'HF16': ['HF16.01', 'HF16.02', 'HF16.03', 'HF16.04'],
    'HF17': ['HF17']
    }

HF_NAMES_DICT = {
    'HF01': 'Lungi Under Fives CHP',
    'HF02': 'Lunsar CHC',
    'HF03': 'Mahera CHC',
    'HF04': 'Masiaka CHC',
    'HF05': 'Port Loko U5 CHP',
    'HF06': 'Rogbere Junction CHC',
    'HF08': 'Magburaka Under Fives Clinic',
    'HF10': 'Matotoka CHC',
    'HF11': 'Loreto Clinic',
    'HF12': 'Red Cross ¨(Makeni City) CHP',
    'HF13': 'Stocco CHP',
    'HF15': 'Makama CHP',
    'HF16': 'Makeni Government Hospital',
    'HF17': 'Masuba CHC',
    }


doses = {1:['epipenta1_v0_recru_arm_1'],2:['epimvr1_v4_iptisp4_arm_1','epivita_v5_iptisp5_arm_1'],3:['epimvr2_v6_iptisp6_arm_1']}

# DATA DICTIONARY FIELDS USED BY THE DIFFERENT ALERTS - IMPROVE PERFORMANCE OF API CALLS
ALERT_LOGIC_FIELDS_old = ['record_id', 'child_dob', 'screening_date', 'community', 'int_azi','int_next_visit', 'int_date',
                      'int_sp', 'intervention_complete', 'hh_child_seen','hh_why_not_child_seen','hh_date','study_number',
                      'call_caretaker','reachable_status','household_follow_up_complete', 'a1m_date', 'comp_date',
                      'phone_success','child_birth_weight_known','phone_success','fu_type','int_random_letter',
                      'death_reported_date', 'ae_date','sae_awareness_date','ms_date','unsch_date','mig_date','comp_date',
                      'ch_his_date','phone_child_status','child_fu_status']

recruitment_rate = 520 # monthly 460 - 650
total_recruited = 16990
total_to_recruit = 20560

ALERT_LOGIC_FIELDS = [
    'record_id','child_dob','study_number','int_azi','int_date','int_next_visit','int_sp','intervention_complete','child_fu_status'
]
ALERT_LOGIC_FIELDS_SAE_physicians = [
    'record_id', 'sae_report_type', 'sae_med_terms', 'sae_rel_doc_1', 'sae_onset',
    'sae_death', 'sae_hosp', 'sae_threat', 'sae_disability', 'sae_other', 'sae_other_criteria',
    'sae_relationship', 'sae_severity', 'sae_expectedness', 'sae_con_med_rel', 'sae_outcome', 'sae_action',
    'sae_other_action', 'sae_con_drug_1', 'sae_con_subs_1', 'sae_interviewer_id', 'sae_complete', 'sae_date'
]

SAE_personnel_ids = ['ssheriff','agbla','ajalloh']

physicians_worksheet = 'Reporting_updates'