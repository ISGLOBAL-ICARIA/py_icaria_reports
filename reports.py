from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from functools import reduce
import pandas as pd
import numpy as np
import redcap
import params
import tokens
import gspread
from gspread_dataframe import set_with_dataframe

def all_projects_together():
    main_df = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format='df', fields=params.ALERT_LOGIC_FIELDS)

        if main_df.empty:
            main_df = df
        else:
            main_df = pd.concat([main_df,df])
    return main_df

def get_one_project(HF=False):
    main_df = pd.DataFrame()

    for project_name in params.HF_DICT[HF]:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format='df', fields=params.ALERT_LOGIC_FIELDS)

        if main_df.empty:
            main_df = df
        else:
            main_df = pd.concat([main_df,df])
    return main_df

def doses_per_month(df, year=2023, excel=False):
    print("DOSES PER MONTH\n")
    df = df[(df['int_azi']==1)&(df['intervention_complete']==2)]
    df['int_year'] = pd.DatetimeIndex(df['int_date']).year
    df['int_month'] = pd.DatetimeIndex(df['int_date']).month

    if year:
        df = df[df['int_year']==year]

    print(df.groupby(['int_month','redcap_event_name'])['int_azi'].count())

    if excel:
        df.groupby(['int_month','redcap_event_name'])['int_azi'].count().to_excel(excel)


def last_dose_per_record(df):
    df = df[df['int_azi'] == 1].sort_values('int_azi')
    dfres = df.reset_index()[['record_id','redcap_event_name','int_date']]
    last_doses = df.groupby('record_id')['int_date'].max().sort_index().reset_index()
    last_doses_join = pd.merge(dfres,last_doses,on=['record_id','int_date']).sort_values('record_id')
    return last_doses_join

def retrieve_dob(df,df_list_records):
    df = df.reset_index()
    result = pd.merge(df_list_records,df[(df['record_id'].isin(df_list_records['record_id'].unique()))&(df['child_dob'].notnull())][['record_id','child_dob','child_fu_status']],on='record_id')
    return result

def date_dosis_projections(df):
    df = df[df['int_azi'] == 1]
    print("DATA DOSES PROJECTIONS")
    rare_cases = df[df['child_fu_status'].apply(lambda x: ' ' == str(x))]
    rare_cases.to_excel(tokens.path_reports+'child_fu_status_raros.xlsx')

    ##Eliminate Finished participants
    df = df[df['child_fu_status'].apply(lambda x: 'COMPLETED' not in str(x) and 'Death' not in str(x) and 'Migrated' not in str(x) and 'withdrawn' not in str(x) and 'Withdrawn' not in str(x) and 'UNREACHABLE' not in str(x))]

    last_doses = last_dose_per_record(df)
    last_doses = retrieve_dob(df,last_doses)
    last_doses = last_doses[last_doses['redcap_event_name']!='epimvr2_v6_iptisp6_arm_1']

    first_doses = last_doses[last_doses['redcap_event_name'].isin(params.doses[1])] # 6w visit
    second_doses = last_doses[last_doses['redcap_event_name'].isin(params.doses[2])]

    # COUNT ALL FROM FIRST DOSE THAT WILL BE 2N DOSES
    # A total of 9 M from dob
    visit2_list = []
    visit3_list = []
    for k,el in first_doses.T.items():
        visit2  = datetime.strptime(el['child_dob'],'%Y-%m-%d')+relativedelta(months=9)
        visit2_list.append(visit2.date())
        visit3 = datetime.strptime(el['child_dob'], '%Y-%m-%d') + relativedelta(months=15)
        visit3_list.append(visit3.date())
    first_doses['future2nd'] = visit2_list
    first_doses['future3rd'] = visit3_list

    visit3_list = []
    for k,el in second_doses.T.items():
        visit3 = datetime.strptime(el['child_dob'], '%Y-%m-%d') + relativedelta(months=15)
        visit3_list.append(visit3.date())
    second_doses['future3rd'] = visit3_list

    all_future2 = first_doses[['record_id','future2nd']]
    all_future2['int_year'] = pd.DatetimeIndex(all_future2['future2nd']).year
    all_future2['int_month'] = pd.DatetimeIndex(all_future2['future2nd']).month

    all_future3 = pd.concat([first_doses,second_doses])[['record_id','future3rd']]
    all_future3['int_year'] = pd.DatetimeIndex(all_future3['future3rd']).year
    all_future3['int_month'] = pd.DatetimeIndex(all_future3['future3rd']).month
    all_together = pd.concat([all_future2,all_future3])

    to_print = all_together.groupby(['int_year','int_month']).count()
    to_print.to_excel(tokens.path_reports+'actual_future_doses.xlsx')

    return to_print

def new_future_doses(actual_prediction=None,recruitment_rate=params.recruitment_rate):
    new_df = pd.DataFrame(columns=['int_year','int_month','record_id','future1st','future2nd','future3rd'])

    """ REMEMBER to change the RECRUITMENT RATE and the TOTAL RECRUITED in the params file or into this function"""
    total_tmp = params.total_recruited
    iterations = 0
    first_month = 10
    year = 2023

    while total_tmp < params.total_to_recruit:
        iterations += 1
        print("interation "+str(iterations))
        if params.total_to_recruit-total_tmp < recruitment_rate:
            total_month = params.total_to_recruit-total_tmp
        else:
            total_month = recruitment_rate

        if first_month == 13:
            first_month=1
            year+=1
        new_df.loc[iterations]= [year,first_month,total_month,total_month,0,0]

        first_month+=1
        total_tmp +=total_month
        print(total_tmp,total_month)

    future_2_doses = pd.DataFrame(columns=['int_year','int_month','future2nd'])
    future_3_doses = pd.DataFrame(columns=['int_year','int_month','future3rd'])

    for k,el in new_df.T.items():
        second = el.int_month+7
        third = el.int_month+13

        if 12 < second < 24:
            second_dosis_month = second-12
            second_dosis_year = el.int_year + 1
        else:
            second_dosis_month = second
            second_dosis_year = el.int_year

        if third <= 24:
            third_dosis_month = third-12
            third_dosis_year = el.int_year + 1
        elif third > 24:
            third_dosis_month = third-24
            third_dosis_year = el.int_year + 2
        else:
            print("EEERRROR")
        future_2_doses.loc[k] = [second_dosis_year,second_dosis_month, recruitment_rate]
        future_3_doses.loc[k] = [third_dosis_year,third_dosis_month, recruitment_rate]

    futures_together = pd.merge(new_df[['int_year','int_month','future1st']],future_2_doses,on=['int_year','int_month'],how='outer')
    futures_together = pd.merge(futures_together,future_3_doses,on=['int_year','int_month'],how='outer')
    join_prediction_new(actual_prediction,futures_together)

def join_prediction_new(actual_prediction, new_doses):
    print("JOINING PREDICTIONS")
    actual_prediction = actual_prediction[['future2nd','future3rd']].reset_index().rename(columns={'future2nd':'actual_second','future3rd':'actual_third'})
    print(actual_prediction)
    new_doses = new_doses.rename(columns={'future2nd':'new_second','future3rd':'new_third','future1st':'new_first'})

    joining = pd.merge(actual_prediction,new_doses,on=['int_year','int_month'],how='outer').replace(np.nan,0)
    joining['all_actual'] = joining['actual_second'] + joining['actual_third']
    joining['all_new'] = joining['new_first'] + joining['new_second']  + joining['new_third']
    joining['all_doses'] = joining['actual_second'] + joining['actual_third'] + joining['new_first'] + joining['new_second']  + joining['new_third']
    joining.to_excel(tokens.path_reports+'doses_prediction_122week.xlsx')


def report_doses_per_month_and_prediction():
    df = all_projects_together()
    # df.to_csv(tokens.path_reports+'all_df.csv')
    doses_per_month(df, tokens.path_reports+'reports_per_months.xlsx')
    #df = pd.read_csv(tokens.path_reports+'all_df.csv')
    df = df.set_index(['record_id', 'redcap_event_name'])
    actual_projection = date_dosis_projections(df)
    new_future_doses(actual_projection)


def participants_intervention_between_dates():
    df = pd.read_csv(tokens.path_reports+'all_df.csv')
    select_dates = pd.read_excel(tokens.path_reports+'PROPOSED_REMOTE_SDV_LIST_FOR_PHARMALYSIS.xlsx')
    select_dates = select_dates.groupby('HF')

    count = 0
    for k,el in select_dates:
        print(k)
        starting_date0 = el['STARTING DATE'].reset_index(drop=True)[0]
        starting_date1 = el['STARTING DATE'].reset_index(drop=True)[1]
        end_date0 = el['END DATE'].reset_index(drop=True)[0]
        end_date1 = el['END DATE'].reset_index(drop=True)[1]
        df = get_one_project(k)
        df = df[df['int_azi'] == 1]
        #df = df[df['intervention_complete'] == 2]
        df['int_date'] = pd.to_datetime(df['int_date'])
        df_good_dates = df[((df['int_date'] <= end_date0) & (df['int_date'] >= starting_date0)) | (df['int_date'] <= end_date1) & (df['int_date'] >= starting_date1)]

        df_good_dates = df_good_dates[['study_number','int_date']].sort_values('int_date')

        df_good_dates['HF_ID'] = k
        df_good_dates['HF_NAME'] = params.HF_NAMES_DICT[k]
        study_numbers = retrieve_study_number(df,df_good_dates.reset_index()['record_id'].unique())

        final_df = pd.merge(df_good_dates.reset_index()[['record_id','HF_ID','HF_NAME','redcap_event_name','int_date']], study_numbers,on='record_id')

        #record_ids_2 = final_df.groupby('record_id').count().sort_values('study_number')
        #for el in record_ids_2[record_ids_2['HF_ID']==2].index.values


        if count != 0:
            together_df = pd.concat([together_df, final_df[['study_number','HF_ID','HF_NAME','redcap_event_name','int_date']]])
        else:
            together_df = final_df[['study_number','HF_ID','HF_NAME','redcap_event_name','int_date']]
        count+=1


    together_df.to_excel(tokens.path_reports+'list_participants_pharmalysis.xlsx',index=False)

def retrieve_study_number(df,list_record_ids):
    df = df.reset_index()
    df = df[(df['redcap_event_name']=='epipenta1_v0_recru_arm_1')&(df['record_id'].isin(list_record_ids))]
    return df.set_index('record_id')[['study_number']]


def physician_reports():
    main_df = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format='df', fields=params.ALERT_LOGIC_FIELDS_SAE_physicians,event_name=['adverse_events_arm_1'])
        df_sn = project.export_records(format='df', fields=['study_number'],event_name=['epipenta1_v0_recru_arm_1'])
        df_sn = df_sn.reset_index()
        df_sn = df_sn[df_sn['redcap_event_name']=='epipenta1_v0_recru_arm_1']
        df = df.reset_index()
        df = df[df['redcap_event_name']=='adverse_events_arm_1']
        df = pd.merge(df,df_sn,left_on='record_id',right_on='record_id')

        df['HF_id'] = project_name.split('.')[0]
        if main_df.empty:
            main_df = df
        else:
            main_df = pd.concat([main_df,df])
#    df = main_df[main_df['redcap_event_name']=='adverse_events_arm_1']

    final_df = main_df[main_df['sae_interviewer_id'].isin(params.SAE_personnel_ids)]
    print(final_df)
    df_to_excel = (final_df[['HF_id','record_id','study_number','sae_report_type', 'sae_med_terms',
                    'sae_icd_10','sae_rel_doc_1','sae_onset',
                    'sae_death','sae_hosp','sae_threat','sae_disability','sae_other','sae_other_criteria',
                    'sae_relationship','sae_severity','sae_expectedness','sae_con_med_rel','sae_outcome','sae_action',
                    'sae_other_action','sae_con_drug_1','sae_con_subs_1','sae_interviewer_id','sae_complete','sae_date']])

    df_to_excel = df_to_excel.sort_values('sae_date',ascending=False)
    print(df_to_excel)

    file_to_drive(params.physicians_worksheet,df_to_excel,tokens.filename_physicians,tokens.
    folder_id_physicians,index_included=False)

def sae_pending_medrecords():
    main_df = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format='df', fields=params.ALERT_LOGIC_FIELDS_SAE_medrecords,event_name=['adverse_events_arm_1'])
        df_sn = project.export_records(format='df', fields=['study_number'],event_name=['epipenta1_v0_recru_arm_1'])
        df_sn = df_sn.reset_index()
        df_sn = df_sn[df_sn['redcap_event_name']=='epipenta1_v0_recru_arm_1']
        df = df.reset_index()
        df = df[df['redcap_event_name']=='adverse_events_arm_1']
        df = pd.merge(df,df_sn,left_on='record_id',right_on='record_id')

        df['HF_id'] = project_name.split('.')[0]
        if main_df.empty:
            main_df = df
        else:
            main_df = pd.concat([main_df,df])

    final_df = main_df[(main_df['sae_rel_doc_1'].isnull())&
            (main_df['sae_rel_doc_2'].isnull())&
            (main_df['sae_rel_doc_3'].isnull())&
            (main_df['sae_rel_doc_4'].isnull())&
            (main_df['sae_rel_doc_5'].isnull())&
            (main_df['sae_rel_doc_6'].isnull())&
            (main_df['sae_rel_doc_7'].isnull())&
            (main_df['sae_rel_doc_8'].isnull()) &
            (main_df['sae_rel_doc_9'].isnull()) &
            (main_df['sae_rel_doc_10'].isnull()) &
            (main_df['sae_rel_doc_11'].isnull()) &
            (main_df['sae_rel_doc_12'].isnull()) &
            (main_df['sae_rel_doc_13'].isnull()) &
            (main_df['sae_rel_doc_14'].isnull()) &
            (main_df['sae_rel_doc_15'].isnull()) &
            (main_df['sae_rel_doc_16'].isnull()) &
            (main_df['sae_rel_doc_17'].isnull()) &
            (main_df['sae_rel_doc_18'].isnull()) &
            (main_df['sae_rel_doc_19'].isnull()) &
            (main_df['sae_rel_doc_20'].isnull()) &
            (main_df['sae_rel_doc_21'].isnull()) &
            (main_df['sae_rel_doc_22'].isnull()) &
            (main_df['sae_rel_doc_23'].isnull()) &
            (main_df['sae_rel_doc_24'].isnull()) &
            (main_df['sae_rel_doc_25'].isnull())
            ][['HF_id','record_id','study_number','sae_hosp_admin_date', 'sae_outcome', 'sae_interviewer_id','sae_date','sae_time',
    'sae_complete']]

    final_df = final_df[final_df['sae_time']>='2023-06-01 00:00:00']
    outcome = []
    complete = []
    for k,el in final_df.T.items():
        try:
            outcome.append(params.sae_outcome_dict[int(el.sae_outcome)])
        except:
            outcome.append('NaN')
        try:
            complete.append(params.sae_complete_dict[int(el.sae_complete)])
        except:
            complete.append('NaN')
    final_df['sae_outcome'] = outcome
    final_df['sae_complete']=complete


    """ EXCLUSION OF VERBAL AUTOPSIES"""
    va_who = pd.read_csv('/home/abofill/Documents/github/py_icaria_reports/va_who_v1_5_3_20230110.csv')
    ica_va = list(va_who['consented-deceased_CRVS-info_on_deceased-ICA001'])

    final_df = final_df[~final_df['study_number'].isin(ica_va)]

    df_to_excel = final_df.sort_values(['HF_id','sae_time'],ascending=[True,False])

    print(df_to_excel)
    df_to_excel.to_excel('/home/abofill/Documents/github/py_icaria_reports/sae_without_medical_record.xlsx',index=False)


def file_to_drive(worksheet,df,drive_file_name,folder_id,index_included=True,deleting=False):
    gc = gspread.oauth(tokens.path_credentials)
    sh = gc.open(title=drive_file_name,folder_id=folder_id)
    if deleting:
        actual_worksheet = sh.worksheet(worksheet)
        actual_worksheet.clear()
    set_with_dataframe(sh.worksheet(worksheet), df,include_index=index_included)


def cohorts():
    all_records = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format='df', fields=params.ALERT_LOGIC_FIELDS_COHORTS,event_name=['cohort_after_mrv_2_arm_1'])
        df = df.reset_index()
        df = df[df['redcap_event_name']=='cohort_after_mrv_2_arm_1']
        if all_records.empty:
            all_records = df
        else:
            all_records = pd.concat([all_records,df])

        print(df.T)

    cohort_records = all_records['record_id'].unique()
    print(cohort_records)



def SPR_baseline_merge_with_lab_results(lab_results,save_):
    project = redcap.Project(tokens.URL, tokens.SPR_BASELINE)
    df = project.export_records(format='df', fields=params.SPR_BASELINE_FIELDS)
    print(df['study_number'].str.replace('SPR-BL-',''))
    print(df.reset_index()['study_number'])
    df['SAMPLE_ID'] = df['study_number'].str.replace('SPR-BL-','')
    df['SAMPLE_ID'] = df['SAMPLE_ID'].astype('float')
    print(df.reset_index()['SAMPLE_ID'])
    lab = pd.read_excel(lab_results,sheet_name='Codons_divide')
    print(lab)


    all_together = pd.merge(df,lab,on='SAMPLE_ID')
    print(all_together)

    all_together.to_excel(save_,index=False)






def compare(x, y):
    if x == y:
        return False
    return True


class CLEANING:
    def more_than_expected_vacc_doses(self):
        final_df = pd.DataFrame(columns=['HF','record_id','study_number','vacc_field','number_of_dates','epipenta1_v0_recru_arm_1',
                                         'epipenta2_v1_iptis_arm_1','epipenta3_v2_iptis_arm_1','epivita_v3_iptisp3_arm_1',
                                         'epimvr1_v4_iptisp4_arm_1','epivita_v5_iptisp5_arm_1','epimvr2_v6_iptisp6_arm_1'])
        c = 0
        final_df_coh = pd.DataFrame(columns=['HF','record_id','study_number','vacc_field','number_of_dates','epipenta1_v0_recru_arm_1',
                                         'epipenta2_v1_iptis_arm_1','epipenta3_v2_iptis_arm_1','epivita_v3_iptisp3_arm_1',
                                         'epimvr1_v4_iptisp4_arm_1','epivita_v5_iptisp5_arm_1','epimvr2_v6_iptisp6_arm_1'])
        c_coh = 0
        for project_name in tokens.REDCAP_PROJECTS_ICARIA:
            print(project_name)
            project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

            study_numbers = project.export_records(format='df', fields=['study_number']).reset_index().set_index('record_id')
            study_numbers = study_numbers[study_numbers['redcap_event_name']=='epipenta1_v0_recru_arm_1'][['study_number']]

            df = project.export_records(format='df', fields=params.LOGIC_FIELDS_INT_ANTIGENS)
            dfcoh = df.reset_index()
            cohorts_list = dfcoh[dfcoh['redcap_event_name']=='cohort_after_mrv_2_arm_1']['record_id'].unique()

            final_df_coh,c_coh = CLEANING().build_new_df(df[(df.index.get_level_values('record_id').isin(cohorts_list))&(df['int_date'].notnull())].groupby(level=0),study_numbers,project_name,final_df_coh,c_coh)
            final_df,c = CLEANING().build_new_df(df[(~df.index.get_level_values('record_id').isin(cohorts_list)) & (df['int_date'].notnull())].groupby(level=0),study_numbers,project_name,final_df,c)

        file_to_drive(params.vacc_coh_worksheet,final_df_coh,tokens.filename_vacc,tokens.folder_id_vacc,index_included=False)
        file_to_drive(params.vacc_worksheet,final_df,tokens.filename_vacc,tokens.folder_id_vacc,index_included=False)

    def build_new_df(self,initial_df,study_numbers,project_name,final_df,count):
        for n, data in initial_df:
            for k, el in data.items():
                if ("date" in str(k) and str(k) != 'int_vacc_vit_a_date' and str(k) != 'int_date' and el.count() > 1) or (str(k) == 'int_vacc_vit_a_date' and el.count() > 2):
                    if reduce(compare, el.dropna().values):
                        final_df.loc[count] = ''
                        final_df.loc[count]['study_number'] = study_numbers.loc[n].values[0]
                        final_df.loc[count]['HF'] = project_name
                        final_df.loc[count]['record_id'] = n
                        final_df.loc[count]['vacc_field'] = k
                        final_df.loc[count]['number_of_dates'] = str(el.count())
                        for event in el.index.get_level_values(1):
                            final_df.loc[count][event] = el.reset_index().set_index('redcap_event_name').T[event].values[-1]
                        count += 1
        #     elif str(k) == 'int_vacc_vit_a_date' and el.count() > 2:
        final_df = final_df.replace(np.nan, '0')
        return final_df,count



    def vacc_not_received(self,age=16,visit='18M'):
        for HF in params.HF_DICT:
            final_df = pd.DataFrame(columns=['HF', 'record_id', 'study_number', 'last_epi_visit', 'Vaccine', 'number_of_dosis'])
            c = 0
            print(HF)
            for project_name in tokens.REDCAP_PROJECTS_ICARIA:
                if HF in str(project_name):
                    print(project_name)
                    project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

                    study_numbers = project.export_records(format='df', fields=['study_number']).reset_index().set_index('record_id')
                    study_numbers = study_numbers[study_numbers['redcap_event_name']=='epipenta1_v0_recru_arm_1'][['study_number']]

                    df = project.export_records(format='df', fields=params.LOGIC_FIELDS_INT_ANTIGENS)
                    dfres = df.reset_index().set_index('record_id')

                    ## FIND THOSE RECORD_IDS WITH AGE MORE THAN 16
                    age_dict = {}
                    more_than_age = []
                    for k,el in dfres[dfres['redcap_event_name']=='epipenta1_v0_recru_arm_1']['child_dob'].T.items():
                        if str(el)!='nan':
                            b = months_between(datetime.today(),datetime.strptime(el,'%Y-%m-%d'))
                            if b >= age:
                                more_than_age.append(k)
                            age_dict[k] = b

                    ## FIND THOSE COMPLETED, DEATH, MIGRATED, WITHDRAWAL OR UNREACHABLE RECORD_IDS
                    completed = dfres[(dfres['redcap_event_name']=='hhat_18th_month_of_arm_1')&(dfres['household_follow_up_complete']==2)].index
                    death = dfres[(dfres['redcap_event_name']=='end_of_fu_arm_1')&(dfres['death_complete']==2)].index
                    migrated = dfres[(dfres['redcap_event_name'] == 'out_of_schedule_arm_1') & (dfres['migration_complete']==2)].index
                    withdrawal = dfres[(dfres['redcap_event_name'] == 'end_of_fu_arm_1') & (dfres['withdrawal_complete']==2)].index
                    unreachable = dfres[(dfres['redcap_event_name'] == 'hhat_18th_month_of_arm_1') & (dfres['reachable_status']==2)].index
                    screening_failures = dfres[(dfres['redcap_event_name'] == 'epipenta1_v0_recru_arm_1') & ((dfres['eligible']==0)|(dfres['study_number'].isnull()))].index

                    errors =dfres[(dfres['redcap_event_name'] == 'epipenta1_v0_recru_arm_1') & (dfres['screening_complete']!=2)].index
                    print("POTENTIAL RECORD ERRORS:")
                    print(errors.values)
                    to_analyse_df = df[((df.index.get_level_values('record_id').isin(more_than_age)) |
                                       (df.index.get_level_values('record_id').isin(completed)))&
                                       (~df.index.get_level_values('record_id').isin(screening_failures))&
                                       (~df.index.get_level_values('record_id').isin(death))&
                                       (~df.index.get_level_values('record_id').isin(migrated))&
                                       (~df.index.get_level_values('record_id').isin(withdrawal))&
                                       (~df.index.get_level_values('record_id').isin(errors))&
                                       (~df.index.get_level_values('record_id').isin(unreachable))

                    ]

                    ## CALCULATION OF THE LAST VISIT AND THE LIST OF VACCINES
                    last_intervention_df = to_analyse_df[to_analyse_df.index.get_level_values('redcap_event_name').isin(params.epi_visits)]

                    ### BCG vaccine in Vaccination History
                    bcg_on_vacc_hist = dfres[dfres['his_vacc_bcg']==1].index


                    for n, data in last_intervention_df.groupby(level=0):
                        last_visit = data[['int_date']][data[['int_date']] == max(data[['int_date']].dropna().values)[0]].dropna().index.get_level_values('redcap_event_name')[0]
                        list_vacc = params.epi_visits_dict[last_visit]
                        for k, el in data.items():
                            if "date" in str(k) and str(k) in list_vacc:
                                if (str(k) == 'int_vacc_vit_a_date' and el.count() < 2) or (str(k) != 'int_vacc_vit_a_date' and el.count() < 1):
                                    if k.split("_date")[0] == 'int_vacc_bcg' and n in bcg_on_vacc_hist:
                                        pass
                                    else:
                                        final_df.loc[c] = ''
                                        final_df.loc[c]['study_number'] = study_numbers.loc[n].values[0]
                                        final_df.loc[c]['HF'] = HF
                                        final_df.loc[c]['record_id'] = n
                                        final_df.loc[c]['last_epi_visit'] = last_visit.split("_arm")[0]
                                        final_df.loc[c]['Vaccine'] = k.split("_date")[0]
                                        final_df.loc[c]['number_of_dosis'] = str(el.count())
                                        c += 1

            if not final_df.empty:
                print(final_df)
                file_to_drive(HF,final_df,tokens.filename_vacc_not_administered,tokens.folder_id_vacc,
                              index_included=False, deleting=True)

def months_between(d1, d2):
    dd1 = min(d1, d2)
    dd2 = max(d1, d2)
    return (dd2.year - dd1.year)*12 + dd2.month - dd1.month

"""
MIRAR SI ALGUN CHILD NO HA REBUT ALGUN ANTIGEN
- BY AGE 16MoA
- Or at 18M visit


Antigens NO but date.
Antigens YES but no date.



"""