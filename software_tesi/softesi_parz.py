import spacy
from spacy.lang.en import English
from spacy.symbols import VERB,AUX,PART,PRON,ADJ,NOUN,ADV 
from spacy import displacy
from nltk.corpus import wordnet as wn
from pathlib import Path
from gspan_mining.config import parser
from gspan_mining.main import main

# caricamento nlp
nlp = spacy.load("en_core_web_lg")

''' sent = input("Inserisci il testo: ")
doc = nlp(sent)

text = open("756-6658-1-PB.pdf").read()'''

# inserimento di un testo da input

text = "We recognized the problem and took care of it. Let's go, after to be start!"
#text = "What's happened to me? he thought. It wasn't a dream."
#text = "The remaining part of this paper is organized as follows. Section 3 describes the methodology for building graph structures from text. Section 4 presents how graph patterns can be extracted from these graph representations. Section 5 describes how graph patterns map back to a graph representation corresponding to a given event pair."
#text = "Luca didn't want to go to school. He hadn't done homeworks."
#text = "In ancient Rome, some neighbors live in three adjacent houses. In the center is the house of Senex, who lives there with wife Domina, son Hero, and several slaves, including head slave Hysterium and the musical's main character Pseudolus. A slave belonging to Hero, Pseudolus wishes to buy, win, or steal his freedom. One of the neighboring houses is owned by Marcus Lycus, who is a buyer and seller of beautiful women; the other belongs to the ancient Erronius, who is abroad searching for his long-lost children (stolen in infancy by pirates). One day, Senex and Domina go on a trip and leave Pseudolus in charge of Hero. Hero confides in Pseudolus that he is in love with the lovely Philia, one of the courtesans in the House of Lycus (albeit still a virgin)."

doc = nlp(text)

# funzione che, per ogni frase, fonde in un solo due token separati da un apostrofo 
def merge_span(sent):
	i = 0	
	while (i < len(sent) - 1):
		span = sent[i:i+2]
		with doc.retokenize() as retokenizer:
			if (sent[i].whitespace_ == ''):
				if (((sent[i].pos == AUX) and (sent[i+1].pos == PART)) or ((sent[i].pos == VERB) and (sent[i+1].pos == PRON))):
					retokenizer.merge(span)
		i = i + 1
	
	return sent 

# funzione che, per ogni frase, data la lista degli rispettivi enablement, crea le liste: 
# l_tok, contenente sottoliste di ogni token e suo successivo, 
# l_tag, contenente sottoliste dei POS di ogni token e del suo successivo,
# attr, contenente le sottoliste di l_tok riguardanti gli enablement
def next_edges(sent, enabl):
	l_tok = []
	l_tag = []
	attr = []
	i = 0
	while (i < len(sent) - 1):
		l_tok.append([sent[i], sent[i+1]])
		l_tag.append([str(sent[i].tag_), str(sent[i+1].tag_)])	
		i = i + 1
	
	for j in enabl:
		a, b = j
		for k in l_tok:
			if ((k[0] == a) and ((k in attr) == False)):
				attr.append(k)
	
	print("TOKEN AND TOKEN NEXT LIST:")	
	print(l_tok,'\n')
	print("TOKEN'S TAG AND TOKEN'S TAG NEXT LIST:")
	print(l_tag,'\n')
	print("ENABLEMENT'S TUPLE LIST:")
	print(attr,'\n')

	return attr

# funzione che, per ogni token della frase considerata, esegue WSD per ottenere i suoi synset antenati nella sua catena di ipernimia; i token vengono distinti in base al POS; dopodiche', per ogni synset, vengono estratti i ripsettivi lemmi e chiavi, raggruppati in tuple di liste
def wsd_hyper(sent):
	for t in sent:
		wsd = []
		wsd = wn.synsets(t.text)
		if (wsd != []):
			if (t.pos == VERB):
				wsd = wn.synsets(t.text, pos=wn.VERB)
			if (t.pos == NOUN):
				wsd = wn.synsets(t.text, pos=wn.NOUN)
			if (t.pos == ADJ):
				wsd = wn.synsets(t.text, pos=wn.ADJ)
			if (t.pos == ADV):
				wsd = wn.synsets(t.text, pos=wn.ADV)

			print("['{0}'] : {1} \n".format(t.text, wsd))
			
			for ss in wsd:
				ss = ss.hypernym_paths()
				print(ss,'\n')
				for l in ss:
					lem = [i.lemmas() for i in l]
					print("LEMMAS FOR ANYONE SYNSET:")
					for j in lem:
						keys = [k.key() for k in j]
						print((j,keys),'\n')
						
# funzione che, per ogni frase, estrae e stampa i suoi event e enablement, restituendo quest'ultimi 
def detect_events(sent):
	verbs = []
	enabl = []
	 
	for match in sent:
		if (match.pos == VERB):
			verbs.append(match)
			if (match != match.head) and (match.head.pos == VERB): 
				enabl.append((match.head, match))
						
	print("VERB:")
	print(verbs,'\n')
	print("ENABLEMENT:")
	print(enabl,'\n')
	
	return enabl

# funzione che restituisce un file contenente i dati input per l'esecuzione dell'algoritmo gSpan, richiamando anche la lista attr
def parse_tree(sent, enabl, file_in, s):
	
	if (s == 1):
		sub_graph = open("/Users/filippo/Desktop/UNIMI/Tesi/"+file_in, "w")
	else:
		sub_graph = open("/Users/filippo/Desktop/UNIMI/Tesi/"+file_in, "a")		
	
	attr = next_edges(sent, enabl)
	
	ind = 0
	for i in enabl:
		j,k = i
		t = "t # "
		sub_graph.write(t+str(ind))
		sub_graph.write("\n")
		sub_graph.write("v 0 "+j.text)
		sub_graph.write("\n")
		for w in attr:
			if (w[0] == j):
				sub_graph.write("v 1 "+str(w[0].tag_))
				sub_graph.write("\n")
				sub_graph.write("v 2 "+str(w[1].tag_))
				sub_graph.write("\n")
		sub_graph.write("v 3 "+k.text)
		sub_graph.write("\n")
		sub_graph.write("e 0 3 enabl")
		sub_graph.write("\n")	
		sub_graph.write("e 1 0 pos")
		sub_graph.write("\n")
		sub_graph.write("e 1 2 next")
		sub_graph.write("\n")
				
		ind = ind + 1

	return sub_graph

if __name__ == '__main__':
	s = 1	# indice riguardante la frase considerata in ordine di lettura
	stc = 1	# indice riguardante il file utilizzato per la visualizzazione della frase con displacy
	
	for sent in doc.sents:
		# stampa token di ogni frase
		print("SENTENCE TOKEN ATTRIBUTES:")
		for token in sent:
			print([token.text, token.lemma_, token.pos_, token.tag_, token.dep_], '\n')
		
		print("SENTENCE:")
		print(sent,'\n')

		sent = merge_span(sent)

		print([t for t in sent],'\n')

		enabl = detect_events(sent)

		wsd_hyper(sent)

		# il file di input per gSpan viene inizializzato nel corpo principale del programma e richiamato in parse_tree
		file_in = "inputgSpan_sentence.data"
		sub_graph = parse_tree(sent, enabl, file_in, s)
		
		# esecuzione file di output
		svg = displacy.render(sent, style="dep")
		
		file_name = "sentence"+str(stc)+".svg"
		output_path = Path("/Users/filippo/Desktop/UNIMI/Tesi/"+file_name)
		output_path.open("w", encoding="utf-8").write(svg)
		
		stc = stc + 1
		s = s + 1

	# il file viene chiuso esternamente alla funzione per evitare sovrascritture dei dati di input 
	sub_graph.write("t # -1")	
	sub_graph.write("\n")		
	sub_graph.close()

	# richiamo gSpan e visualizzazione grafi, per ogni enablement del doc considerato
	args_str = '-d True /Users/filippo/Desktop/UNIMI/Tesi/inputgSpan_sentence.data'
	FLAGS, _ = parser.parse_known_args(args=args_str.split())
	gs = main(FLAGS)

	for g in gs.graphs.values():
		g.plot()
		

	

