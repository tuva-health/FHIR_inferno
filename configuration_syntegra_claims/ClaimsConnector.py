# this is just so you can import parseFhir from the parent folder
# if parseFhir.py is in the same folder as claimsConnector, or if its in a folder in Path, this isnt needed
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parseFhir

parseFhir.parse( r"config\configpatient.ini")
parseFhir.parse( r"config\configcoverage.ini")
parseFhir.parse( r"config\configdme.ini")
parseFhir.parse( r"config\configprofessional.ini")
parseFhir.parse( r"config\configInstitutional.ini")