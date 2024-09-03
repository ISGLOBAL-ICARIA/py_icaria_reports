from datetime import datetime, date,timedelta
from dateutil.relativedelta import relativedelta
from functools import reduce
import pandas as pd
import numpy as np
import redcap
import params
import tokens
import gspread
from gspread_dataframe import set_with_dataframe
import os

def all_projects_together():
    main_df = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format_type='df', fields=params.ALERT_LOGIC_FIELDS)

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
        df = project.export_records(format_type='df', fields=params.ALERT_LOGIC_FIELDS)

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
        df = project.export_records(format_type='df', fields=params.ALERT_LOGIC_FIELDS_SAE_physicians,event_name=['adverse_events_arm_1'])
        df_sn = project.export_records(format_type='df', fields=['study_number'],event_name=['epipenta1_v0_recru_arm_1'])
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
        df = project.export_records(format_type='df', fields=params.ALERT_LOGIC_FIELDS_SAE_medrecords,event_name=['adverse_events_arm_1'])
        df_sn = project.export_records(format_type='df', fields=['study_number'],event_name=['epipenta1_v0_recru_arm_1'])
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
    cohorts_df = pd.DataFrame(columns=['HF','record_id','study_number'])
    all_records = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df_sn = project.export_records(format_type='df', fields=['study_number'],event_name=['epipenta1_v0_recru_arm_1'])
        df_sn = df_sn.reset_index()
        df_sn = df_sn[df_sn['redcap_event_name']=='epipenta1_v0_recru_arm_1']
        df = project.export_records(format_type='df', fields=params.ALERT_LOGIC_FIELDS_COHORTS,event_name=['cohort_after_mrv_2_arm_1'])
        df = df.reset_index()
        df = df[df['redcap_event_name']=='cohort_after_mrv_2_arm_1']

        df_sn = df_sn.set_index('record_id')[['study_number']]
        if all_records.empty:
            all_records = df
        else:
            all_records = pd.concat([all_records,df])

        for k, el in df.T.items():
#            print(df_sn.loc[el['record_id']]['study_number'])
            cohorts_df.loc[len(cohorts_df)] = project_name, el['record_id'],df_sn.loc[el['record_id']]['study_number']


    cohort_records = all_records['record_id'].unique()
    print(cohort_records)
    cohorts_df.to_csv(tokens.path_reports+"cohort_participants.csv",index=False)


def SPR_baseline_merge_with_lab_results(lab_results,save_):
    project = redcap.Project(tokens.URL, tokens.SPR_BASELINE)
    df = project.export_records(format_type='df', fields=params.SPR_BASELINE_FIELDS)
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


def haily_merge_on_baseline_lab_tabs():
    SA_tab = pd.read_excel('/home/abofill/Documents/BASELINE20240207.xlsx',sheet_name='S.a 2 def')
    SP_tab = pd.read_excel('/home/abofill/Documents/BASELINE20240207.xlsx',sheet_name='S.p 2 def')
    muestras_tab = pd.read_excel('/home/abofill/Documents/BASELINE20240207.xlsx',sheet_name='Muestras')

    print(muestras_tab)
    print(SA_tab)
    print(SP_tab)
    first_merge = pd.merge(muestras_tab,SA_tab,on='MUESTRA',how='left')
    print(first_merge)
    second_merge = pd.merge(first_merge,SP_tab,on='MUESTRA',how='left')
    print(second_merge)

    second_merge.to_excel('/home/abofill/Documents/BASELINE20240216_merged.xlsx',index=False)




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

            study_numbers = project.export_records(format_type='df', fields=['study_number']).reset_index().set_index('record_id')
            study_numbers = study_numbers[study_numbers['redcap_event_name']=='epipenta1_v0_recru_arm_1'][['study_number']]

            df = project.export_records(format_type='df', fields=params.LOGIC_FIELDS_INT_ANTIGENS)
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

                    study_numbers = project.export_records(format_type='df', fields=['study_number']).reset_index().set_index('record_id')
                    study_numbers = study_numbers[study_numbers['redcap_event_name']=='epipenta1_v0_recru_arm_1'][['study_number']]

                    df = project.export_records(format_type='df', fields=params.LOGIC_FIELDS_INT_ANTIGENS)
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



def all_participants_grater_than(months=6,when='01-04-2024'):
    list_records_vaccine = []
    from_date = datetime.strptime(when,'%d-%m-%Y') - relativedelta(months=months)
    print(datetime.strftime(from_date,'%Y-%m-%d'))

    dict_ages = {
        1:0,
        2:0,
        3:0,
        4:0,
        5:0,
    }
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format_type='df', fields=['child_dob'],events=['epipenta1_v0_recru_arm_1'])
        list_records_vaccine+= list(df[df['child_dob']>datetime.strftime(from_date,'%Y-%m-%d')].reset_index()['record_id'])
        df_lower_months = df[df['child_dob'] > datetime.strftime(from_date,'%Y-%m-%d')].reset_index()['child_dob']
        for el in df_lower_months:
            rd=relativedelta(datetime.strptime(when,'%d-%m-%Y'),datetime.strptime(el,'%Y-%m-%d'))
            dict_ages[rd.months]+=1
#        for week in ['2024-02-12','2024-02-19','2024-02-26','2024-03-04','2024-03-11','2024-03-18','2024-03-25','2024-04-01','2024-04-08']:
#            print(week)
#            for i in range(117):
#                rd=relativedelta(datetime.strptime(when,'%d-%m-%Y'),datetime.strptime(week,'%Y-%m-%d'))
#                print(rd.months)

    print(len(list_records_vaccine))
    print(dict_ages)
def actual_deaths():
    total_count = 0
    deaths_per_project = pd.DataFrame(columns=['HF','deaths'])
    all_deaths = pd.DataFrame(columns=['record_id','HF','death_reported_date','death_complete'])
    c = 0
    cc = 0

    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format_type='df', fields=['death_reported_date','death_place','death_date','death_complete','death_interviewer_id'],
                                    events=['end_of_fu_arm_1'],filter_logic= '[death_date]!=""')
        if not df.empty:
            df = df.reset_index()
            for k,record in df.T.items():
                all_deaths.loc[cc] = [record['record_id'],project_name,record['death_reported_date'],record['death_complete']]
                cc += 1
            deaths_per_project.loc[c] = [project_name,len(df)]
            total_count += len(df)
        else:
            deaths_per_project.loc[c] = [project_name, 0]



        c += 1
    #print(deaths_per_project)
    deaths_per_project.to_csv('/home/abofill/Documents/github/py_icaria_reports/deaths_per_project.csv',index=False)
   # print(total_count)
    #print(all_deaths)
    all_deaths.to_csv('/home/abofill/Documents/github/py_icaria_reports/deaths_icaria.csv',index=False)
    to_compare = pd.read_excel('/home/abofill/Baixades/icaria_deaths20240312.xlsx')
    #print(to_compare)

def SAE_checks(from_redcap = False):

    if from_redcap:
        all_sae = pd.DataFrame(columns=params.sae_columns)
        for project_name in tokens.REDCAP_PROJECTS_ICARIA:
            print(project_name)
            project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
            df = project.export_records(format_type='df',forms=['sae'],filter_logic= '[sae_interviewer_id]!=""')
            #df = project.export_records(format_type='df',events=['adverse_events_arm_1'],
            #fields=['sae_date','sae_complete'],filter_logic= '[sae_interviewer_id]!=""')
            if not df.empty:
                for k,el in df.reset_index().set_index('record_id').T.items():
                    to_add = [k,project_name]
                    for l in el:
                        to_add.append(l)
                    all_sae.loc[len(all_sae)] = to_add
        all_sae.to_csv('/home/abofill/Documents/github/py_icaria_reports/SAE/sae_reports_2024_04_09.csv',index=False)
        print(all_sae)
    else:
        all_sae = pd.read_csv('/home/abofill/Documents/github/py_icaria_reports/SAE/sae_reports_2024_04_09.csv',index_col='record_id')
        print(all_sae)
        
        print(all_sae.groupby('sae_outcome').count())

        for group in all_sae.groupby('sae_outcome').groups:
            print(params.sae_outcome[int(group)])

def end_of_study_not_being():
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format_type='df', fields=[
            'death_reported_date','death_date','mig_date','mig_reported_date',
            'wdrawal_date','wdrawal_reported_date',
            'screening_date','id_date','his_date','clin_date','hh_date',
            'a1m_date','react_date','int_date','se_date','comp_date','unsch_date',
            'ae_date','sae_date','ch_his_date','ch_rdt_date','ms_date','mrs_date',
            'mrs_date_t2','mrs_date_t3','azivac_date'],filter_logic= '')

        print(df)

        dfres = df.reset_index()

        for group,el in dfres.groupby('record_id').items():
            print(group)




def mortality_surveillance_interim(output_file, limit=31):

    all_to_be_contacted = pd.DataFrame(columns=['record_id','last_contact'])
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=params.INTERIM_ANALYSIS_FIELDS)
        to_be_surveyed, last_visit_dates = get_record_ids_new_ms(df,limit)

        #print(to_be_surveyed,last_visit_dates)
        last_visit_dates = last_visit_dates.reset_index().rename(columns={0:'last_contact'})
        all_to_be_contacted = pd.concat([all_to_be_contacted,last_visit_dates])
        print(all_to_be_contacted)

    all_to_be_contacted.to_csv(output_file,index=False)


def get_record_ids_new_ms(redcap_data,days_after_epi=31,ms=True):
    """Get the project record ids of the participants requiring a contact to know their vital status, i.e. if they are
    alive or death. Thus, for every project record, check if the date of the last EPI visit was more than some weeks ago
    and the participant hasn't a mortality surveillance contact yet.

    :param redcap_data: Exported REDCap project data
    :type redcap_data: pd.DataFrame
    :param days_after_epi: Number of days since the last visit date when the mortality surveillance contact must be done
    :type days_after_epi: int
    :param excluded_epi_visits: List of EPI visits that are not considered in the mortality surveillance schema
    :type excluded_epi_visits: list

    :return: Array of record ids representing those study participants that require a contact to know their vital status
    (alive or death)
    :rtype: pd.Int64Index
    """

    # Cast int_date and a1m_date columns from str to date and get the last EPI visit and mortality surveillance dates
    x = redcap_data
    x['int_date'] = pd.to_datetime(x['int_date'])
    x['a1m_date'] = pd.to_datetime(x['a1m_date'])
    x['ae_date'] = pd.to_datetime(x['ae_date'])
    x['sae_awareness_date'] = pd.to_datetime(x['sae_awareness_date'])
    x['ms_date'] = pd.to_datetime(x['ms_date'])
    x['hh_date'] = pd.to_datetime(x['hh_date'])
    ms_list = []
    hh_list = []
    for k,el in x.T.items():
        if str(el['ms_status_child']) == '1.0' or str(el['ms_status_child']) == '2.0' or str(el['ms_status_child']) == '6.0':
            ms_list.append(pd.to_datetime(el['ms_date']))
        else:
            ms_list.append(pd.to_datetime(''))

        if str(el['hh_child_seen']) == '1.0' or str(el['hh_why_not_child_seen']) == '3.0':
            hh_list.append(pd.to_datetime(el['ms_date']))
        else:
            hh_list.append(pd.to_datetime(''))

    x['ms_date'] = ms_list
    x['hh_date'] = hh_list
    x['unsch_date'] = pd.to_datetime(x['unsch_date'])
    x['comp_date'] = pd.to_datetime(x['comp_date'])
    x['ch_his_date'] = pd.to_datetime(x['ch_his_date'])
    x['sae_awareness_date'] = pd.to_datetime(x['sae_awareness_date'])

    dates_df = x.groupby('record_id')[
        ['int_date', 'a1m_date', 'hh_date', 'ae_date', 'sae_awareness_date', 'ms_date', 'unsch_date',
         'comp_date', 'ch_his_date']].max().reset_index().set_index('record_id')


    last_visit_dates = dates_df.apply(pd.to_datetime).max(axis=1)
    #    last_visit_dates = x.groupby('record_id')['int_date'].max()
    last_visit_dates = last_visit_dates[last_visit_dates.notnull()]
    # last_ms_contacts = x.groupby('record_id')['a1m_date'].max()
    # last_ms_contacts = last_ms_contacts[last_visit_dates.keys()]
    # already_contacted = last_ms_contacts > last_visit_dates
    days_since_last_epi_visit = datetime.today() - last_visit_dates
    # Remove those participants who have already completed the study follow up, so household visit at 18th month of age
    # has been carried out
    completed_fu = x.query(
        "redcap_event_name == 'hhat_18th_month_of_arm_1' and "
        "household_follow_up_complete == 2"
    )
    death_fu = x.query(
        "redcap_event_name == 'end_of_fu_arm_1' and "
        "death_date != '' "
    )

    to_be_surveyed = days_since_last_epi_visit[days_since_last_epi_visit > timedelta(days=days_after_epi)].keys()
    to_be_surveyed
    if completed_fu is not None:
        record_ids_completed_fu = completed_fu.index.get_level_values('record_id')
        to_be_surveyed = to_be_surveyed.difference(record_ids_completed_fu)

    if death_fu is not None:
        record_ids_death_fu = death_fu.index.get_level_values('record_id')
        to_be_surveyed = to_be_surveyed.difference(record_ids_death_fu)

    return to_be_surveyed, last_visit_dates[list(to_be_surveyed)]


def splitting_by_hf(file_):
    df = pd.read_csv(file_)

    hf = []
    for k,el in df.T.items():
        if len(str(el.record_id)) == 7:
            hf.append(str(el.record_id)[:1])
        elif len(str(el.record_id)) == 8:
            hf.append(str(el.record_id)[:2])
        else:
            hf.append('')

    df['HF'] = hf
    print(df)
    splitted = df.groupby('HF').count()
    output_file = str(file_).split(".")[0] + "_split.csv"
    splitted.to_csv(output_file)



""" TO KNOW IF A PARTICIPANT HAVE ANY REPORT AFTER 18M COMPLETED OR DEATH"""

def forms_after_completed():
    """
    This helps to know if a participant have any report after 18M completed
    or is death, so this report should not be recorded
    :return:
    """


    final_df = pd.DataFrame(columns=['HF','record_id','study_number','actual_status','actual_final_date','last_date_event','last_date_instrument','last_date'])
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL,tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=params.LOGIC_FIELDS_DATES)
        completed_df = df[df['child_fu_status']=='COMPLETED. 18 months of age']
        death_df =  df[df['child_fu_status']=='Death']
        completed_ids = list(completed_df.index.get_level_values('record_id').unique())
        death_ids = list(death_df.index.get_level_values('record_id').unique())
        dfres = df.reset_index()

        study_ids_df = retrieve_study_number(df,dfres['record_id'].unique())
        compl_dates = pd.DataFrame(columns=['record_id','last_date'])
        for record in completed_ids:
            if record != 13020147:
                hh_date = dfres[(dfres['record_id']==record)&(dfres['redcap_event_name']=='hhat_18th_month_of_arm_1')]['hh_date'].values[-1]
                compl_dates.loc[len(compl_dates)] = record,hh_date

        death_dates = pd.DataFrame(columns=['record_id', 'last_date'])
        for record in death_ids:
            death_date = dfres[(dfres['record_id'] == record) & (dfres['redcap_event_name'] == 'end_of_fu_arm_1')]['death_date'].values[-1]
            death_dates.loc[len(death_dates)] = record, death_date


        dfrec = df.reset_index().set_index('record_id')
    #    dfrec = dfrec.drop('redcap_event_name',axis=1)
        #dfrec = dfrec.replace(np.nan,0)
    #    dfres = dfres.drop('sae_date', axis=1)
        for k,el in dfrec.groupby('record_id'):
            #print(k,el)
            max_date = None

            for l, le in el.T.items():
                leres = le[params.LOGIC_FIELDS_DATES]
                leres = leres.drop('child_fu_status', axis=0)


                leres = leres.drop('study_number', axis=0)
    #            leres = leres.drop('sae_date', axis=0)
                to_compare = pd.to_datetime(leres[leres.notnull()], format='%Y-%m-%d')
                #            to_compare = le[le.notnull()]
                if not max_date:
                    max_date = to_compare.max()
                    last_event = le['redcap_event_name']
                    last_instrument = le['redcap_repeat_instrument']

                elif to_compare.max() > max_date:
                    max_date = to_compare.max()
                    last_event = le['redcap_event_name']
                    last_instrument = le['redcap_repeat_instrument']

            if k in completed_ids or k in death_ids:
                if last_event != "hhat_18th_month_of_arm_1" and last_event != "end_of_fu_arm_1":
                    if len(death_dates[death_dates['record_id']==k]['last_date']) != 0:
    #                    print(death_dates[death_dates['record_id'] == k]['last_date'].values[0])
                        comparison = max_date - datetime.strptime(death_dates[death_dates['record_id'] == k]['last_date'].values[0], '%Y-%m-%d %H:%M:%S')
                        real_last_event = 'death'
                        real_last_date = death_dates[death_dates['record_id']==k]['last_date'].values[0]

                    if len(compl_dates[compl_dates['record_id']==k]['last_date']) != 0:
    #                    print(compl_dates[compl_dates['record_id']==k]['last_date'].values[0])
                        comparison = max_date - datetime.strptime(compl_dates[compl_dates['record_id']==k]['last_date'].values[0],'%Y-%m-%d %H:%M:%S')
                        real_last_event = 'completed'
                        real_last_date = compl_dates[compl_dates['record_id']==k]['last_date'].values[0]
                    if k != 13020147:
                        if comparison.days > 0:
                            final_df.loc[len(final_df)] = project_name,k,study_ids_df.loc[k].values[0], real_last_event, str(real_last_date).split(" ")[0], params.dict_event_to_change[str(last_event)], params.dict_event_to_change[str(last_instrument)], str(max_date).split(" ")[0]
                            print(project_name, k, study_ids_df.loc[k].values[0], real_last_event, str(real_last_date).split(" ")[0], params.dict_event_to_change[str(last_event)], params.dict_event_to_change[str(last_instrument)], str(max_date).split(" ")[0])

    print(final_df)
    final_df.to_csv('dates_after_completed_or_death.csv',index=False)


def sae_analyse_repeated_death_sae_outcomes():
    final_df = pd.DataFrame(columns=[
        'record_id','study_number','sae_icd_10','sae_onset','sae_death','sae_death_date',
        'sae_death_va','sae_outcome','sae_interviewer_id','sae_interviewer_role',
        'sae_date','sae_complete'])

    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=params.DEATH_SAE_OUTCOMES)
        df_outcome_death = df[(df['sae_outcome']==7)&(df['sae_icd_10'].notnull())].reset_index()
        study_numbers = retrieve_study_number(df,df_outcome_death['record_id'].unique())
        for k,el in df_outcome_death.groupby('record_id'):
            if len(el) > 1:
                for l, le in el.T.items():
                    to_be_set = [
                        le['record_id'],study_numbers.loc[k].values[0], le['sae_icd_10'], le['sae_onset'],
                        le['sae_death'],
                        le['sae_death_date'], le['sae_death_va'], le['sae_outcome'],
                        le['sae_interviewer_id'], le['sae_interviewer_role'],
                        le['sae_date'],
                        le['sae_complete']]
                    final_df.loc[len(final_df)] = to_be_set


    print(final_df)
    final_df.to_csv('sae_to_be_analyzed_phy.csv',index=False)



def maps_cluster_csv(file_,file_2):
    df = pd.read_csv(file_)
    print(df.columns)
    df['cluster'] = df[df.columns[3:6]].apply(lambda x: ','.join(x.dropna().astype(str)),axis=1)
    df = df[['record_id','district','cluster','household','latitude','longitude']]
    df.to_csv(file_2,index=False)



def deaths_in_hospital():
    hospital_deaths = 0
    home_deaths = 0
    hf_deaths = 0
    all_deaths = 0
    other_deaths = 0
    non_determined = 0
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=params.DAEATH_PLACE)
        hospital_deaths += len(df[df['death_place']==2])
        home_deaths += len(df[df['death_place']==1])
        hf_deaths += len(df[df['death_place']==3])
        other_deaths += len(df[df['death_place']==4])
        print(hospital_deaths)

        df = df.replace(np.nan, 0)
        all_deaths += len(df[df['death_date']!=0])
        non_determined += len(df[(df['death_place']!=0)&df['death_date']!=0])
    print(home_deaths)
    print(hf_deaths)
    print(all_deaths)
    print(other_deaths)
    print(non_determined)

def cotrimox():
   total_cotrim = 0
   total_doses_cotrim=0
   for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=['his_septrin','his_septrin_2','his_septrin_3',
                                                        'clin_septrin','clin_septrin_2','clin_septrin_3',
                                                        'hh_septrin','hh_septrin_2','hh_septrin_3'])
        df = df[(df['his_septrin']==1)|(df['his_septrin_2']==1)|(df['his_septrin_3']==1)|
        (df['clin_septrin']==1)|(df['clin_septrin_2']==1)|(df['clin_septrin_3']==1)|
        (df['hh_septrin']==1)|(df['hh_septrin_2']==1)|(df['hh_septrin_3']==1)]
        print(df)
        dfres = df.reset_index()
        total_doses_cotrim += len(df)
        total_cotrim += len(dfres['record_id'].unique())
        print(total_cotrim)
   print(total_doses_cotrim)


def icd10_code(code):
   for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])


        df = project.export_records(format_type='df',fields=['sae_icd_10'])
        print(df[df['sae_icd_10']==code])


def non_completed(bw=False):
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=['child_fu_status','child_birth_weight_known','child_weight_birth'])

        df = df.fillna('').reset_index()
        noncompleted_df = df[(df['redcap_event_name']=='epipenta1_v0_recru_arm_1')&((~df['child_fu_status'].str.contains('COMPLETED'))&(~df['child_fu_status'].str.contains('Screening Failure'))&(~df['child_fu_status'].str.contains('Death'))&(~df['child_fu_status'].str.contains('UNREACHABLE'))&(~df['child_fu_status'].str.contains('Withdrawn'))&(~df['child_fu_status'].str.contains('Migrated'))&(~df['child_fu_status'].str.contains('withdrawn')))]
       # print(noncompleted_df[['child_fu_status','child_weight_birth']])
        if bw:
            final = noncompleted_df[noncompleted_df['child_birth_weight_known'] == '']
        else:
            final = noncompleted_df[['record_id','child_fu_status']]

        print(final,"\n", final['record_id'].nunique(),"\n\n")

def hospitalizations_consistency_get_data():
    all_df = pd.DataFrame()
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=params.HOSPITALIZATION_FIELDS)
        dfres = df.reset_index()

        dfres = dfres[(dfres['redcap_event_name']=='adverse_events_arm_1')|(dfres['redcap_event_name']=='out_of_schedule_arm_1')|(dfres['redcap_event_name']=='end_of_fu_arm_1')]
        if not all_df.empty:
            all_df = pd.concat([all_df,dfres])
        else:
            all_df = dfres
        print(all_df)

    all_df.to_csv('/home/abofill/Documents/github/py_icaria_reports/hospitalization_data.csv',index=False)


def hospitalizations_consistency():
    dfres = pd.read_csv('/home/abofill/Documents/github/py_icaria_reports/hospitalization_data.csv')

    sae_df = dfres[(dfres['redcap_event_name'] == 'adverse_events_arm_1')][[
        'record_id','sae_hosp','sae_hosp_admin_date','sae_date','sae_death',
        'sae_death_date']]
    print(sae_df)
    print("SAE hospitalized", len(sae_df[(sae_df['sae_hosp']==1)]))
    print("SAE non-hospitalized",len(sae_df[(sae_df['sae_hosp']==0)]))
    print("SAE no data about hospitalization",len(sae_df[(sae_df['sae_hosp']!=1)&(sae_df['sae_hosp']!=0)]))

    print('SAEs deaths', len(sae_df[(sae_df['sae_death']==1)]))
    print('SAEs NO deaths', len(sae_df[(sae_df['sae_death']==0)]))
    print("SAE no data about death ",len(sae_df[(sae_df['sae_death']!=1)&(sae_df['sae_death']!=0)]))

    print("SAEs hospitalized & NO death (sae_death=YES)",len(sae_df[(sae_df['sae_hosp']==1)&(sae_df['sae_death']==0)]))
    print("SAEs hospitalized & death (sae_death=YES)",len(sae_df[(sae_df['sae_hosp']==1)&(sae_df['sae_death']==1)]))

    print("SAEs non-hospitalized & NO death (sae_death!=YES)",len(sae_df[(sae_df['sae_hosp']==0)&(sae_df['sae_death']==0)]))
    print("SAEs non-hospitalized & death (sae_death=YES)",len(sae_df[(sae_df['sae_hosp']==0)&(sae_df['sae_death']==1)]))


def MRS_baseline_districts_file():
    all_df = pd.DataFrame()
    mostres = pd.read_excel('/home/abofill/Baixades/BASELINE.xlsx',sheet_name='S.a  DEF')
    mostres2 = pd.read_excel('/home/abofill/Baixades/BASELINE.xlsx',sheet_name='S.p DEF')
    print(mostres)

    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL, tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df',fields=params.MRS_FIELDS)
        dfres = df.reset_index()
        dfres = dfres[(dfres['redcap_event_name']=='epipenta1_v0_recru_arm_1')&(dfres['mrs_study_number'].notnull())]

        for el in params.districts:
            if project_name in params.districts[el]:
                district = el
        df = dfres[['mrs_study_number']]
        df['district'] = district

        if not all_df.empty:
            all_df = pd.concat([all_df, df])
        else:
            all_df = df
    all_df.to_csv('/home/abofill/Baixades/BASELINE.csv',index=False)

def MRS_baseline_districts():
    mostres = pd.read_excel('/home/abofill/Baixades/BASELINE.xlsx',sheet_name='S.a  DEF')
    mostres2 = pd.read_excel('/home/abofill/Baixades/BASELINE.xlsx',sheet_name='S.p DEF')
    all_df = pd.read_csv('/home/abofill/Baixades/BASELINE.csv')
    district_dict = all_df.set_index('mrs_study_number')

    print(mostres)
    print(mostres2)

    district_list = get_district(mostres,district_dict)
    mostres['District'] = district_list

    district_list2 = get_district(mostres2,district_dict)
    mostres2['District'] = district_list2

    print(mostres2)
    with pd.ExcelWriter("/home/abofill/Baixades/BASELINE_AB.xlsx") as writer:
        mostres.to_excel(writer, sheet_name="S.a  DEF")
        mostres2.to_excel(writer, sheet_name="S.p DEF")

def get_district(mostres,district_dict):
    district_list = []
    for el in mostres['MUESTRA']:
        id = "MRS-"+str(el.split("'")[0].split("MRS")[1])
        try:
            district_list.append(district_dict.loc[id]['district'])
        except:
            id = "MRS-" + str(el.split("´")[0].split("MRS")[1])
            try:
                district_list.append(district_dict.loc[id]['district'])
            except:
                print('ERROR: '+id)

    return district_list


def bombali_deaths():
    final_death_df = pd.DataFrame(columns=['HF','record_id','study_number',
                                           'death_place','death_date'
                                           ])

    second_final_death_df = pd.DataFrame(columns=['record_id', 'child_dob',
                                                  'child_name', 'child_sex',
                                                  'caretaker_name', 'phone',
                                                  'community',
                                                  'address'])
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        if project_name in params.districts['Bombali']:
            print(project_name)
            project = redcap.Project(tokens.URL,
                                     tokens.REDCAP_PROJECTS_ICARIA[project_name])

            df = project.export_records(format_type='df', fields=params.DEATHS_BOMBALI_FIELDS,
                                        events=['end_of_fu_arm_1'])
            df_study_number = project.export_records(format_type='df', fields=params.DEATHS_DEMO_FIELDS,
                                        events=['epipenta1_v0_recru_arm_1'])

            study_numbers_dict = df_study_number.reset_index().set_index('record_id')['study_number'].to_dict()
            addresses_dict = df_study_number.reset_index().set_index('record_id')['community'].to_dict()

            dfres = df.reset_index().set_index('record_id')
            dfres = dfres.fillna('')
            dfres = dfres[dfres['death_interviewer_id']!='']
            #print(dfres)
            #dfres = dfres.fillna(0)
            for k,el in dfres.T.items():
                #print(k, int(el['death_place']))
                if int(el['death_place']) == 1:
                    place = 'Home'
                elif int(el['death_place']) == 2:
                    if int(el['death_hosp'])== 88:
                        place = el['death_hosp_other']
                    else:
                        place = params.death_hosp[int(el['death_hosp'])]
                elif int(el['death_place']) == 3:
                    place = params.death_hf[int(el['death_hf'])]
                elif int(el['death_place']) == 88:
                    place = el['death_other_place']
                else:
                    place = ''

                #print(place,"\n")
                final_death_df.loc[len(final_death_df)] = project_name.split(".")[0],k,study_numbers_dict[int(k)],place,el['death_reported_date']

            death_records = list(final_death_df['record_id'].unique())
            df_id = df_study_number.reset_index().set_index('record_id')
            df_id = df_id.fillna('')

            for k,el in df_id.T.items():
                if k in death_records:
                    child_name = str(el['child_first_name']) + " " + str(el['child_surname'])
                    #print(el)
                    if int(el['mother_caretaker']) == 1:
                        caretaker_name = str(el['mother_first_name']) + " " + str(el['mother_surname'])
                    elif int(el['caretaker']) == 2:
                        caretaker_name = str(el['father_first_name']) + " " + str(el['father_surname'])
                    elif int(el['caretaker']) == 88:
                        caretaker_name = str(el['caretaker_first_name']) + " " + str(el['caretaker_surname'])
                    else:
                        caretaker_name = ''

                    if int(el['community']) == 88:
                        comm = el['other_community']
                    else:
                        comm = params.community[int(el['community'])]

                    second_final_death_df.loc[len(second_final_death_df)] = k, el['child_dob'], child_name, params.child_sex[int(el['child_sex'])],caretaker_name,el['phone_1'],comm,el['address']
            #second_final_death_df = second_final_death_df.set_index('record_id')
            #final_death_df = final_death_df.set_index('record_id')

            fdf = pd.merge(final_death_df,second_final_death_df,on='record_id')

    print(fdf)
    fdf.to_excel('/home/abofill/Documents/github/py_icaria_reports/ICARIA_deaths_bombali.xlsx',index=False)


def azivac_sn():
    all = pd.DataFrame(columns=['record_id','study_number','Azivac_study_number'])
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL,tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df_sn = project.export_records(format_type='df', fields=['study_number'],events=['epipenta1_v0_recru_arm_1'])
        sn_dict = df_sn.reset_index().set_index('record_id')['study_number'].to_dict()

        df = project.export_records(format_type='df', fields=params.AZIVAC_SN_FIELDS)
        dfres = df.reset_index()
        dfres =dfres.fillna('')
        final = dfres[(dfres['redcap_event_name']=='epimvr1_v4_iptisp4_arm_1')&(dfres['azivac_interviewer_id']!='')][['record_id','azivac_study_number']]

        good_final = final[final['azivac_study_number'].isin(params.azi_to_not_count)]
        for k,el in good_final.T.items():
            all.loc[len(all)] = el['record_id'], sn_dict[el['record_id']], el['azivac_study_number']

        print(all)


def counts():
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL,tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df_sn = project.export_records(format_type='df', fields=['study_number'],events=['epipenta1_v0_recru_arm_1'])
        print(len(df_sn))



def find_repeated_va():
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)
        project = redcap.Project(tokens.URL,tokens.REDCAP_PROJECTS_ICARIA[project_name])

        df = project.export_records(format_type='df', fields=['mother_first_name','mother_surname'],events=['epipenta1_v0_recru_arm_1'])
        print(df.columns)
        df[df['mother_first_name']==tokens.mother_firstname]


def ongoing_participants():
    status_per_hf = pd.DataFrame(columns=['HF','ongoing','all_completed','completed','death','unreachable','withdrawn','migrated','Screening Failure'])
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL,tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_records(format_type='df', fields=['child_fu_status'],events=['epipenta1_v0_recru_arm_1'])

        df_ong = df[df['child_fu_status'].apply(
            lambda x: 'COMPLETED' not in str(x) and 'Death' not in str(
                x) and 'Migrated' not in str(x) and 'withdrawn' not in str(
                x) and 'Withdrawn' not in str(x) and 'UNREACHABLE' not in str(
                x) and 'Screening Failure' not in str(x))]


        ong = df_ong.reset_index()['record_id'].unique()
        if len(ong) < 10 and not df_ong.empty:
            print(df_ong)

        df_comp = df[~df['child_fu_status'].apply(
            lambda x: 'COMPLETED' not in str(x) and 'Death' not in str(
                x) and 'Migrated' not in str(x) and 'withdrawn' not in str(
                x) and 'Withdrawn' not in str(x) and 'UNREACHABLE' not in str(
                x) and 'Screening Failure' not in str(x))]
        all_completed = df_comp.reset_index()['record_id'].unique()

        completed = df[df['child_fu_status'].apply(
            lambda x: 'COMPLETED' in str(x))].reset_index()['record_id'].unique()
        death = df[df['child_fu_status'].apply(
            lambda x: 'Death' in str(x))].reset_index()['record_id'].unique()
        migr = df[df['child_fu_status'].apply(
            lambda x: 'Migrated' in str(x))].reset_index()['record_id'].unique()
        withdr = df[df['child_fu_status'].apply(
            lambda x: 'withdrawn' in str(x) or 'Withdrawn' in str(x) )].reset_index()['record_id'].unique()
        unreach = df[df['child_fu_status'].apply(
            lambda x: 'UNREACHABLE' in str(x))].reset_index()['record_id'].unique()
        screen_failure = df[df['child_fu_status'].apply(
            lambda x: 'Screening Failure' in str(x))].reset_index()['record_id'].unique()

        status_per_hf.loc[len(status_per_hf)] = (
            project_name, len(ong), len(all_completed), len(completed), len(death),
            len(unreach),len(withdr),len(migr),len(screen_failure))

    print(status_per_hf)
    status_per_hf.to_csv(tokens.path_reports + 'summary_recruitment_20240718.csv',index=False)



def metadata():
    for project_name in tokens.REDCAP_PROJECTS_ICARIA:
        print(project_name)

        project = redcap.Project(tokens.URL,tokens.REDCAP_PROJECTS_ICARIA[project_name])
        df = project.export_metadata(format_type='df')
        print(df)
        df.to_csv(tokens.path_reports + 'summary_metadata.csv')
        break
#        export_records(format_type='df', fields=['child_fu_status'],events=['epipenta1_v0_recru_arm_1'])



def downloads_comprovacio(primera, segona):
    for file in os.listdir(primera):
        prdf = pd.read_csv(os.path.join(primera,file))
        print(prdf)
    print("SEPARACIOOOOOOOOOOOOOOOOO")
    for file in os.listdir(segona):
        prdf = pd.read_csv(os.path.join(segona,file))
        print(prdf)