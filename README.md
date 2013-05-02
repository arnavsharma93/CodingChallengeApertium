CodingChallengeApertium
=======================
===================================================================
It has the coding challenge for Apertium's GSoC project Improved Bilingual Dictionary Induction.
===================================================================

Files:
============
1. generate-bidix-templates-arnav.py --> 
======================
Contains the script /apertium-forms-server/generate-bidix-templates.py written in Python3/ElementTree. It generates lesser duplicate templates than the original and also takes care of the <g> tag. 
Usage:: python  generate-bidix-templates-arnav.py   <monodix left> <bidix> <monodix right> [-p : optional to show the processing]
2. outputTemplate.xml -->
======================
Contains the output of the script run on fr-es language pair.
3. en-es.parallelCorpus.200 --> 
======================
Contains the first 200 lines of the word aligned and tagged EuroParl parallel corpus of English-Spanish. Apertium's tagger was used to tag the data and Giza++ was used to generate the word aligned parallel corpus.
