# This is just so you can import parseFhir from the parent folder
# if parseFhir.py is in the same folder as connector this isn't needed.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the parser script
import parseFhir

# Update config paths as needed
parseFhir.parse(r"config/configCoverage.ini")
parseFhir.parse(r"config/configPatient.ini")
parseFhir.parse(r"config/configExplanationOfBenefit.ini")
