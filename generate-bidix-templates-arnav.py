#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# from xml.dom.ext.reader import Sax2
from xml.dom.ext import PrettyPrint
import sys, string, codecs, xml, os, re, md5, cStringIO 
import xml.etree.ElementTree as ET


categories = ['n', 'adj', 'np']

if len(sys.argv) < 4: 
	print('Usage: python generate-bidix-templates.py <left monodix> <bidix> <right monodix> [-p:processing <optional>]');
	sys.exit(-1);

left_file = sys.argv[1]
bidix_file = sys.argv[2];
right_file = sys.argv[3];
dep = 0
if(len(sys.argv) == 5):
	processing = sys.argv[4][1]
	if(processing == 'p'):
		dep = 1
	else:
		print('Usage: python generate-bidix-templates.py <left monodix> <bidix> <right monodix> [-p:processing <optional>]');
		sys.exit(-1)

#Get the tree of the input files
left_tree = ET.parse(left_file)
right_tree = ET.parse(right_file)
bidix_tree = ET.parse(bidix_file)


def generate_monodix_hash(tree):
	#get the root node
	root = tree.getroot()

	paradigms={};

	for paradigm in root.iter('pardef'):#iterate recursively inside root to look for <pardef>
		current_paradigm = paradigm.attrib['n'];#<pardef n="k"> k = current_paradigm 
		current_category = '';
		ignoring = 1;
		for tag in categories:
			needle = '.*__' + tag + '$';#re search inside the current_paradigm to look for tag 
			patron = re.compile(needle);
			if(patron.match(current_paradigm)):
				current_category = tag; #if found assign the tag
				ignoring = 0;


		if ignoring == 1:
			continue

		paradigm_hash = []
	
		for entrada in paradigm.iter('e'): #iterate recursively inside paradigm element to look for <e> and assign it to entrada 
			if 'r' in entrada.attrib.keys(): # if r is an attribute
				restriction = entrada.attrib['r'] #<e r = "k"> k = restriction
			else:
				restriction = ''

			symbols = ''

			for symbol in entrada.iter('s'):#iterate recursively inside entrada element to look for <s>  and assign it to symbol
				if 'n' in symbol.attrib.keys():
					symbols = symbols + symbol.attrib['n'] + '.' 
			
			paradigm_hash.append((restriction,symbols))
		#calculate md5
		m = md5.new()
		m.update(str(set(paradigm_hash)))
		
		#make key
		key = current_category + '.' + m.hexdigest()
		
		#initialize the dict
		if key not in paradigms:
			paradigms[key] = []
		
		if dep == 1:
			print >> sys.stderr, 'generate_monodix_hash: ' + current_category + '.' + m.hexdigest() , current_paradigm;
		
		paradigms[key].append(current_paradigm)
	
	return paradigms #returns the dict

def generate_entry_list(tree, paradigms):
	root = tree.getroot()# get root of the tree
	entries = {}
	for section in root.iter('section'): #iterate recursively inside root to look for <section> and assign it to section
		if section.attrib['id'] == 'main': #if <section id = "main">
			for entry in section.iter('e'):#look for <e> inside symbol and assign it to entry
				lema = ''				
				if "lm" in entry.attrib.keys(): #if lm among attributes of <e> 
					lema = entry.attrib['lm']  # <e lm="k"> ; lema = k
				
				pars = entry.findall('./par') #find <par> among the childrens of entry
				if len(pars) >= 1:
					par = pars[0].attrib['n'] # <par n="k">; par = k
					#NOTE par has an item "probj_dem__prn" here which is there in the given script as well. 
					#Its not there if par is defined in the manner given below. 
 				# for pars in entry.iter('par'):
				# 	par = pars.attrib['n']

					for hash in paradigms:
						if par in paradigms[hash]:
							if lema not in entries:
								entries[lema] = {} #init entries

							category = hash.split('.')[0]; 
							entries[lema][category] = hash #entries[ox][n] = n.9588f1fbcc06f14e70ac3801be795d50
							if dep == 1:
								print >> sys.stderr, 'generate_entry_list:', lema + '.' + category, ';', par, ';',  hash;

	return entries


def retrieve_lemma(entry, side):
#Function behaviour is a little different that the one in the given script 
	full_lemma = ''
	temp_str = ''
	for text in side[0].itertext(): # iterate over all the text in side[0] element
		if temp_str == '':
			temp_str = text
		else:
			temp_str = temp_str + ' ' + text
		
	full_lemma = full_lemma + temp_str 	
	return full_lemma # return the concatenated lemma; given script does not return full lemmas in case of <g> tag

def retrieve_category(entry, side): 
	for kid in side[0].findall('.//s'):#find <s> in whole the tree under side[0]
		return kid.attrib['n'] # <s n='k'>; k is returned
	
	return ''
##Extra function needed because ElementTree has no pretty print functon. It was needed to get uniform formatting to compare two elements
def prettyPrintET(Node):
  	#reader = Sax2.Reader()
    #docNode = reader.fromString(ET.tostring(Node, encoding="utf-8"))
    tmpStream = cStringIO.StringIO()
    PrettyPrint(Node, stream=tmpStream)
    return tmpStream.getvalue()

#comapare the two nodes, if same return true, else return false
def equal_entries(entry1, entry2):
	equal = False
	entrada1 = prettyPrintET(entry1) 
	entrada2 = prettyPrintET(entry2)
	if dep == 1:
		print >> sys.stderr, '--'
		print >> sys.stderr, 'entrada1: ', entrada1
		print >> sys.stderr, 'entrada2: ', entrada2
		print >> sys.stderr, '--'

	
	if entrada1 == entrada2:
		equal = True
		return equal

	if dep == 1:
		print >> sys.stderr, equal
		print >> sys.stderr, '--'

	return equal;

#look if the entry already exists
def entry_exists(existing, new):
	existing = '<doc>' + existing.encode('utf-8') + '</doc>'
	new = '<doc>' + new + '</doc>'
	
	if dep == 1:	
		print >> sys.stderr, ' %%%%%%%%%%%%%% '
		print >> sys.stderr, ' %% existing %% '
		print >> sys.stderr, ' ' , existing
		print >> sys.stderr, ' %% new %% ' 
		print >> sys.stderr, ' ' , new
		print >> sys.stderr, ' %%%%%%%%%%%%%% '

	existing_doc = ET.fromstring(existing)
	new_doc = ET.fromstring(new)
	for node in existing_doc.iter('e'): # iterate to find <e>, assign it to node
		for new_node in new_doc.iter('e'): #iterate to find <e>, assign to new_node
			if equal_entries(node, new_node) == True:
				return True 

	return False

#making templates
def generate_templates(tree, left_entries, right_entries):
	root = tree.getroot() #get root of the tree/bidix file
	template_matrix = {}
	for entry in root.findall('./section[@id="main"]/e'):
		#remove attributes a, c, srl, slr, alt from <e>
		if 'a' in entry.attrib.keys():
			del(entry.attrib['a'])
		if 'c' in entry.attrib.keys():
			del(entry.attrib['c'])
		if 'srl' in entry.attrib.keys():
			del(entry.attrib['srl'])
		if 'slr' in entry.attrib.keys():
			del(entry.attrib['slr'])
		if 'alt' in entry.attrib.keys():
			del(entry.attrib['alt'])

		if len(entry.findall('.//i')) > 0:
			continue
		#find all the <l> and <r> nodes inside a particular
		left = entry.findall('.//l') 
		right = entry.findall('.//r')

		#retrieve lemmma inside <l> and <r>
		left_lemma = retrieve_lemma(entry, left)
		right_lemma = retrieve_lemma(entry, right)

		#retrieve symbol inside <l> and <r>
		left_symbol = retrieve_category(entry, left)
		right_symbol = retrieve_category(entry, right)


		if left_symbol == '' or right_symbol == '':
			continue

		#if symbol not equal to 'n', 'adj', 'np'	
		if left_symbol not in categories or right_symbol not in categories:
			continue

		#create left_hash and right_hash
		if left_lemma not in left_entries:
			continue

		try:
			left_hash = left_entries[left_lemma][left_symbol]
		except:
			continue

		if right_lemma not in right_entries:
			continue

		try:
			right_hash = left_entries[left_lemma][left_symbol]
		except:
			continue

		#initialize template_matrix
		if left_hash not in template_matrix:
			template_matrix[left_hash] = {}

		if right_hash not in template_matrix[left_hash]:
			template_matrix[left_hash][right_hash] = {}

		#eg : bidix_hash = iawn.adj.5ffa88a1f2d70562b49c78b550ba4060:OK.adj.5ffa88a1f2d70562b49c78b550ba4060
 	
		bidix_hash = left_lemma + '.' + left_hash + ':' + right_lemma + '.' + right_hash

		#eg:<e><p><l>iawn<s n="adj" /></l><r>OK<s n="adj" /></r></p></e> 
		entrada = ET.tostring(entry, encoding='utf-8').strip()
		# entrada = entrada.decode('utf-8')
		entrada = re.sub(r'<b *?/>', ' ', entrada)
		#case not taken care of in the script given, multiwords
		entrada = re.sub(r'<g *?>', '', entrada)
		entrada = re.sub(r'</g *?>', '', entrada)
		##
		#eg of entrada now: <e><p><l>nos Wener<s n="n" /><s n="f" /></l><r>Friday night<s n="n"/></r></p></e>

		entrada = re.sub(left_lemma, 'lemma1', entrada)
		entrada = re.sub(right_lemma,'lemma2', entrada)
		# entrada = entrada.encode('utf-8')

		#eg of entrada now: <e><p><l>lemma1<s n="n" /><s n="f" /></l><r>lemma2<s n="n"/></r></p></e>



		#create template matrix
		#eg of template_matrix: 
		#template_matrix[left_hash][right_hash][bidix_hash] = <e><p><l>lemma1<s n="np" /><s n="top"/><s n="f"/></l><r>lemma1<s n="np"/><s n="top" /></r></p></e>
		if bidix_hash not in template_matrix[left_hash][right_hash]:
			template_matrix[left_hash][right_hash][bidix_hash] = ''
			template_matrix[left_hash][right_hash][bidix_hash] = template_matrix[left_hash][right_hash][bidix_hash].decode('utf-8') + '\n' + entrada.decode('utf-8')
		else:
			if entry_exists(template_matrix[left_hash][right_hash][bidix_hash], entrada) != True: #{
				template_matrix[left_hash][right_hash][bidix_hash] = template_matrix[left_hash][right_hash][bidix_hash] + '\n' +  entrada.decode('utf-8')

		# print(template_matrix[left_hash][right_hash][bidix_hash].encode('utf-8').strip())
	
	templates = {}
	#make templates
	for left in template_matrix: 
		for right in template_matrix[left]: 
			for bidix in template_matrix[left][right]: 
				col = bidix.split(':')
				hash_left = col[0].split('.')[1] + '.' + col[0].split('.')[2]
				hash_right = col[1].split('.')[1] + '.' + col[1].split('.')[2]
				hash = hash_left + ':' + hash_right
				comment = col[0].split('.')[0] + '.' + col[0].split('.')[1] + ':' + col[1].split('.')[0] + '.' + col[1].split('.')[1]

				if left not in templates: 
					templates[left] = {}

				if right not in templates[left]: 
					templates[left][right] = ''


				templates[left][right] = template_matrix[left][right][bidix] + '<!-- ' + comment + ' -->'
				templates[left][right] = templates[left][right]
	print('<templates>')
	print('')
	for left in templates: #{
		print('  <left id="' + left + '">')
		for right in templates[left]: #{
			print('    <right id="' + right + '">')
			print('      <template>')
			print(templates[left][right].encode('utf-8'))
			print('      </template>')
			print('    </right>')
		print('  </left>')
		print('')
	print('</templates>')
	return templates

#main function calls
left_paradigms = generate_monodix_hash(left_tree)
right_paradigms = generate_monodix_hash(right_tree)

left_entries = generate_entry_list(left_tree, left_paradigms)
right_entries = generate_entry_list(right_tree, right_paradigms)

templates = generate_templates(bidix_tree, left_entries, right_entries)


