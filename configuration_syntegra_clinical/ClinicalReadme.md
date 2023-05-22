# Clinical connector 
The following is a collection of configurations that can use the FHIR connector to convert data in the [FHIR USCDI format](https://hl7.org/fhir/us/core/) to the [Tuva core format](https://docs.tuvahealth.com/).

To execute the script, run `py .\ClinicalConnector.py` while in this folder.

The sample FHIR data here was taken from the [FHIR USCDI website]( http://build.fhir.org/ig/HL7/US-Core/) 


### Configuration Notes

- The Condition configuration example is expecting conditions in an encounter object, rather than in condition objects.  
- ConfigBPDias and ConfigBPSys are parsing the vital sign objects at the component level.  ConfigVitalSign is parsing vital sign objects at the object level.
