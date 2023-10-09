#!/usr/bin/env python
""" Python script to manage generate reports in the ICARIA Clinical Trial."""

import reports
import tokens

__author__ = "Andreu Bofill Pumarola"
__copyright__ = "Copyright 2023, ISGlobal Maternal, Child and Reproductive Health"
__credits__ = ["Andreu Bofill Pumarola"]
__license__ = "MIT"
__version__ = "0.0.1"
__date__ = "20230928"
__maintainer__ = "Andreu Bofill"
__email__ = "andreu.bofill@isglobal.org"
__status__ = "Dev"


if __name__ == '__main__':
    """ DOSES PER MONTH  AND PREDICTION KWABENA 20231028 """
    #reports.report_doses_per_month_and_prediction()
    """ PARTICIPANTS THAT RECEIVED INTERVENTION BETWEEN TWO DATES (dates in excel file)"""
    #reports.participants_intervention_between_dates()

    """ PHYSICIANS CONSULTANT REPORT UPDATES"""
    reports.physician_reports()