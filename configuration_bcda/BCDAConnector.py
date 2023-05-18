# this is just so you can import parseFhir from the parent folder
# if parseFhir.py is in the same folder as claimsConnector, or if its in a folder in Path, this isnt needed
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import parseFhir

parseFhir.parse( r"config\configCoverage.ini")
parseFhir.parse( r"config\configExplanationOfBenefit.ini")
parseFhir.parse( r"config\configPatient.ini")
