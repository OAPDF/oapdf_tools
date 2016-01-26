# oapdftools
Tools for OAPDF Project

> Need python module: 

- requests : need it to load web and stop redirection.  
Install: `pip install requests`
- pdfminer : need it to parse pdf file.
Install: `pip install pdfminer`

## Scripts for DOI processing.

## Scripts for endnote library processing.

- [modifyXML.py](#file-modifyxml-py): To deal with nonsense chars in "Notes" column, reserve Time Cited information; modify improper doi format (remove DOI:, litter case)
- [prepareDOI.py](#file-preparedoi-py): To pre-process doi number for getPDF.py script. 
- [getPDF.py](#file-getpdf-py): Search PDF for endnote XML DOI records based on scihub.  
Save the doi number in a file (one doi per line) and use the file as script input.  
Each file save as "10.1021_ci111111a.pdf" in current directory. You have to move the valid file to "Done" Directory and use addPDF.py.
- [addPDF.py](#file-addpdf-py): Put found PDF in "Done" Directory, Some pdf don't want to search anymore in "Accept".   
Give a endnote XML as input. Move the PDF to a directory based on doi-paper number. A new xml file will be generated.  
Move all the directories in "Done" to "Endnote library.Data/PDF" and import the new xml file.  You may delete old records firstly.
- [checkdone.sh](#file-checkdone-sh): Use input file in getPDF.py (saving doi numbers) as input  
and generated a "not.txt" file saving doi not found.
