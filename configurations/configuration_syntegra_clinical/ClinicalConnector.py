# this allows us to import the file when it is in the parent of the working directory.
# if parseFhir.py is in the same directory as ClinicalConnector.py or its in a location
# listed in the path environmental variable, this wouldn't be needed.
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parseFhir


parseFhir.parse( r"config\configAllergy.ini")
parseFhir.parse( r"config\configCondition.ini")
parseFhir.parse( r"config\configEncounter.ini")
parseFhir.parse( r"config\configLocation.ini")
parseFhir.parse( r"config\configLab.ini")
parseFhir.parse( r"config\configMedication.ini")
parseFhir.parse( r"config\configPatient.ini")
parseFhir.parse( r"config\configPractitioner.ini")
parseFhir.parse( r"config\configProcedure.ini")
parseFhir.parse( r"config\configVitalSign.ini")
parseFhir.parse( r"config\configBPDias.ini")
parseFhir.parse( r"config\configBPSys.ini")