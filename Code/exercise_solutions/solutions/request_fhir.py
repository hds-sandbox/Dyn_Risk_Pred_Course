from urllib.parse import urlparse, parse_qs
import json
import os
import random
import pandas as pd
from requests.models import Response

# Calculate data directory path relative to this script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../../exercise_data/raw_data'))

"""NOTE: This code creates a simulated server or a 'mock api', designed to handle data in FHIR format. 
The code simulates the process of GET data and the request to create data (POST). """

BASE_URL = 'https://test/fhir'
JSON_HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}
RAW_PATIENT_STR = ('{{"resourceType":"Patient","id":"{id}","meta":{{"versionId":"1","lastUpdated":"2023-05-23T09:33:58.623+00:00","source":"#TxHlcnq3KZSdg567"}},'
                   '"text":{{"status":"generated","div":"<div>Some HTML</div>"}},"identifier":[{{"system":"http://example.org","value":"002"}}],"gender":"{gender}",'
                   '"birthDate":"{birthdate}"}}')
RAW_OBSERVATION_STR = ('{{"resourceType":"Observation","id":"10308213","meta":{{"versionId":"1","lastUpdated":"2023-04-19T10:00:27.158+00:00","source":"#2I8F1Uz63ty9AVBh"}},'
                       '"code":{{"coding":[{{"system":"http://snomed.info/sct","code":"{code}"}}]}},"status":"final","subject":{{"reference":"Patient/{patient_id}"}},'
                       '"effectiveDateTime":"{date}","valueQuantity":{{"value":"{value}"}}}}')
RAW_PROCEDURE_STR = ('{{"resourceType":"Procedure","id":"10308213","meta":{{"versionId":"1","lastUpdated":"2023-04-14T10:00:27.158+00:00","source":"#2I8F1Uzwdaty9AVBh"}},'
                     '"code":{{"coding":[{{"system":"http://snomed.info/sct","code":"{code}"}}]}},"subject":{{"reference":"Patient/{patient_id}"}},'
                     '"performedDateTime":"{date}","valueQuantity":{{"value":"{value}"}}}}')
RAW_ENTRY_START_STR = '{{"fullUrl":"{base_url}/{entity}/{id}","resource":'
RAW_ENTRY_END_STR = ',"search":{{"mode":"match"}}}'
RAW_BUNDLE_STR = ('{{"resourceType":"Bundle","id":"512f46e7-1df0-4fc9-83c9-f871a625558d","meta":{{"lastUpdated":"2023-06-09T09:54:34.061+00:00"}},'
                  '"type":"searchset","link":[{{"relation":"self","url":"{base_url}/{entity}"}}],"entry":[{entries}]}}')


def post(url, data, headers):
    response = Response()

    if not url.startswith(BASE_URL):
        response.status_code = 404
        response._content = b'{ "error" : "NOT_FOUND", "message": "You are trying to contact an inexisting server, check your URL."}'
        return response

    try:
        if headers['Content-type'] != JSON_HEADERS['Content-type']:
            response.status_code = 403
            response._content = b'{ "error" : "METHOD_NOT_ALLOWED", "message": "The content-type is not correct."}'
            return response
    except KeyError:
        response.status_code = 403
        response._content = b'{ "error" : "BAD_REQUEST", "message": "It seems no content-type is defined."}'
        return response

    data_json = json.loads(data)

    object_id = random.randint(1356, 9871)
    data_json['id'] = object_id
    data_json['meta']['versionId'] = '1'
    data_json['meta']['lastUpdated'] = '2022-09-09T09:15:01.328000+00:00'
    data_json['text'] = {
        'status': "generated",
        'div': "<div xmlns=\"http://www.w3.org/1999/xhtml\"><div class=\"hapiHeaderText\">Some object</div>"
               "<table class=\"hapiPropertyTable\"><tbody><tr><td>Identifier</td><td>" + str(object_id) +
               "</td></tr></tbody></table></div>"
    }

    data = json.dumps(data_json)

    response.status_code = 200
    response._content = bytes(data, 'utf-8')

    return response


def get(url):
    response = Response()
    response.status_code = 200

    if not url.startswith(BASE_URL):
        response.status_code = 404
        response._content = b'{ "error" : "NOT_FOUND", "message": "You are trying to contact an inexisting server, check your URL."}'
        return response

    entity_with_info = url.replace(BASE_URL + '/', '').split('/')
    entity = entity_with_info[0].split('?')[0]
    entity_id = 0

    if len(entity_with_info) == 2:
        entity_id = entity_with_info[1].split('?')[0]
        if len(entity_id) == 0:
            entity_id = 0
        else:
            entity_id = int(entity_id)

    baseline_df = pd.read_csv(os.path.join(_DATA_DIR, 'baseline_data.csv'), parse_dates=['d.birth'])
    snomed_df = pd.read_csv(os.path.join(_DATA_DIR, 'snomed.csv'))

    if entity == 'Patient':
        if entity_id:
            patient_list = baseline_df.loc[baseline_df['id'] == entity_id]
            if len(patient_list) != 1:
                response.status_code = 404
                response._content = b'{ "error" : "NOT_FOUND", "message": "The patient was not found."}'
                return response

            patient_info = patient_list.iloc[0]
            patient_str = RAW_PATIENT_STR.format(base_url=BASE_URL, id=entity_id, gender=patient_info['sex'],
                                                 birthdate=patient_info['d.birth'].strftime("%Y-%m-%d"))
            response._content = bytes(patient_str, 'utf-8')
            return response
        else:
            entries_list = []
            for key, patient_info in baseline_df.iterrows():
                entries_list.append((RAW_ENTRY_START_STR +
                                     RAW_PATIENT_STR +
                                     RAW_ENTRY_END_STR).format(base_url=BASE_URL, entity=entity, id=patient_info['id'],
                                                               gender=patient_info['sex'],
                                                               birthdate=patient_info['d.birth'].strftime("%Y-%m-%d")))

            entries_str = ','.join(entries_list)
            bundle_str = RAW_BUNDLE_STR.format(base_url=BASE_URL, entity=entity, entries=entries_str)
            response._content = bytes(bundle_str, 'utf-8')
            return response

    elif entity in ['Observation', 'Procedure']:
        if entity_id:
            response.status_code = 501
            response._content = b'{ "error" : "NOT_IMPLEMENTED", "message": "You cannot fetch an observation or procedure using an ID."}'
            return response

        parse_result = urlparse(url)
        dict_result = parse_qs(parse_result.query)

        try:
            patient_ids = dict_result['patient'][0].split(',')
            snomed_codes = dict_result['code'][0].split(',')
        except KeyError:
            response.status_code = 501
            response._content = b'{ "error" : "NOT_IMPLEMENTED", "message": "You cannot request all observations or procedures, please specify one or more patient IDs and one or more codes."}'
            return response

        if entity == 'Procedure':
            treat_df = pd.read_csv(os.path.join(_DATA_DIR, 'treat_data.csv'), parse_dates=['treat_start_date'], index_col=0)
            event_df = (pd.read_csv(os.path.join(_DATA_DIR, 'events.csv'), parse_dates=['date'], index_col=0)
                        .query("type != 'death'")
                        .assign(revascularization=lambda df: (df["event"] == "revascularization").astype(int),
                                malignancy=lambda df: (df["event"] == "malignancy").astype(int),
                                infarction=lambda df: (df["event"] == "infarction").astype(int),
                                amputation=lambda df: (df["event"] == "amputation").astype(int),
                                stroke=lambda df: (df["event"] == "stroke").astype(int)))

        if entity == 'Observation':
            blood_df = pd.read_csv(os.path.join(_DATA_DIR, 'blood_data.csv'), parse_dates=['sample_date'], index_col=0)
            diag_df = pd.read_csv(os.path.join(_DATA_DIR, 'diag_data.csv'), parse_dates=['sample_date'], index_col=0)
            quest_df = pd.read_csv(os.path.join(_DATA_DIR, 'quest_data.csv'), parse_dates=['date.x'], index_col=0)
            visit_df = pd.read_csv(os.path.join(_DATA_DIR, 'visit_date.csv'), parse_dates=['visit_date'], index_col=0)

        entries_list = []

        for patient_id in patient_ids:
            patient_id = int(patient_id)
            patient_list_df = baseline_df.loc[baseline_df['id'] == patient_id]
            if len(patient_list_df) != 1:
                response.status_code = 404
                response._content = b'{ "error" : "NOT_FOUND", "message": "The patient was not found."}'
                return response

            patient_info = patient_list_df.iloc[0]

            for snomed_code in snomed_codes:
                snomed_code = int(snomed_code)
                snomed_list_df = snomed_df.loc[snomed_df['code'] == snomed_code]
                if len(snomed_list_df) != 1:
                    response.status_code = 404
                    response._content = b'{ "error" : "NOT_FOUND", "message": "The SNOMED code was not found."}'
                    return response

                snomed_info = snomed_list_df.iloc[0]

                if snomed_info['source'] == 'blood_data':
                    entries_temp_df = blood_df.loc[blood_df['..record.id'] == patient_id][['sample_date', snomed_info['label']]].rename(
                        columns={'sample_date': 'date', snomed_info['label']: 'value'})

                elif snomed_info['source'] == 'diag_data':
                    patient_diag_df = diag_df.loc[(diag_df['id'] == patient_id) & (diag_df['code'] == snomed_info['label'])][['sample_date']]
                    patient_diag_df['value'] = 1
                    entries_temp_df = patient_diag_df.rename(columns={'sample_date': 'date'})

                elif snomed_info['source'] == 'quest_data':
                    entries_temp_df = quest_df.loc[quest_df['id'] == patient_id][['date.x', snomed_info['label']]].rename(
                        columns={'date.x': 'date', snomed_info['label']: 'value'})

                elif snomed_info['source'] == 'treat_data':
                    entries_temp_df = treat_df.loc[treat_df['record_id'] == patient_id][['treat_start_date', snomed_info['label']]].rename(
                        columns={'treat_start_date': 'date', snomed_info['label']: 'value'})

                elif snomed_info['source'] == 'events':
                    entries_temp_df = event_df.loc[event_df['id'] == patient_id][['date', snomed_info['label']]].rename(
                        columns={snomed_info['label']: 'value'})

                elif snomed_info['source'] == 'baseline_data' and snomed_info['label'] == 'smoker':
                    visit_row = visit_df.loc[visit_df['id'] == patient_id].sort_values(by=['visit_date']).head(1)
                    visit_row['value'] = patient_info['smoking']
                    entries_temp_df = visit_row.rename(columns={'visit_date': 'date'})

                elif snomed_info['source'] == 'visit_date' and snomed_info['label'] == 'visit':
                    visit_row = visit_df.loc[visit_df['id'] == patient_id].sort_values(by=['visit_date'])
                    visit_row['value'] = True
                    entries_temp_df = visit_row.rename(columns={'visit_date': 'date'})

                else:
                    response.status_code = 501
                    response._content = b'{ "error" : "NOT_IMPLEMENTED", "message": "The corresponding data set could not be found." }'
                    return response

                entries_temp_df['code'] = snomed_code
                entries_temp_df['patient_id'] = patient_id
                entries_list.append(entries_temp_df)

        entries_df = pd.concat(entries_list)
        entries_str_list = []
        for _, entry_info in entries_df.iterrows():
            raw_entry_body_str = RAW_OBSERVATION_STR if entity == 'Observation' else RAW_PROCEDURE_STR
            entries_str_list.append((RAW_ENTRY_START_STR + raw_entry_body_str + RAW_ENTRY_END_STR).format(
                base_url=BASE_URL, entity=entity, id='1234', code=entry_info['code'],
                patient_id=entry_info['patient_id'], date=entry_info['date'].strftime("%Y-%m-%d"), value=entry_info['value']))

        entries_str = ','.join(entries_str_list)
        bundle_str = RAW_BUNDLE_STR.format(base_url=BASE_URL, entity=entity, entries=entries_str)
        response._content = bytes(bundle_str, 'utf-8')
        return response

    else:
        response.status_code = 501
        response._content = b'{ "error" : "NOT_IMPLEMENTED", "message": "This server only supports calls for Patient, Observation or Procedure." }'
        return response
