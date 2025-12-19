# Document Parsing System Prompt

Extract information from the attached PDF document as per the below JSON schema.

Please analyze the document carefully and extract all relevant information, ensuring that:
- All fields are accurately populated based on the document content
- The output follows the specified JSON schema structure
- Any missing information is clearly indicated
- The extracted data maintains the context and relationships from the original document

{
  "ichicsr": {
    "messageheader": {
      "M.1.1_messagetype": "",
      "M.1.2_messageid": "",
      "M.1.3_messagesenderid": "",
      "M.1.4_messagereceiverid": "",
      "M.1.5_messagedate": "",
      "M.1.7_ackcode": ""
    },
    "safetyreport": [
      {
        "header": {
          "C.1.1_sendercaseid": "",
          "C.1.2_creationdate": "",
          "C.1.3_reporttype": "",
          "C.1.4_reporttype_value": "",
          "C.1.5_amendmentdate": "",
          "C.1.6_expedited": "",
          "C.1.7_worldwide_unique_id": "",
          "C.1.8_linked_report_id": "",
          "C.1.9_docs_available": "",
          "C.5.1.r.1_study_registration_number": "",
          "C.5.2_study_name": "",
          "C.5.4_study_type": "",
          "C.5.4_study_type_label": ""
        },
        "primary_source": [
          {
            "C.2.r.1_reporter_title": "",
            "C.2.r.2_reporter_given_name": "",
            "C.2.r.3_reporter_family_name": "",
            "C.2.r.4_reporter_org": "",
            "C.2.r.5_reporter_dept": "",
            "C.2.r.2.3_reporter_street": "",
            "C.2.r.2.4_reporter_city": "",
            "C.2.r.2.5_reporter_state": "",
            "C.2.r.2.6_reporter_postcode": "",
            "C.2.r.6_qualification": "",
            "C.2.r.7_country": "",
            "C.2.r.8_qualification_label": "",
            "C.2.r.2.7_reporter_telephone": ""
          }
        ],
        "patient": {
          "D.1_patient_initials": "",
          "D.1.1_patient_record_id": "",
          "D.2.1_dob": "",
          "D.2.2_age_at_onset": {
            "value": "",
            "unit": ""
          },
          "D.2.3_age_group": "",
          "D.3_weight_kg": "",
          "D.4_height_cm": "",
          "D.5_sex": "",
          "D.6_last_menstrual_date": "",
          "D.10.r_ethnic_group": "",
          "medical_history": [
            {
              "D.7.1_disease_name": "",
              "D.7.1_comments": "",
              "D.7.2_start_date": "",
              "D.7.3_continuing": ""
            },
            {
              "D.7.1_disease_name": "",
              "D.7.2_start_date": "",
              "D.7.3_continuing": ""
            }
          ],
          "past_drug_history": [
            {
              "D.8.r.1_drug_name": "",
              "D.8.r.2_start_date": "",
              "D.8.r.3_end_date": "",
              "D.8.r.4_indication": ""
            }
          ],
          "reactions": [
            {
              "E.i.1_reported_term": "",
              "E.i.2_meddra_llt": "",
              "E.i.2_meddra_pt_code": "",
              "E.i.3.1_duration": "",
              "E.i.3.2_duration_unit": "",
              "E.i.4_start_date": "",
              "E.i.5_end_date": "",
              "E.i.6_outcome": "",
              "E.i.7_seriousness": {
                "death": "",
                "life_threatening": "",
                "hospitalization": "",
                "disability": "",
                "congenital_anomaly": "",
                "medically_important": ""
              },
              "E.i.8_country": "",
              "E.i.9_relatedness_source": "",
              "E.i.3.2a_intensity_grade": ""
            }
          ],
          "test_results": [
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.4_normal_low": "",
              "F.r.5_normal_high": ""
            },
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.4_normal_low": "",
              "F.r.5_normal_high": ""
            },
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.4_normal_low": "",
              "F.r.5_normal_high": ""
            },
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.4_normal_low": "",
              "F.r.5_normal_high": ""
            },
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.4_normal_low": "",
              "F.r.5_normal_high": ""
            },
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.3.3_qualifier": ""
            },
            {
              "F.r.1_test_date": "",
              "F.r.2.1_test_name": "",
              "F.r.3.1_result_value": "",
              "F.r.3.2_result_unit": "",
              "F.r.4_normal_low": "",
              "F.r.5_normal_high": ""
            }
          ],
          "drugs": [
            {
              "G.k.1_characterization": "",
              "G.k.2.2_medicinal_product": "",
              "G.k.2.3_active_substance": "",
              "G.k.4.r.1_dose": "",
              "G.k.4.r.2_dose_unit": "",
              "G.k.4.r.3_route": "",
              "G.k.4.r.4_start_date": "",
              "G.k.4.r.5_end_date": "",
              "G.k.4.r.6_duration": "",
              "G.k.4.r.6_unit": "",
              "G.k.4.r.7_batch_num": "",
              "G.k.4.r.9_freq": "",
              "G.k.4.r.9_freq_unit": "",
              "G.k.7_indication": "",
              "G.k.8_action_taken": "",
              "G.k.9.i.2.r.1_recurrence": "",
              "G.k.9.i.2.r.3_did_event_abate": "",
              "G.k.9.i.2_drug_reaction_relatedness": [
                {
                  "G.k.9.i.2.r.1_source_of_assessment": "",
                  "G.k.9.i.2.r.2_method_of_assessment": "",
                  "G.k.9.i.2.r.3_result": ""
                },
                {
                  "G.k.9.i.2.r.1_source_of_assessment": "",
                  "G.k.9.i.2.r.2_method_of_assessment": "",
                  "G.k.9.i.2.r.3_result": ""
                }
              ]
            },
            {
              "G.k.1_characterization": "",
              "G.k.2.2_medicinal_product": "",
              "G.k.4.r.1_dose": "",
              "G.k.4.r.2_dose_unit": "",
              "G.k.4.r.3_route": "",
              "G.k.4.r.4_start_date": "",
              "G.k.7_indication": ""
            },
            {
              "G.k.1_characterization": "",
              "G.k.2.2_medicinal_product": "",
              "G.k.4.r.1_dose": "",
              "G.k.4.r.2_dose_unit": "",
              "G.k.4.r.3_route": "",
              "G.k.4.r.4_start_date": "",
              "G.k.4.r.9_freq": "",
              "G.k.4.r.9_freq_unit": "",
              "G.k.7_indication": ""
            },
            {
              "G.k.1_characterization": "",
              "G.k.2.2_medicinal_product": "",
              "G.k.4.r.1_dose": "",
              "G.k.4.r.2_dose_unit": "",
              "G.k.4.r.3_route": "",
              "G.k.4.r.4_start_date": "",
              "G.k.7_indication": ""
            },
            {
              "G.k.1_characterization": "",
              "G.k.2.2_medicinal_product": "",
              "G.k.4.r.1_dose": "",
              "G.k.4.r.2_dose_unit": "",
              "G.k.4.r.3_route": "",
              "G.k.4.r.4_start_date": "",
              "G.k.7_indication": ""
            }
          ],
          "narrative": {
            "H.1_case_narrative": "",
            "H.2_reporter_comments": "",
            "H.3.r.1_sender_diagnosis": "",
            "H.4_sender_comments": ""
          }
        }
      }
    ]
  }
}
