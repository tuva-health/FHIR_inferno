# BCDA Connector 
The following is a collection of configurations that can use 
the FHIR connector to convert data in the 
[BCDA FHIR format](https://bcda.cms.gov/guide.html#fhir-types) to the 
[Tuva Claims Data Model](https://docs.tuvahealth.com/). 
*Note: Some additional staging is necessary to combine/separate the mapped data 
into the Tuva models Eligibility, Medical Claim, and Pharmacy Claim.*

To execute the script, run `py .\BCDAConnector.py` while in this folder.

The sample FHIR data can be downloaded from the BCDA Sandbox by using 
their [API](https://bcda.cms.gov/guide.html#try-the-api). 


### Configuration Notes

- The eligibility data is separated into the FHIR resources Coverage 
  and Patient. These will need to be combined before running through the 
  Tuva Project.  
- Medical, DME, and pharmacy claims are all in the same resource 
  Explanation of Benefit. These are being mapped to the Tuva Medical Claim
  and Pharmacy Claim models. These will need to be separated before running 
  through the Tuva Project.
- ConfigExplanationOfBenefit is parsing the objects at the "item" level.
