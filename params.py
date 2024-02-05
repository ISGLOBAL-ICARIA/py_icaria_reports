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
    'sae_other_action', 'sae_con_drug_1', 'sae_con_subs_1', 'sae_interviewer_id', 'sae_complete', 'sae_date',
    'sae_icd_10'
]

ALERT_LOGIC_FIELDS_COHORTS = [
    'record_id','ch_his_fever','ch_his_sick','ch_his_net','ch_his_date','ch_rdt_malaria','ch_rdt_malaria_result',
    'ch_rdt_antimalarial_1','ch_rdt_no_antimalarial_desc','ch_rdt_antimalarial_name_1','ch_rdt_antimalarial_ind_1',
    'ch_rdt_antimalarial_dose_1','ch_rdt_antimalarial_unit_1','ch_rdt_antimalarial_freq_1','ch_rdt_antimalarial_route_1',
    'ch_rdt_antimalarial_start_1','ch_rdt_antimalarial_ongoing_1','ch_rdt_antimalarial_stop_1','ch_rdt_antimalarial_2',
    'ch_rdt_antimalarial_name_2','ch_rdt_antimalarial_ind_2',
    'ch_rdt_antimalarial_dose_2','ch_rdt_antimalarial_unit_2','rdt_antimalarial_freq_2','rdt_antimalarial_route_2',
    'ch_rdt_antimalarial_start_2','ch_rdt_antimalarial_ongoing_2','ch_rdt_antimalarial_stop_2',
    'hemocue','hemocue_result','hemocue_result_lower','hemocue_result_haematinics_1','hemocue_haematinics_name_1',
    'hemocue_haematinics_ind_1','hemocue_haematinics_dose_1','hemocue_haematinics_unit_1','hemocue_haematinics_freq_1',
    'hemocue_haematinics_route_1','hemocue_haematinics_start_1','hemocue_haematinics_ongoing_1','hemocue_haematinics_stop_1',
    'hemocue_haematinics_2','hemocue_haematinics_name_2','hemocue_haematinics_dose_2','hemocue_haematinics_ind_2',
    'hemocue_haematinics_unit_2','hemocue_haematinics_freq_2','hemocue_haematinics_route_2','hemocue_haematinics_start_2',
    'hemocue_haematinics_ongoing_2','hemocue_haematinics_stop_2','blood_spots','blood_spots_sample_1',
    'blood_spots_sample_1_id','blood_spots_sample_2','blood_spots_sample_2_id','blood_smear','blood_smear_malaria',
    'blood_smear_malaria_treatment','bs_antimalarial_name_1','bs_antimalarial_ind_1','bs_antimalarial_dose_1',
    'bs_antimalarial_unit_1','bs_antimalarial_freq_1','bs_antimalarial_route_1','bs_antimalarial_start_1','bs_antimalarial_ongoing_1',
    'bs_antimalarial_stop_1','bs_antimalarial_2','bs_antimalarial_name_2','bs_antimalarial_ind_2','bs_antimalarial_dose_2',
    'bs_antimalarial_unit_2','bs_antimalarial_freq_2','bs_antimalarial_route_2','bs_antimalarial_start_2','bs_antimalarial_ongoing_2',
    'bs_antimalarial_stop_2','blood_smear_other','blood_smear_other_diagnoses','ch_rdt_date'
]
ALERT_LOGIC_FIELDS_SAE_medrecords = [
    'record_id', 'sae_report_type',  'sae_hosp_admin_date', 'sae_outcome', 'sae_interviewer_id','sae_date','sae_time',
    'sae_complete','sae_rel_doc_1','sae_rel_doc_2','sae_rel_doc_3','sae_rel_doc_4','sae_rel_doc_5','sae_rel_doc_6',
    'sae_rel_doc_7','sae_rel_doc_8','sae_rel_doc_9','sae_rel_doc_10','sae_rel_doc_11','sae_rel_doc_12','sae_rel_doc_13',
    'sae_rel_doc_14','sae_rel_doc_15','sae_rel_doc_16','sae_rel_doc_17','sae_rel_doc_18','sae_rel_doc_19',
    'sae_rel_doc_20','sae_rel_doc_21','sae_rel_doc_22','sae_rel_doc_23','sae_rel_doc_24','sae_rel_doc_25'
]

sae_outcome_dict = {
1:'Recovered/resolved',
2:'Recovered/resolved with sequelae',
3:'Not yet recovered/not resolved',
4:'Ongoing',
5:'Deterioration',
6:'Permanent damage',
7:'Death',
8:'Unknown',
}
sae_complete_dict = {
    0:'Incomplete',
    1:'Unverified',
    2:'Complete',
}

LOGIC_FIELDS_INT_ANTIGENS = [
    'child_dob','int_vacc_bcg', 'int_vacc_bcg_date', 'int_vacc_opv1', 'int_vacc_opv1_date','int_vacc_opv2', 'int_vacc_opv2_date',
    'int_vacc_opv3', 'int_vacc_opv3_date', 'int_vacc_ipv', 'int_vacc_ipv_date','int_vacc_ipv2', 'int_vacc_ipv2_date',
    'int_vacc_penta1', 'int_vacc_penta1_date', 'int_vacc_penta2','int_vacc_penta2_date', 'int_vacc_penta3',
    'int_vacc_penta3_date', 'int_vacc_pneumo1', 'int_vacc_pneumo1_date','int_vacc_pneumo2', 'int_vacc_pneumo2_date',
    'int_vacc_pneumo3', 'int_vacc_pneumo3_date', 'int_vacc_rota1','int_vacc_rota1_date', 'int_vacc_rota2',
    'int_vacc_rota2_date','int_vacc_mrv1','int_vacc_mrv1_date','int_vacc_mrv2','int_vacc_mrv2_date',
    'int_vacc_yellow_fever', 'int_vacc_yellow_fever_date', 'int_vacc_vit_a','int_vacc_vit_a_date','int_vacc_deworm',
    'int_vacc_deworm_date', 'int_date', 'household_follow_up_complete','death_complete','migration_complete',
    'withdrawal_complete', 'reachable_status', 'eligible', 'screening_complete', 'study_number','his_vacc_bcg'
]

epi_visits_dict = {
    'epipenta1_v0_recru_arm_1': ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date'],
    'epipenta2_v1_iptis_arm_1':  ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date',
                                  'int_vacc_penta2_date','int_vacc_opv2_date','int_vacc_pneumo2_date','int_vacc_rota2_date'],
    'epipenta3_v2_iptis_arm_1': ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date',
                                 'int_vacc_penta2_date','int_vacc_opv2_date','int_vacc_pneumo2_date','int_vacc_rota2_date',
                                 'int_vacc_penta3_date','int_vacc_opv3_date','int_vacc_pneumo3_date','int_vacc_ipv_date'],
    'epivita_v3_iptisp3_arm_1': ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date',
                                 'int_vacc_penta2_date','int_vacc_opv2_date','int_vacc_pneumo2_date','int_vacc_rota2_date',
                                 'int_vacc_penta3_date','int_vacc_opv3_date','int_vacc_pneumo3_date','int_vacc_ipv_date','int_vacc_vit_a_date'],
    'epimvr1_v4_iptisp4_arm_1': ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date',
                                 'int_vacc_penta2_date','int_vacc_opv2_date','int_vacc_pneumo2_date','int_vacc_rota2_date',
                                 'int_vacc_penta3_date','int_vacc_opv3_date','int_vacc_pneumo3_date','int_vacc_ipv_date','int_vacc_vit_a_date',
                                 'int_vacc_ipv2_date','int_vacc_yellow_fever_date','int_vacc_mrv1_date'],
    'epivita_v5_iptisp5_arm_1': ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date',
                                 'int_vacc_penta2_date','int_vacc_opv2_date','int_vacc_pneumo2_date','int_vacc_rota2_date',
                                 'int_vacc_penta3_date','int_vacc_opv3_date','int_vacc_pneumo3_date','int_vacc_ipv_date','int_vacc_vit_a_date',
                                 'int_vacc_ipv2_date','int_vacc_yellow_fever_date','int_vacc_mrv1_date','int_vacc_deworm_date'],
    'epimvr2_v6_iptisp6_arm_1': ['int_vacc_bcg_date','int_vacc_penta1_date','int_vacc_opv1_date','int_vacc_pneumo1_date','int_vacc_rota1_date',
                                 'int_vacc_penta2_date','int_vacc_opv2_date','int_vacc_pneumo2_date','int_vacc_rota2_date',
                                 'int_vacc_penta3_date','int_vacc_opv3_date','int_vacc_pneumo3_date','int_vacc_ipv_date','int_vacc_vit_a_date',
                                 'int_vacc_ipv2_date','int_vacc_yellow_fever_date','int_vacc_mrv1_date','int_vacc_deworm_date',
                                 'int_vacc_mrv2_date'],
}

epi_visits = ['epipenta1_v0_recru_arm_1', 'epipenta2_v1_iptis_arm_1', 'epipenta3_v2_iptis_arm_1',
             'epivita_v3_iptisp3_arm_1',
             'epimvr1_v4_iptisp4_arm_1', 'epivita_v5_iptisp5_arm_1', 'epimvr2_v6_iptisp6_arm_1']
SAE_personnel_ids = ['ssheriff','agbla','ajalloh']

physicians_worksheet = 'Reporting_updates'
vacc_coh_worksheet = 'COH participants'
vacc_worksheet = 'non-COH participants'



SPR_BASELINE_FIELDS = [
    'study_number','district','hf_bombali','hf_port_loko','hf_tonkolili','screening_age_months','sex','weight','height_available',
    'height','muac_available','muac','ethnicity','other_ethnicity','antimalarials','antimalarials_48h','ctx',
    'ctx_duration','art','bednet','temperature','fever_new','fever','fever_episodes','fever_episodes_2',
    'last_sp_dose_available','last_sp_dose'
]
