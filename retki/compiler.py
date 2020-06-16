# Retki
# Copyright (C) 2019 Iikka Hauhio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import readline, os, sys, argparse, traceback, time
import re
import itertools
from suomilog.patternparser import ERROR_STACK, setDebug, PatternRef, Grammar, groupCauses
from suomilog.finnish import tokenize, CASES, addNounToDictionary
from .language import *
from .tokenutils import *

GRAMMAR = Grammar()

GRAMMAR_STACK = [GRAMMAR]
STACK_FRAMES = [0]

def pgl(*a, **d):
	GRAMMAR_STACK[-1].parseGrammarLine(*a, **d)

def getCombinedGrammar():
	combined_grammar = Grammar()
	for grammar in GRAMMAR_STACK:
		combined_grammar.update(grammar)
	return combined_grammar

def pushGrammar(grammar, new_frame=True):
	if new_frame:
		STACK_FRAMES.append(len(GRAMMAR_STACK))
		GRAMMAR_STACK.append(grammar)
	else:
		GRAMMAR_STACK.insert(STACK_FRAMES[-1], grammar)

def popGrammar():
	global GRAMMAR_STACK
	GRAMMAR_STACK = GRAMMAR_STACK[:STACK_FRAMES.pop()]

# Villikortit

class AnyPattern:
	def __init__(self, allow_empty, required_bits=set()):
		self.allow_empty = allow_empty
	def __repr__(self):
		return "AnyPattern()"
	def toCode(self):
		if self.allow_empty:
			return "<pattern that matches all strings without punctuation>"
		else:
			return "<pattern that matches all non-empty strings without punctuation>"
	def match(self, grammar, tokens, bits):
		bits_found = False
		for token in tokens:
			if token.token in [".", ",", ":", "!", "?", "[", "]"]:
				return []
			if any(altbits >= bits for _, altbits in token.alternatives):
				bits_found = True
		
		if bits and not bits_found:
			return []
		
		return [[lambda: tokens, " ".join([t.token for t in tokens])]]
	def allowsEmptyContent(self):
		return self.allow_empty

GRAMMAR.patterns["*"] = [
	AnyPattern(False)
]

GRAMMAR.patterns["**"] = [
	AnyPattern(True)
]

class WordPattern:
	def __repr__(self):
		return "WordPattern()"
	def toCode(self):
		return "<pattern that matches any single token>"
	def match(self, grammar, tokens, bits):
		if len(tokens) != 1 or bits and not any(altbits >= bits for _, altbits in tokens[0].alternatives):
			return []
		return [[lambda: tokens[0], tokens[0].token]]
	def allowsEmptyContent(self):
		return False

GRAMMAR.patterns["."] = [
	WordPattern()
]

class StringContentPattern:
	def __init__(self, create_alternative):
		self.create_alternative = create_alternative
	def __repr__(self):
		return "StringContentPattern()"
	def toCode(self):
		return "<pattern that matches all strings without quote marks>"
	def match(self, grammar, tokens, bits):
		for token in tokens:
			if token.token == '"':
				return []
		string = ""
		string_tokens = [[]]
		subs = []
		current_subs = None
		capitalizeds = []
		quote = False
		for token in tokens:
			if current_subs is not None:
				if token.token == "]":
					if not quote or string[-1] != '"':
						string += " "
					string += "%s"
					alts = grammar.matchAll(current_subs, "EXPR-CASE", set())
					subs.append(alts)
					capitalizeds.append(current_subs[0].token.capitalize() == current_subs[0].token if current_subs else False)
					current_subs = None
				else:
					current_subs.append(token)
				continue
			if token.token == "[":
				current_subs = []
				string_tokens.append([])
			elif token.token in [".", ":", ",", ";", "?", "!"]:
				string += token.token
				string_tokens[-1].append(token)
			else:
				if not quote or (string[-1] != '"' and token.token != "'"):
					string += " "
				if token.token == "%":
					string += "%%"
				elif token.token == "'":
					string += '"'
					quote = not quote
				else:
					string += token.token
				string_tokens[-1].append(token)
		string = string.strip()
		ans = []
		for alternative in itertools.product(*subs):
			ans.append(self.create_alternative(string, string_tokens, alternative, capitalizeds))
		return ans
	def allowsEmptyContent(self):
		return True

def createStringLiteralAlternative(string, string_tokens, alternative, capitalizeds):
	def f():
		subs = []
		for (expr_f, _), capitalized in zip(alternative, capitalizeds):
			expr, case = expr_f()
			subs.append("%s.asString(case=%s, capitalized=%s)" % (expr, repr(case), repr(capitalized)))
		if len(subs) > 0:
			return "(" + repr(string) + " % (" + ", ".join(subs) + ("," if len(alternative) == 1 else "") + "))"
		else:
			return repr(string)
	return [
		f,
		string % tuple([p[1] for p in alternative])
	]

GRAMMAR.patterns["STR-CONTENT"] = [
	StringContentPattern(createStringLiteralAlternative)
]

GRAMMAR.addCategoryName("STR-CONTENT", "merkkijono")

CARDINALS = ["nolla", "yksi", "kaksi", "kolme", "neljä", "viisi", "kuusi", "seitsemän", "kahdeksan", "yhdeksän", "kymmenen"]

class NumberPattern:
	def __repr__(self):
		return "NumberPattern()"
	def toCode(self):
		return "<pattern that matches any number>"
	def match(self, grammar, tokens, bits):
		if len(tokens) != 1:
			return []
		for bf, altbits in tokens[0].alternatives:
			if bits <= altbits:
				if bf in CARDINALS:
					return [[lambda: CARDINALS.index(bf), bf]]
				elif re.fullmatch(r"[0-9]+", bf):
					return [[lambda: int(bf), bf]]
		return []
	def allowsEmptyContent(self):
		return False

GRAMMAR.patterns["N"] = [
	NumberPattern()
]

# Apufunktio

def orTrue(code):
	return "(" + code + " or True)"

# Nimiavaruudet

NAMESPACES = {}
NAMESPACE_STACK = [""]

def openNamespace(name=None):
	if not name:
		pushGrammar(Grammar())
		NAMESPACE_STACK.append("anonymous-" + str(nextCounter("openNamespace")))
		return
	
	name_str = tokensToString(name, rbits={"nimento"})
	name_code = nameToCode(name, rbits={"nimento"})
	
	if name_str not in NAMESPACES:
		NAMESPACES[name_str] = Grammar()
		pgl(".NAMESPACE-DEF ::= Muista %s . -> remember %s" % (name_code, name_str), FuncOutput(lambda: rememberNamespace(name_str)))
	
	pushGrammar(NAMESPACES[name_str])
	NAMESPACE_STACK.append(name_str)

def rememberNamespace(name_str):
	pushGrammar(NAMESPACES[name_str], new_frame=False)

def closeNamespace():
	popGrammar()
	NAMESPACE_STACK.pop()

pgl(".NAMESPACE-DEF ::= Avaa nimiavaruus . -> open namespace", FuncOutput(openNamespace))
pgl(".NAMESPACE-DEF ::= Avaa nimiavaruus ( .* ) . -> open namespace $1", FuncOutput(openNamespace))
pgl(".NAMESPACE-DEF ::= Sulje nimiavaruus . -> close namespace", FuncOutput(closeNamespace))

pgl(".DEF ::= .NAMESPACE-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("NAMESPACE-DEF", "nimiavaruuskäsky")

# Substantiivit

NOUNS = []

def addNoun(token):
	addNounToDictionary(token.token)
	NOUNS.append(token.token)

pgl(".NOUN-DEF ::= \" .. \" on substantiivi . -> noun $1", FuncOutput(addNoun))

pgl(".DEF ::= .NOUN-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("NOUN-DEF", "substantiivimääritys")

# Luokat

def defineClass(name, superclass, name_rbits={"yksikkö", "nimento"}):
	name_str = tokensToString(name, rbits=name_rbits)
	name_code = nameToCode(name, rbits=name_rbits)
	pattern = lambda bits: nameToCode(name, bits=bits, rbits=name_rbits)
	
	if name_str in CLASSES:
		raise Exception("redefinition of class " + name_str)
	
	rclass = RClass(name_str, superclass, name)
	
	for clazz in reversed(superclass.superclasses()) if superclass else []:
		for fname in clazz.fields:
			rclass.fields[fname] = clazz.fields[fname].copy()
	
	pgl(".CLASS-PATTERN-%d ::= %s -> %s" % (rclass.id, name_code, name_str), FuncOutput(lambda: RPattern(rclass=rclass)))
	GRAMMAR_STACK[-1].addCategoryName("CLASS-PATTERN-WITH-ADV-%d" % (rclass.id,), name_str + "-käsitteen hahmo")
	GRAMMAR_STACK[-1].addCategoryName("CLASS-PATTERN-%d" % (rclass.id,), name_str + "-käsitteen hahmo")
	GRAMMAR_STACK[-1].addCategoryName("PATTERN-%d" % (rclass.id,), name_str + "-käsitteen arvon hahmo")
	
	pgl(".CLASS-PATTERN ::= .CLASS-PATTERN-%d{$} -> $1" % (rclass.id,), identity)
	pgl(".CLASS-PATTERN ::= .CLASS-PATTERN-WITH-ADV-%d{$} -> $1" % (rclass.id,), identity)
	for clazz in rclass.superclasses():
		pgl(".CLASS-%d ::= %s -> %s" % (clazz.id, name_code, name_str), FuncOutput(lambda: rclass))
		pgl(".PATTERN-%d ::= %s -> %s" % (clazz.id, name_code, name_str), FuncOutput(lambda: RPattern(rclass=rclass)))
		if clazz is not rclass:
			for _, group_strs, group_codes in clazz.bit_groups:
				for group_str, group_code in zip(group_strs, group_codes):
					addBitPatternPhrase(rclass, rclass, group_code, group_str, set(group_strs))
					addBitClassPatternPhrase(rclass, group_code, group_str, set(group_strs))
			for attributePhraseAdder in clazz.attributePhraseAdders:
				attributePhraseAdder(rclass, rclass)
	pgl(".CLASS ::= %s -> %s" % (name_code, name_str), FuncOutput(lambda: rclass))
	
	def addClassCasePhrase(case):
		pgl(".CLASS-CASE-%d ::= %s -> $1:%s" % (rclass.id, pattern({case}), case), FuncOutput(lambda: case))
		GRAMMAR_STACK[-1].addCategoryName("CLASS-CASE-%d" % (rclass.id,), name_str + "-käsitteen nimi "+case+"-muodossa")
		pgl(".PATTERN-CASE-%d ::= .PATTERN-%d{%s,yksikkö} -> $1:%s" % (rclass.id, rclass.id, case, case), FuncOutput(lambda p: (p, case)))
		GRAMMAR_STACK[-1].addCategoryName("PATTERN-CASE-%d" % (rclass.id,), name_str + "-käsitteen arvon hahmo "+case+"-muodossa")

	for case in CASES:
		addClassCasePhrase(case)
	
	def addMapFieldDefPattern(key_case, is_pre):
		pgl(".MAP-FIELD-DEF ::= Kutakin %s kohden .CLASS{ulkoolento} voi olla %s se{%s} %s %s kutsuttu .CLASS{nimento} . -> $1.$2 : {$4}" % (
			pattern({"osanto", "yksikkö"}),
			".**" if is_pre else "",
			key_case,
			pattern({key_case, "yksikkö"}),
			".**" if not is_pre else ""
		), FuncOutput(lambda *p: defineMapField(rclass, key_case, is_pre, *p, case="tulento")))
	
	for key_case in CASES:
		for is_pre in [True, False]:
			addMapFieldDefPattern(key_case, is_pre)
	
	for clazz in rclass.superclasses():
		pgl(".EXPR-%d ::= viimeksi luotu{$} .CLASS-PATTERN-%d{$} -> last created $1" % (clazz.id, rclass.id),
			FuncOutput(lambda pattern: "searchLastObject(" + pattern.toPython() + ")"))

		pgl(".EXPR-%d ::= satunnainen{$} .CLASS-PATTERN-%d{$} -> random $1" % (clazz.id, rclass.id),
			FuncOutput(lambda pattern: "searchRandomObject(" + pattern.toPython() + ")"))
	
	GRAMMAR_STACK[-1].addCategoryName("EXPR-%d" % (rclass.id,), name_str + "-tyyppinen lauseke")

	pgl(".COPY-DEF ::= On .N .EXPR-%d{yksikkö,osanto} . -> copy $*" % (rclass.id, ),
		FuncOutput(lambda n, obj: eval(obj).createCopies(n)))
	
	return rclass

pgl(".CLASS-DEF ::= .* on käsite . -> class $1 : asia", FuncOutput(lambda x: defineClass(x, asia)))
pgl(".CLASS-DEF ::= .* on .CLASS{omanto} alakäsite . -> class $1 : $2", FuncOutput(defineClass))
pgl(".DEF ::= .CLASS-DEF -> $1", identity)

GRAMMAR_STACK[-1].addCategoryName("CLASS-PATTERN", "käsitteen hahmo")
GRAMMAR_STACK[-1].addCategoryName("CLASS-DEF", "luokkamääritys")
GRAMMAR_STACK[-1].addCategoryName("CLASS", "luokan nimi")

# Sijamuodon tunnistamiseen käytettävät säännöt

def addCasePhrases(case):
	pgl(".CLASS-CASE ::= .CLASS{%s} -> $1:%s" % (case, case), FuncOutput(lambda cl: (cl, case)))
	pgl(".EXPR-CASE ::= .EXPR{%s} -> $1:%s" % (case, case), FuncOutput(lambda ex: (ex, case)))
	GRAMMAR_STACK[-1].addCategoryName("CLASS-CASE", "luokan nimi "+case+"-muodossa")
	GRAMMAR_STACK[-1].addCategoryName("EXPR-CASE", "lauseke "+case+"-muodossa")

for case in CASES:
	addCasePhrases(case)

# Ominaisuudet

def definePolyparamField(name_str, field_id, owner, vtype, to_register, pattern, to_get, get_str_output, to_set, set_str_output, defa_pattern, to_set_defa, set_defa_str_output):
	
	for clazz in owner.subclasses():
		to_register(clazz)
	
	for clazz in vtype.superclasses():
		pgl(".EXPR-%d ::= .EXPR-%d{omanto} %s -> %s" % (clazz.id, owner.id, pattern({"$"}), get_str_output), FuncOutput(to_get))
	
	pgl(".FIELD-DEFAULT-DEF-%d ::= .CLASS-%d{omanto} %s on yleensä .EXPR-%d{nimento} . -> %s" % (
		field_id, owner.id, defa_pattern({"yksikkö", "nimento"}), vtype.id, set_defa_str_output
	), FuncOutput(to_set_defa))
	pgl(".DEF ::= .FIELD-DEFAULT-DEF-%d -> $1" % (field_id,), identity)
	GRAMMAR_STACK[-1].addCategoryName("FIELD-DEFAULT-DEF-%d" % (field_id,), name_str+"-kentän oletusarvomääritys")
	
	pgl(".FIELD-VALUE-DEF-%d ::= .EXPR-%d{omanto} %s on .EXPR-%d{nimento} . -> %s" % (
		field_id, owner.id, pattern({"yksikkö", "nimento"}), vtype.id, set_str_output
	), FuncOutput(lambda *p: eval(to_set(*p))))
	pgl(".DEF ::= .FIELD-VALUE-DEF-%d -> $1" % (field_id,), identity)
	GRAMMAR_STACK[-1].addCategoryName("FIELD-VALUE-DEF-%d" % (field_id,), name_str+"-kentän arvon määritys")
	
	pgl(".CMD ::= .EXPR-%d{omanto} %s on nyt .EXPR-%d{nimento} . -> %s" % (
		owner.id, pattern({"yksikkö", "nimento"}), vtype.id, set_str_output
	), FuncOutput(to_set))
	
	pgl(".COND ::= .EXPR-%d{omanto} %s on .EXPR-%d{nimento} -> $1.%s==$2" % (
		owner.id, pattern({"yksikkö", "nimento"}), vtype.id, get_str_output
	), FuncOutput(lambda *p: ('(%s == %s)' % (to_get(*p[:-1]), p[-1]), orTrue(to_set(*p)))))

def defineField(owner, name, vtype, case="nimento"):
	name_str = tokensToString(name, {"yksikkö", case})
	
	counter = nextCounter("RField")
	
	pattern = lambda bits: nameToCode(name, bits, rbits={case, "yksikkö"})
	
	definePolyparamField(
		name_str,
		counter,
		owner,
		vtype,
		lambda clazz: clazz.addField(name_str, RField(counter, name_str, vtype)),
		pattern,
		lambda obj: '%s.get(%s)' % (obj, repr(name_str)),
		"$1.%s" % (name_str,),
		lambda obj, val: '%s.set(%s, %s)' % (obj, repr(name_str), val),
		"$1.%s = $2" % (name_str,),
		pattern,
		lambda clazz, defa: clazz.fields[name_str].setDefaultValue(eval(defa)),
		"$1.%s defaults $2" % (name_str,)
	)

pgl(".FIELD-DEF ::= .CLASS{ulkoolento} on .CLASS{nimento} . -> $1.$3 : $3", FuncOutput(lambda owner, vtype: defineField(owner, vtype.name_tokens, vtype)))
pgl(".FIELD-DEF ::= .CLASS{ulkoolento} on .*{nimento} , joka on .CLASS{nimento} . -> $1.$2 : $3", FuncOutput(defineField))
pgl(".FIELD-DEF ::= .CLASS{ulkoolento} on .*{tulento} kutsuttu .CLASS{nimento} . -> $1.$2 : $3", FuncOutput(lambda *x: defineField(*x, case="tulento")))
pgl(".FIELD-DEF ::= .CLASS{ulkoolento} on .*{tulento} kutsuttu joukko .CLASS{osanto,monikko} . -> $1.$2 : $3", FuncOutput(lambda *x: defineListField(*x, case="tulento")))
pgl(".DEF ::= .FIELD-DEF -> $1", identity)
pgl(".DEF ::= .MAP-FIELD-DEF -> $1", identity)

GRAMMAR_STACK[-1].addCategoryName("FIELD-DEF", "kenttämääritys")
GRAMMAR_STACK[-1].addCategoryName("MAP-FIELD-DEF", "kuvauskenttämääritys")

def defineMapField(key_class, key_case, is_pre, owner, name, vtype, case="nimento"):
	name_str = "m"+str(key_class.id)+"-"+tokensToString(name, rbits={case, "yksikkö"})
	name_code = nameToCode(name, rbits={case, "yksikkö"})
	
	counter = nextCounter("RField")
	
	def createKeyPattern(category):
		return ".%s-%d{%s}" % (category, key_class.id, key_case)
	pre = lambda cat: (createKeyPattern(cat)+" " if not is_pre else "")
	post = lambda cat: (" "+createKeyPattern(cat) if is_pre else "")
	
	definePolyparamField(
		name_str,
		counter,
		owner,
		vtype,
		lambda clazz: clazz.addField(name_str, RField(counter, name_str, vtype, is_map=True)),
		lambda bits: pre("EXPR") + nameToCode(name, bits, rbits={case, "yksikkö"}) + post("EXPR"),
		lambda obj, key: '%s.getMap(%s, %s)' % (obj, repr(name_str), key),
		"$1.%s" % (name_str,),
		lambda obj, key, val: '%s.setMap(%s, %s, %s)' % (obj, repr(name_str), key, val),
		"$1.%s[$2] = $3" % (name_str,),
		lambda bits: pre("CLASS") + nameToCode(name, bits, rbits={case, "yksikkö"}) + post("CLASS"),
		lambda clazz, _, defa: clazz.fields[name_str].setDefaultValue(eval(defa)),
		"$1.%s[$2] defaults $3" % (name_str,)
	)

def defineListField(owner, name, vtype, case="nimento"):
	name_str = "l-"+tokensToString(name, {"yksikkö", case})
	pattern = lambda bits: nameToCode(name, bits, rbits={case, "yksikkö"})
	
	counter = nextCounter("RField")
	
	to_append = lambda val, obj: '%s.appendSet(%s, %s)' % (obj, repr(name_str), val)
	to_remove = lambda val, obj: '%s.removeSet(%s, %s)' % (obj, repr(name_str), val)
	
	pgl(".CMD ::= lisää .EXPR-%d{nimento} .EXPR-%d{omanto} %s . -> $2.%s.append($1)" % (
		vtype.id, owner.id, pattern({"yksikkö", "sisatulento"}), name_str
	), FuncOutput(to_append))
	
	pgl(".CMD ::= poista .EXPR-%d{nimento} .EXPR-%d{omanto} %s . -> $2.%s.append($1)" % (
		vtype.id, owner.id, pattern({"yksikkö", "sisaeronto"}), name_str
	), FuncOutput(to_remove))
	
	for named_code in ["", "( .* )"]:
		pgl(".CMD ::= toista jokaiselle .PATTERN-%d{ulkotulento} %s .EXPR-%d{omanto} %s : -> for each $1 in $2.%s:" % (
			vtype.id, named_code, owner.id, pattern({"yksikkö", "sisaolento"}), name_str
		), FuncOutput(lambda *p: ForParser(name_str, *p)))
		
		pgl(".CMD ::= toista jokaiselle ryhmälle samanlaisia .PATTERN-%d{osanto,monikko} %s .EXPR-%d{omanto} %s : -> for each $1 in $2.%s:" % (
			vtype.id, named_code, owner.id, pattern({"yksikkö", "sisaolento"}), name_str
		), FuncOutput(lambda *p: ForParser(name_str, *p, group=True)))
		
		pgl(".COND-STMT ::= jokaiselle .PATTERN-%d{ulkotulento} %s .EXPR-%d{omanto} %s pätee : -> for each $1 in $2.%s:" % (
			vtype.id, named_code, owner.id, pattern({"yksikkö", "sisaolento"}), name_str
		), FuncOutput(lambda *p: ForCondParser(name_str, "all", "forSet", *p)))
		
		pgl(".COND-STMT ::= jollekin .PATTERN-%d{ulkotulento} %s .EXPR-%d{omanto} %s pätee : -> for each $1 in $2.%s:" % (
			vtype.id, named_code, owner.id, pattern({"yksikkö", "sisaolento"}), name_str
		), FuncOutput(lambda *p: ForCondParser(name_str, None, "onceSet", *p)))
	
	def addContainsPattern(condpattern, arglambda, pseudonot, pynot, modify):
		pgl(".COND ::= .EXPR-%d{omanto} %s %s -> %s$1.%s.contains($2)" % (
			owner.id, pattern({"yksikkö", "nimento"}), condpattern, pseudonot, name_str
		), FuncOutput(lambda obj, val: (
			'(%s %s.containsSet(%s, %s))' % (pynot, obj, repr(name_str), arglambda(val)),
			orTrue(modify(arglambda(val), obj))
		)))
	
	for p in [
		("sisältää .EXPR-%d{omanto}" % (vtype.id,),               lambda x: x,            "", "",     to_append),
		("sisältää yhdenkin .PATTERN-%d{omanto}" % (vtype.id,),   lambda x: x.toPython(), "", "",     to_append),
		("ei sisällä .EXPR-%d{osanto}" % (vtype.id,),             lambda x: x,            "!", "not", to_remove),
		("ei sisällä yhtäkään .PATTERN-%d{osanto}" % (vtype.id,), lambda x: x.toPython(), "!", "not", to_remove)
	]:
		addContainsPattern(*p)
	
	pgl(".COND ::= .EXPR-%d %s on tyhjä -> $1.%s.empty()" % (owner.id, pattern({"yksikkö", "nimento"}), name_str),
		FuncOutput(lambda obj: ('%s.isSetEmpty(%s)' % (obj, repr(name_str)), '%s.clearSet(%s)' % (obj, repr(name_str)))))

# Adjektiivit

def addBitPatternPhrase(owner, clazz, name_code, name_str, name_set):
	pgl(".PATTERN-%d ::= %s .PATTERN-%d{$} -> %s($1)" % (clazz.id, name_code, owner.id, name_str),
		FuncOutput(lambda p: p.bitsOff(name_set-{name_str}).bitOn(name_str)))

def addBitClassPatternPhrase(clazz, name_code, name_str, name_set):
	pgl(".CLASS-PATTERN-%d ::= %s .CLASS-PATTERN-%d{$} -> %s($1)" % (clazz.id, name_code, clazz.id, name_str),
		FuncOutput(lambda p: p.bitsOff(name_set-{name_str}).bitOn(name_str)))

def defineBit(owner, *names):
	counter = nextCounter("defineBit")
	
	names = names
	name_strs = []
	name_codes = []
	for name in names:
		name_strs.append(tokensToString(name, {"yksikkö", "nimento"}))
		name_codes.append(nameToCode(name, rbits={"yksikkö", "nimento"}))
	name_set = set(name_strs)
	owner.bit_groups.append((names, name_strs, name_codes))
	
	def addBitPhrases(name, name_str, name_code):
		name_code_nominative = nameToCode(name, bits={"yksikkö", "nimento"}, rbits={"yksikkö", "nimento"})
		
		pgl(".ENUM-DEFAULT-DEF-%d ::= .CLASS-%d{nimento} on yleensä %s . -> $1 defaults %s" % (
			counter, owner.id, name_code_nominative, name_str
		), FuncOutput(lambda c: c.bitOn(name_str)))

		for clazz in owner.subclasses():
			addBitPatternPhrase(clazz, clazz, name_code, name_str, name_set)
			addBitClassPatternPhrase(clazz, name_code, name_str, name_set)
		
		if owner.superclass:
			for clazz in owner.superclass.superclasses():
				addBitPatternPhrase(owner, clazz, name_code, name_str, name_set)
		
		pgl(".CMD ::= .EXPR-%d{nimento} on nyt %s . -> $1.%s = True" % (
			owner.id, name_code_nominative, name_str
		), FuncOutput(lambda obj: '%s.bitsOff(%s).bitOn(%s)' % (obj, repr(name_set-{name_str}), repr(name_str))))
		
		if len(name_set) == 1:
			pgl(".CMD ::= .EXPR-%d{nimento} ei ole enää %s . -> $1.%s = False" % (
				owner.id, name_code_nominative, name_str
			), FuncOutput(lambda obj: '%s.bitOff(%s)' % (obj, repr(name_str))))
		
		pgl(".COND ::= .EXPR-%d{nimento} on %s -> $1.%s == True" % (
			owner.id, name_code_nominative, name_str
		), FuncOutput(lambda obj: (
			'%s in %s.bits' % (repr(name_str), obj),
			orTrue('%s.bitsOff(%s).bitOn(%s)' % (obj, repr(name_set-{name_str}), repr(name_str)))
		)))
		
	for name, name_str, name_code in zip(names, name_strs, name_codes):
		addBitPhrases(name, name_str, name_code)
	pgl(".DEF ::= .ENUM-DEFAULT-DEF-%d -> $1" % (counter,), identity)
	GRAMMAR_STACK[-1].addCategoryName("ENUM-DEFAULT-DEF-%d" % (counter,), "bitin oletusarvomääritys")

pgl(".ENUM-DEF ::= .CLASS{nimento} voi olla .* . -> $1 has bit $2", FuncOutput(defineBit))
pgl(".ENUM-DEF ::= .CLASS{nimento} on joko .* tai .* . -> $1 has bits $2==!$3", FuncOutput(defineBit))
pgl(".ENUM-DEF ::= .CLASS{nimento} on joko .* , .* tai .* . -> $1 has bits $2==!($3|$4)", FuncOutput(defineBit))
pgl(".DEF ::= .ENUM-DEF -> $1", identity)

GRAMMAR_STACK[-1].addCategoryName("ENUM-DEF", "bittikenttämääritys")

# Ehdot

pgl(".COND ::= .COND ja .COND -> $1 and $2", FuncOutput(lambda x, y: ('(%s and %s)' % (x[0], y[0]), orTrue('(%s, %s)' % (x[1], y[1])))))
pgl(".COND ::= .COND , .COND ja .COND -> $1 and $2 and $3", FuncOutput(lambda x, y, z: ('(%s and %s and %s)' % (x[0], y[0], z[0]), orTrue('(%s, %s, %s)' % (x[1], y[1], z[1])))))

GRAMMAR_STACK[-1].addCategoryName("COND", "ehtolauseke")

pgl(".COND-STMT ::= .COND -> $1", identity)

pgl(".COND-STMT ::= kaikki seuraavista : -> every:", FuncOutput(lambda: CondReductionParser("and", lambda modifys: orTrue("(" + ", ".join(modifys) + ")"))))
pgl(".COND-STMT ::= jokin seuraavista : -> some:", FuncOutput(lambda: CondReductionParser("or", lambda modifys: "(" + " or ".join(modifys) + ")")))

GRAMMAR_STACK[-1].addCategoryName("COND-STMT", "ehtolause")

class CondReductionParser:
	def __init__(self, operator, to_modify):
		self.operator = operator
		self.to_modify = to_modify
	def parse(self, file, grammar, report=False):
		checks, modifys = parseCondBlock(file, grammar, report=report)
		return "(" + (" " + self.operator + " ").join(checks) + ")", self.to_modify(modifys)

class ForCondParser:
	def __init__(self, field_name, reduce, loop, *args):
		self.field_name = field_name
		self.reduce = reduce
		self.loop = loop
		self.args = args
	def parse(self, file, grammar, report=False):
		grammar = grammar.copy()
		
		param_pattern = self.args[0]
		param_name = None if len(self.args) == 2 else self.args[1]
		obj = self.args[-1]
		
		addParamPhrases(grammar, "_val", param_pattern.type(), param_name)
		
		checks, modifys = parseCondBlock(file, grammar, report=report)
		
		ans = []
		for block, join_op, func in [(checks, " and ", self.reduce), (modifys, ", ", None)]:
			block_str = "lambda: (" + join_op.join(block) + ")"
			target_code = '%s.%s(%s, %s, %s, %s)' % (obj, self.loop, repr(self.field_name), repr("_val"), param_pattern.toPython(), block_str)
			if func:
				ans.append(func+"("+target_code+")")
			else:
				ans.append(target_code)
		return tuple(ans)

# Ehtosäännön vartalo

def parseCondBlock(file, grammar, report=False):
	return zip(*parseBlock(file, grammar, category="COND-STMT", report=report))

# Parametrit

def parseParameters(nameds, args):
	params = []
	i = 0
	j = 0
	while i < len(args)-1:
		#                      VTYPE,CASE, POST,      NAME
		if nameds[j]:
			params.append((*args[i],   args[i+2], args[i+1]))
		else:
			params.append((*args[i],   args[i+1], None))
		i += 3 if nameds[j] else 2
		j += 1
	return params

def addParameterPatterns(num_params):
	for nameds in itertools.product(*[[False, True]]*num_params):
		addParameterPattern(nameds)

def addParameterPattern(nameds):
	pattern = " ".join(["[ .CLASS-CASE %s ] .**" % ("" if not named else "( .* )",) for named in nameds])
	pgl(".PARAMETERS-%d ::= %s -> $*" % (len(nameds), pattern), FuncOutput(lambda *p: parseParameters(nameds, p)))
	GRAMMAR_STACK[-1].addCategoryName("PARAMETERS-%d" % (len(nameds),), "%d-parametrinen hahmo" % (len(nameds),))

for num_params in [1,2,3]:
	addParameterPatterns(num_params)

# Käyttäjän määrittelemät ehtosäännöt

# args on joko [pre], [first_name, pre], [pre, params] tai [first_name, pre, params]
def defineCondition(grammar, file, custom_verb, first_named, owner, *args, report=False):
	
	# parsitaan argumentit
	args = list(args)
	if first_named:
		first_name = args[0]
		del args[0]
	else:
		first_name = None
	pre = args[0]
	params = args[1] if len(args) >= 2 else []
	
	# luodaan nimi ja patterni
	name_str = " ".join([tokensToString(pre)] + [
		"- %s" % (tokensToString(post),) for _, _, post, _ in params
	]) + "/" + str(nextCounter("defineCondition"))
	
	pattern = " ".join([tokensToCode(pre)] + [
		".EXPR-%d{%s} %s" % (vtype.id, case, tokensToCode(post)) for vtype, case, post, _ in params
	])
	
	# make_call-funktiolla voi tehdä koodin, joka kutsuu ehtolausetta
	make_call = lambda var, p: "evalOrCall(%s[%s], [%s])" % (var, repr(name_str), ", ".join(p))
	
	# tehdään ehtokomento, muuttamiskomento ja totuusmääritys
	# ne tehdään sekä globaaliin nimiavaruuteen (GRAMMAR_STACK[-1]) että ehtolauseen sisäiseen (grammar)
	pre = "nyt" if custom_verb else ""
	verb = "" if custom_verb else "on"
	post = "" if custom_verb else "nyt"
	
	grammar = grammar.copy()
	
	for g in [GRAMMAR_STACK[-1], grammar]:
		g.parseGrammarLine(".CMD ::= %s .EXPR-%d{nimento} %s %s %s . -> $1~%s = True" % (pre, owner.id, verb, post, pattern, name_str),
			FuncOutput(lambda *p: "(" + make_call("MODIFYS", p) + ")"))

		g.parseGrammarLine(".COND ::= .EXPR-%d{nimento} %s %s -> $1~%s" % (owner.id, verb, pattern, name_str),
			FuncOutput(lambda *p: ("(" + make_call("CHECKS", p) + ")[-2]", orTrue("(" + make_call("MODIFYS", p) + ")"))))

		g.parseGrammarLine(".EXPR-TRUTH-DEF ::= .EXPR-%d{nimento} %s %s . -> $1~%s = True" % (owner.id, verb, pattern, name_str),
			FuncOutput(lambda *p: "(" + make_call("MODIFYS", p) + ")"))
	
	tmp_vars = ["_" + str(i) for i in range(len(params)+1)]
	
	# parsitaan vartalo
	addParamPhrases(grammar, tmp_vars[0], owner, first_name)
	for (vtype, case, _, name), tmp_var in zip(params, tmp_vars[1:]):
		addParamPhrases(grammar, tmp_var, vtype, name)
	
	checks, modifys = parseCondBlock(file, grammar, report=report)
	
	check = "(" + " and ".join(checks) + ")"
	modify = "(" + ", ".join(modifys) + ")"
	
	# luodaan ehto- ja muuttamisfunktiot
	make_lambda = lambda content: "(lambda " + ",".join(tmp_vars) + ": (" + ", ".join([
		"pushStackFrame(" + repr(name_str) + ")",
	] + ["putVar(" + repr(tmp_var) + ", " + tmp_var + ")" for tmp_var in tmp_vars] + [
		content,
		"popStackFrame()",
	]) + "))"
	
	CHECKS[name_str] = make_lambda(check)
	MODIFYS[name_str] = make_lambda(modify)
	
	# ohjelma ei osaa päätellä käyttäjän antaman verbin partisiippimuotoa
	if custom_verb:
		return
	
	# adjektiivisuus päätellään viimeisen sanan perusteella
	if len(pre) == 0 and (len(params) == 0 or len(params[-1][2]) == 0):
		is_adjective = False
	else:
		last_token = pre[-1] if len(params) == 0 else params[-1][2][-1]
		is_adjective = ("laatusana" in last_token.bits() or "nimisana_laatusana" in last_token.bits()) and "nimento" in last_token.bits()
	
	create_condition = lambda p: RCondition(
		"_obj", "(" + make_call("CHECKS", ("_obj",)+p) + ")[-2]", "(" + make_call("MODIFYS", ("_obj",)+p) + ")"
	)
	
	# adjektiivisen ja adverbiaalisen fraasin yhteinen funktio
	func = lambda *p: p[-1].addCondition(create_condition(p[:-1]))
	
	# yhteinen output-merkkijonon osa
	output_str = name_str + "(" + ", ".join(["$" + str(n+1) for n in range(len(params)+1)]) + ")"
	
	if is_adjective:
		def addAttributePhrase(owner, clazz):
			pgl(".PATTERN-%d ::= %s .PATTERN-%d{$} -> %s" % (clazz.id, pattern, owner.id, output_str), FuncOutput(func))
			if owner is clazz: # ehto tarvitaan, ettei tätä lisättäisi kahdesti (alempana kahdessa for-silmukassa)
				pgl(".CLASS-PATTERN-%d ::= %s .CLASS-PATTERN-%d{$} -> %s" % (clazz.id, pattern, clazz.id, output_str), FuncOutput(func))
	else:
		def addAttributePhrase(owner, clazz):
			pgl(".PATTERN-%d ::= %s oleva{$} .PATTERN-%d{$} -> %s" % (clazz.id, pattern, owner.id, output_str), FuncOutput(func))
			if owner is clazz:
				pgl(".CLASS-PATTERN-%d ::= %s oleva{$} .CLASS-PATTERN-%d{$} -> %s" % (clazz.id, pattern, clazz.id, output_str), FuncOutput(func))
				pgl(".CLASS-PATTERN-WITH-ADV-%d ::= .CLASS-PATTERN-%d %s -> %s" % (clazz.id, clazz.id, pattern, output_str),
					FuncOutput(lambda *p: p[0].addCondition(create_condition(p[1:]))))
		
		pgl(".COPY-DEF ::= %s on .EXPR-%d{yksikkö,nimento} . -> copy $* ~ %s" % (pattern, owner.id, output_str),
			FuncOutput(lambda *p: eval(p[-1]).createCopies(1, create_condition(p[:-1]))))
		pgl(".COPY-DEF ::= %s on .N .EXPR-%d{yksikkö,osanto} . -> copy $* ~ %s" % (pattern, owner.id, output_str),
			FuncOutput(lambda *p: eval(p[-1]).createCopies(p[-2], create_condition(p[:-2]))))
	
	if owner.superclass:
		for clazz in owner.superclass.superclasses():
			addAttributePhrase(owner, clazz)
	
	for clazz in owner.subclasses():
		addAttributePhrase(clazz, clazz)
	
	owner.attributePhraseAdders.append(addAttributePhrase)

class ConditionParser:
	def __init__(self, *p):
		self.args = p
	def parse(self, file, grammar, report=False):
		return defineCondition(grammar, file, *self.args, report=report)

def addConditionDefPatterns(num_params):
	addConditionDefPattern(num_params, False)
	addConditionDefPattern(num_params, True)

def addConditionDefPattern(num_params, first_named):
	first_name = "" if not first_named else "( .* )"
	parameters = "" if not num_params else ".PARAMETERS-%d" % (num_params,)
	for prefix, postfix in [("Kun", ""), ("", ", jos")]:
		pgl(".COND-DEF ::= Määritelmä . %s .CLASS{nimento} %s on \" .** %s \" %s : -> def $1~ $*:" % (prefix, first_name, parameters, postfix),
			FuncOutput(lambda *p: ConditionParser(False, first_named, *p)))
		pgl(".COND-DEF ::= Määritelmä . %s .CLASS{nimento} %s \" .** %s \" %s : -> def $1~ $*:" % (prefix, first_name, parameters, postfix),
			FuncOutput(lambda *p: ConditionParser(True, first_named, *p)))

for num_params in [0,1,2]:
	addConditionDefPatterns(num_params)

pgl(".DEF ::= .EXPR-TRUTH-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("EXPR-TRUTH-DEF", "totuusmääritys")

pgl(".DEF ::= .COND-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("COND-DEF", "ehtomääritys")

pgl(".DEF ::= .COPY-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("COPY-DEF", "kopiomääritys")

# Muuttujat

def defineVariable(name, class_pattern):
	name_str = tokensToString(name)
	pattern = lambda bits: nameToCode(name, bits, rbits={"yksikkö", "nimento"})
	
	if len(NAMESPACE_STACK) > 1:
		name_str = NAMESPACE_STACK[-1] + "::" + name_str
	
	if name_str in GLOBAL_SCOPE.variables:
		# muuttuja on jo olemassa
		class_pattern.modify(GLOBAL_SCOPE.variables[name_str])
		return
	
	vtype = class_pattern.type()
	obj = class_pattern.newInstance(name)
	GLOBAL_SCOPE.variables[name_str] = obj
	
	to_get = lambda: 'getVar(' + repr(name_str) + ')'
	to_set = lambda x: 'setVar(' + repr(name_str) + ', ' + x + ')'
	
	for clazz in vtype.superclasses():
		pgl(".EXPR-%d ::= %s -> %s" % (clazz.id, pattern({"$"}), name_str),
			FuncOutput(to_get))
	
	# Asettaminen lopullisesti
	pgl(".CMD ::= %s on nyt .EXPR-%d{nimento} . -> %s = $1" % (pattern({"yksikkö", "nimento"}), vtype.id, name_str),
		FuncOutput(to_set))
	
	# Asettaminen väliaikaisesti
	pgl(".CMD ::= .EXPR-%d %s : -> $1 as $2:" % (vtype.id, pattern({"olento"})), FuncOutput(lambda val: AsParser(name_str, val)))
	
	pgl(".COND ::= %s on .EXPR-%d{nimento} -> %s==$2" % (
		pattern({"yksikkö", "nimento"}), vtype.id, name_str
	), FuncOutput(lambda x: ('%s.equals(%s)' % (to_get(), x), orTrue(to_set(x)))))
	
	pgl(".ALIAS-DEF ::= tulkitse .EXPR-%d{nimento} %s . -> $1 = %s" % (
		merkkijono.id, pattern({"yksikkö", "olento"}), name_str
	), FuncOutput(lambda alias: obj.addVariableAlias(tokenize(eval(alias).extra["str"]))))
	
	pgl(".SELECTION-DEF ::= tarkoittaako pelaaja %s : -> does the player mean %s:" % (
		pattern({"yksikkö", "olento"}), name_str
	), FuncOutput(lambda: SelectionParser(obj)))
	
	for clazz in vtype.superclasses():
		pgl(".PATTERN-%d ::= %s -> %s" % (clazz.id, pattern({"$"}), name_str),
			FuncOutput(lambda: RPattern(obj=obj)))
	
	pgl(".VARIABLE-VALUE-DEF ::= %s on alussa .EXPR-%d{nimento} . -> %s = $1" % (
		pattern({"yksikkö", "nimento"}), vtype.id, name_str
	), FuncOutput(lambda x: setGlobalVar(name_str, eval(x))))

pgl(".VARIABLE-DEF ::= .*{nimento} on .CLASS-PATTERN{nimento} . -> $1 : $2", FuncOutput(defineVariable))
pgl(".DEF ::= .VARIABLE-DEF -> $1", identity)
pgl(".DEF ::= .ALIAS-DEF -> $1", identity)
pgl(".DEF ::= .VARIABLE-VALUE-DEF -> $1", identity)

GRAMMAR_STACK[-1].addCategoryName("VARIABLE-DEF", "muuttujamääritys")
GRAMMAR_STACK[-1].addCategoryName("ALIAS-DEF", "tulkintamääritys")
GRAMMAR_STACK[-1].addCategoryName("VARIABLE-VALUE-DEF", "muuttuja-arvomääritys")

class AsParser:
	def __init__(self, variable, value):
		self.variable = variable
		self.value = value
	def parse(self, file, grammar, report=False):
		block = parseBlock(file, grammar, report=report)
		block_str = joinCodes(block)
		return "(pushScope(), putVar(%s, %s, to_scope_stack=True), %s, popScope())" % (repr(self.variable), self.value, block_str)

# Apufunktio

def addParamPhrases(grammar, case, vtype, name, varname=None, plural=False):
	if name:
		for clazz in vtype.superclasses():
			grammar.parseGrammarLine(".EXPR-%d ::= %s -> %s param" % (
				clazz.id, nameToCode(name, rbits={"yksikkö", "nimento"}), vtype.name
			), FuncOutput(lambda: varname or ('getVar(' + repr(case) + ')')))
	else:
		if not plural:
			pronoun = "hän" if "inhimillinen" in vtype.allBits() else "se"
		else:
			pronoun = "he" if "inhimillinen" in vtype.allBits() else "he"
		for clazz in vtype.superclasses():
			grammar.parseGrammarLine(".EXPR-%d ::= %s{$} -> %s param" % (clazz.id, pronoun, vtype.name),
				FuncOutput(lambda: varname or ('getVar(' + repr(case) + ')')))
			grammar.parseGrammarLine(".PATTERN-%d ::= %s{$} -> %s param" % (clazz.id, pronoun, vtype.name),
				FuncOutput(lambda: varname or ('getVar(' + repr(case) + ')')))

# Toiminnot

class ListenerParser:
	def __init__(self, args):
		self.args = args
		self.action = self.args[0]
		self.params = self.args[1]
	def parse(self, file, grammar, report=False):
		grammar = grammar.copy()
		for i, (c, p, n) in enumerate(self.params):
			addParamPhrases(grammar, "_" + str(i), p.type(), n)
		grammar.parseGrammarLine(".CMD ::= keskeytä toiminto . -> stop", FuncOutput(lambda: 'ACTION_STACK[-1].bitOn("stop action")')) # suoritetaan isäntäscopessa
		listener_name = None
		listener_name_code = None
		def setListenerName(name):
			nonlocal listener_name, listener_name_code
			listener_name = tokensToString(name)
			listener_name_code = tokensToCode(name)
		grammar.parseGrammarLine(".CMD ::= ( .* ) -> listener name = $1", FuncOutput(setListenerName))
		body = parseBlock(file, grammar, report=report)
		listener = RListener(*self.args, body, name=listener_name)
		if listener_name_code:
			pgl(".LISTENER-NAME-%d ::= %s{$} -> %s" % (self.action.id, listener_name_code, listener_name), FuncOutput(lambda: listener))
		return listener

def defineAction(name, params, pre, post):
	name_str = (tokensToString(pre) + " " + name.token + " " + tokensToString(post)).lower().strip()
	action = RAction(name_str)
	
	def defineActionListener(patterns, priority, is_special_case, is_general_case):
		return ListenerParser((action, [(a_case, pattern, name) for (pattern, name), (_, _, a_case) in zip(patterns, params)], priority, is_special_case, is_general_case))
	
	def defineActionSelection(patterns):
		return ActionSelectionParser(action, [(a_case, pattern, name) for (pattern, name), (_, _, a_case) in zip(patterns, params)])
	
	def separateGroups(groups, nameds):
		i = 0
		j = 0
		ans = []
		while i < len(groups):
			if nameds[j]:
				ans.append((groups[i], groups[i+1]))
				i += 2
			else:
				ans.append((groups[i], None))
				i += 1
			j += 1
		return ans
	
	signature_pattern = lambda nameds: " ".join([
		"%s .PATTERN-%d{%s,yksikkö}" % (tokensToCode(a_pre), a_class.id, a_case)
		+ (" ( .* )" if named else "")
		for named, (a_pre, a_class, a_case) in zip(nameds, params)
	])
	
	def addListenerDefPattern(nameds, p_pre, p_case, p_post, priority, is_special_case, is_general_case):
		pgl(".LISTENER-DEF-%d ::= %s %s %s %s{-minen,%s} %s %s : -> def %s($1):" % (
			action.id,
			p_pre,
			signature_pattern(nameds),
			tokensToCode(pre), name.baseform("-minen"), p_case, tokensToCode(post), p_post,
			name.token
		), FuncOutput(lambda *groups: defineActionListener(separateGroups(groups, nameds), priority, is_special_case, is_general_case)))

	def addSelectionDefPattern(nameds):
		pgl(".SELECTION-DEF ::= tarkoittaako pelaaja %s %s %s{-minen,osanto} %s : -> does the player mean %s($*):" % (
			signature_pattern(nameds),
			tokensToCode(pre), name.baseform("-minen"), tokensToCode(post),
			name.token
		), FuncOutput(lambda *groups: defineActionSelection(separateGroups(groups, nameds))))

	for nameds in itertools.product(*[[False, True]]*len(params)):
		for priority_properties in LISTENER_PRIORITIES:
			addListenerDefPattern(nameds, *priority_properties)
		addSelectionDefPattern(nameds)
	
	pgl(".DEF ::= .LISTENER-DEF-%d -> $1" % (action.id,), identity)
	GRAMMAR_STACK[-1].addCategoryName("LISTENER-DEF-%d" % (action.id,), "kuuntelijamääritys")
	
	def defineCommand(category, pre, *cases_posts, is_reversed=False):
		cmd_params = []
		for i in range(0, len(cases_posts), 2):
			cmd_params.append((cases_posts[i], cases_posts[i+1]))
		
		command_pattern = "%s %s" % (
			tokensToCode(pre),
			" ".join([
				".EXPR-%d{%s} %s" % (
					a_class.id,
					cmd_case + (",yksikkö" if category != "PLAYER-CMD" else ""), # pelaaja voi viitata sanoihin sekä yksikössä että monikossa
					tokensToCode(post)
				)
			for (_, a_class, _), (cmd_case, post) in zip(reversed(params) if is_reversed else params, cmd_params)])
		)
		
		def addCommandPhrase(cmd_post, in_scope):
			pgl(".%s ::= %s %s -> %s($1)" % (
				category,
				command_pattern,
				cmd_post,
				name.token
			), FuncOutput(lambda *val: 'ACTIONS[%d].run([%s], %s)' % (action.id, ", ".join(reversed(val) if is_reversed else val), repr(in_scope))))
		for cmd_post, in_scope in [(".", True), ("jos mahdollista .", False), (", jos mahdollista .", False)]:
			addCommandPhrase(cmd_post, in_scope)
		
		if category == "PLAYER-CMD":
			action.addPlayerCommand(command_pattern)
	
	def addCommandDefPhraseAndIgnorePhrase(is_reversed):
		cmd_pattern = " ".join([
			"[ .CLASS-CASE-%d ] .**" % (a_class.id,)
		for _, a_class, _ in (reversed(params) if is_reversed else params)])
		
		# Action patterneja ovat 1) pelkkä toiminnon nimi 2) toiminnon nimi + adpositiot 3) toiminnon nimi + adpositiot + parametrien tyypit
		action_patterns = [
			"%s %s{-minen,CASE} %s" % (
				tokensToCode(pre), name.baseform("-minen"), tokensToCode(post),
			)
		]
		if len(params) != 0:
			action_patterns.append(
				"%s %s %s{-minen,CASE} %s" % (
					" ".join([
						tokensToCode(a_pre) + " " + a_class.nameToCode({a_case, "yksikkö"})
					for a_pre, a_class, a_case in params]),
					tokensToCode(pre), name.baseform("-minen"), tokensToCode(post)
				)
			)
			if sum([len(a_pre) for a_pre, _, _ in params]) + len(pre) + len(post) != 0:
				action_patterns.append(
					"%s %s %s{-minen,CASE} %s" % (
						" ".join([tokensToCode(a_pre) for a_pre, _, _ in params]),
						tokensToCode(pre), name.baseform("-minen"), tokensToCode(post),
					)
				)
		for action_pattern in action_patterns:
			pgl(".COMMAND-DEF-%d ::= %s komento on \" .** %s \" . -> def %s command" % (
				action.id,
				action_pattern.replace("CASE", "omanto"),
				cmd_pattern,
				name.token
			), FuncOutput(lambda *p: defineCommand("CMD", *p, is_reversed=is_reversed)))
			pgl(".COMMAND-DEF-%d ::= tulkitse \" .** %s \" %s . -> def %s command" % (
				action.id,
				cmd_pattern,
				action_pattern.replace("CASE", "olento"),
				name.token
			), FuncOutput(lambda *p: defineCommand("PLAYER-CMD", *p, is_reversed=is_reversed)))
			if not is_reversed:
				pgl(".IGNORE-DEF-%d ::= %s .LISTENER-NAME-%d{osanto} ei sovelleta . -> ignore %s::$1" %(
					action.id,
					action_pattern.replace("CASE", "omanto"),
					action.id,
					name.token
				), FuncOutput(lambda listener: listener.disable()))
	
	# lisätään komentomääritykset (komento on, tulkitse) sekä ei sovelleta -komento
	# jos parametreja on kaksi ja niillä on eri tyyppi, salli myös parametrien määrittely eri päin
	addCommandDefPhraseAndIgnorePhrase(False)
	if len(params) == 2 and params[0][1] != params[1][1]:
		addCommandDefPhraseAndIgnorePhrase(True)
	
	pgl(".DEF ::= .COMMAND-DEF-%d -> $1" % (action.id,), identity)
	pgl(".DEF ::= .IGNORE-DEF-%d -> $1" % (action.id,), identity)
	GRAMMAR_STACK[-1].addCategoryName("COMMAND-DEF-%d" % (action.id,), "komentomääritys")

def addActionDefPattern(num_params):
	def transformArgs(args):
		ans = []
		i = -2
		for i in range(0, num_params*2, 2):
			#           PRE      CLASS, CASE
			ans.append((args[i], *args[i+1]))
		#      NAME       PARAMS PRE        POST
		return args[i+3], ans,   args[i+2], args[i+4]
	pgl(".ACTION-DEF ::= %s .** ..{-minen,nimento} .** on toiminto . -> action $%d(%d)" % (
		" ".join([".** [ .CLASS-CASE ]"]*num_params),
		num_params*2+2,
		num_params
	), FuncOutput(lambda *p: defineAction(*transformArgs(p))))

for num_params in [0,1,2]:
	addActionDefPattern(num_params)

pgl(".DEF ::= .ACTION-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("ACTION-DEF", "toimintomääritys")

# Sisäänrakennetut luokat

yläkäsite = defineClass(tokenize("yläkäsite"), None)

pgl(".EXPR ::= .EXPR-%d{$} -> $1" % (yläkäsite.id,), identity)
GRAMMAR_STACK[-1].addCategoryName("EXPR", "lauseke")

asia = defineClass(tokenize("asia"), yläkäsite)

merkkijono = defineClass(tokenize("merkkijono"), yläkäsite)
merkkijono.primitive = "lambda obj: 'createStringObj(' + repr(obj.extra['str']) + ')'"
for clazz in [yläkäsite, merkkijono]:
	pgl('.EXPR-%d ::= " .STR-CONTENT " -> "$1"' % (clazz.id,), FuncOutput(lambda s: 'createStringObj(' + s + ')'))
	pgl('.EXPR-%d ::= rivinvaihto{$} -> "\\n"' % (clazz.id,), FuncOutput(lambda: 'createStringObj("\\n")'))
	pgl('.EXPR-%d ::= .EXPR-%d{$} isolla alkukirjaimella -> capitalize($1)' % (clazz.id, merkkijono.id),
		FuncOutput(lambda x: 'createStringObj(' + x + '.extra["str"].capitalize())'))

kokonaisluku = defineClass(tokenize("kokonaisluku"), yläkäsite)
kokonaisluku.primitive = "lambda obj: 'createIntegerObj(' + repr(obj.extra['int']) + ')'"

def addIntOperator(clazz, op, pyop):
	pgl('.EXPR-%d ::= ( .EXPR-%d{nimento} %s .EXPR-%d{$} ) -> ($1 %s $2)' % (clazz.id, kokonaisluku.id, op, kokonaisluku.id, pyop),
		FuncOutput(lambda a, b: 'createIntegerObj(%s.extra["int"] %s %s.extra["int"])' % (a, pyop, b)))

def addIntCondition(op, pyop):
	pgl('.COND ::= .EXPR-%d{nimento} %s .EXPR-%d{$} -> ($1 %s $2)' % (kokonaisluku.id, op, kokonaisluku.id, pyop),
		FuncOutput(lambda a, b: ('(%s.extra["int"] %s %s.extra["int"])' % (a, pyop, b), '()'))) # TODO: virhe modify-osassa

for clazz in [yläkäsite, kokonaisluku]:
	pgl('.EXPR-%d ::= .N{$} -> $1' % (clazz.id,), FuncOutput(lambda s: 'createIntegerObj(' + str(s) + ')'))
	pgl('.EXPR-%d ::= satunnaisluku{$} välillä .EXPR-%d{sisaeronto} .EXPR-%d{sisatulento} -> rnd($1, $2)' % (
		clazz.id, kokonaisluku.id, kokonaisluku.id
	), FuncOutput(lambda start, end: 'createIntegerObj(random.randint(%s.extra["int"], %s.extra["int"]))' % (start, end)))
	pgl('.EXPR-%d ::= .EXPR-%d{omanto} neliöjuuri{$} -> $1' % (clazz.id,kokonaisluku.id), FuncOutput(lambda arg: 'createIntegerObj(math.sqrt(' + arg + '.extra["int"]))'))
	for op, pyop in [("+", "+"), ("-", "-"), ("–", "-"), ("−", "-"), ("*", "*"), ("/", "/")]:
		addIntOperator(clazz, op, pyop)

for op, pyop in [
	("=", "=="), ("on yhtä suuri kuin", "=="),
	("/=", "!="), ("ei ole", "!="),
	("<", "<"), ("on pienempi kuin", "<"),
	(">", ">"), ("on suurempi kuin", ">"),
	("<=", "<="), ("on pienempi tai yhtä suuri kuin", "<="), ("on enintään", "<="),
	(">=", ">="), ("on suurempi tai yhtä suuri kuin", ">="), ("on vähintään", ">=")]:
	addIntCondition(op, pyop)

# Monikot

def addTuple(*args, case="nimento"):
	num_fields = (len(args)-2)//2
	class_name = args[-1]
	tupleclass = defineClass(class_name, yläkäsite, name_rbits={"yksikkö", case})
	tupleclass.primitive = "lambda obj: 'createTupleObj(\"" + tupleclass.name.replace("\\", "\\\\").replace("\"", "\\\"") + "\", ' + ', '.join([v.toPythonRef() for v in obj.extra['tuple']]) + ')'"
	prefix = args[0]
	code = tokensToCode(prefix)

	def addFieldExpression(i, field_name):
		for clazz in kokonaisluku.superclasses():
			pgl(".EXPR-%d ::= .EXPR-%d{omanto} %s -> $1.%s" % (
					clazz.id,
					tupleclass.id,
					nameToCode(field_name, {"$"}, rbits={"nimento", "yksikkö"}),
					nameToCode(field_name)
				),
				FuncOutput(lambda obj: obj + '.extra["tuple"][' + repr((i-1)//2) + ']'))

	for i in range(1, len(args)-1, 2):
		field_name = args[i]
		postfix = args[i+1]
		addFieldExpression(i, field_name)
		code += " .EXPR-%d{nimento} %s" % (kokonaisluku.id, tokensToCode(postfix))

	create = lambda *args: 'createTupleObj(' + ", ".join((repr(tupleclass.name),) + args) + ')'

	def addTupleOperator(clazz, op, pyop):
		pgl('.EXPR-%d ::= ( .EXPR-%d{nimento} %s .EXPR-%d{$} ) -> ($1 %s $2)' % (clazz.id, tupleclass.id, op, tupleclass.id, pyop),
			FuncOutput(lambda a, b:
				create(*[
					'createIntegerObj(%s.extra["tuple"][%d].extra["int"] %s %s.extra["tuple"][%d].extra["int"])' % (a, i, pyop, b, i)
					for i in range(1, num_fields)
				])))
	
	for clazz in tupleclass.superclasses():
		for op, pyop in [("+", "+"), ("-", "-")]:
			addTupleOperator(clazz, op, pyop)
		for det in ["", nameToCode(class_name, rbits={"yksikkö", case}) + " "]:
			pgl(".EXPR-%d ::= %s%s -> ( %s )" % (clazz.id, det, code, ", ".join(["$%d" % i for i in range(1, num_fields)])),
				FuncOutput(create))

for num_fields in [1, 2, 3]:
	pgl('.TUPLE-DEF ::= " .** %s" on merkintä .* . -> %d-tuple $1' % (
		"[ .* ] .** "*num_fields,
		num_fields
	), FuncOutput(lambda *a: addTuple(*a, case="ulkotulento")))
	pgl('.TUPLE-DEF ::= " .** %s" on .* merkintä . -> %d-tuple $1' % (
		"[ .* ] .** "*num_fields,
		num_fields
	), FuncOutput(lambda *a: addTuple(*a, case="omanto")))

pgl(".DEF ::= .TUPLE-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("TUPLE-DEF", "monikkomääritys")

# For-silmikka

class ForParser:
	def __init__(self, field_name, *args, group=False, global_set=False):
		self.field_name = field_name
		self.args = args
		self.group = group
		self.global_set = global_set
	def parse(self, file, grammar, report=False):
		grammar = grammar.copy()
		
		param_pattern = self.args[0]
		param_name = None if len(self.args) == 1 else self.args[1]

		counter = nextCounter("ForParser")
		varname = "val_" + str(counter)
		
		addParamPhrases(grammar, varname, param_pattern.type(), param_name, plural=self.group)
		if self.group:
			for clazz in kokonaisluku.superclasses():
				grammar.parseGrammarLine(".EXPR-%d ::= ryhmän koko{$} -> val count" % (clazz.id,),
					FuncOutput(lambda: 'getVar("_count")'))
			# TODO PURKKAA:
			grammar.parseGrammarLine(".COND ::= ryhmän koko{$} on .N -> val count = $1",
				FuncOutput(lambda n: ('getVar("_count").extra["int"] == %s' % (repr(n),), "()"))) # TODO virhe modify-osassa
		
		block = parseBlock(file, grammar, report=report)
		block_str = "lambda: (" + ", ".join(block) + ")"
		
		if self.global_set:
			return 'forSet(OBJECTS_IN_ORDER, "%s", %s, %s, %s, "_count")' % (
				varname, param_pattern.toPython(), block_str, repr(self.group)
			)
		else:
			obj = self.args[-1]
			return '%s.forSet(%s, "%s", %s, %s, group=%s, count_var_name="_count")' % (
				obj, repr(self.field_name), varname, param_pattern.toPython(), block_str, repr(self.group)
			)

for named_code in ["", "( .* )"]:
	pgl(".CMD ::= toista jokaiselle .PATTERN-%d{ulkotulento} %s : -> for each $1:" % (
		asia.id, named_code
	), FuncOutput(lambda *p: ForParser(None, *p, global_set=True)))

	pgl(".CMD ::= toista jokaiselle ryhmälle samanlaisia .PATTERN-%d{osanto,monikko} %s : -> for each $1:" % (
		asia.id, named_code
	), FuncOutput(lambda *p: ForParser(None, *p, group=True, global_set=True)))

class RepeatParser:
	def __init__(self, end, start=None, var=None):
		self.end = end
		self.start = start
		self.var = var
	def parse(self, file, grammar, report=False):
		grammar = grammar.copy()
		
		counter = nextCounter("RepeatParser")
		varname = "i_" + str(counter)
		
		addParamPhrases(grammar, None, kokonaisluku, self.var, plural=False, varname=varname)
		
		block = parseBlock(file, grammar, report=report)
		return '[(%s) for %s in map(createIntegerObj, range(%s, %s.extra["int"]+1))]' % (
			", ".join(block), varname,
			self.start + '.extra["int"]' if self.start else "1",
			self.end
		)

pgl(".CMD ::= toista .EXPR-%d{nimento} kertaa : -> repeat $1 times:" % (kokonaisluku.id,),
	FuncOutput(RepeatParser))

pgl(".CMD ::= toista jokaiselle kokonaisluvulle ( .* ) välillä .EXPR-%d{sisaeronto} .EXPR-%d{sisatulento} : -> repeat $1 times:" % (
	kokonaisluku.id, kokonaisluku.id
), FuncOutput(lambda var, start, end: RepeatParser(end, start=start, var=var)))

# If-lause

def joinCodes(codes):
	if len(codes) == 1:
		return codes[0]
	elif len(codes) == 0:
		return "()"
	else:
		return "(" + ", ".join(codes) + ")[-1]"

class IfParser:
	def __init__(self, condition, category="CMD", force_else=False):
		self.condition = condition
		self.category = category
		self.force_else = force_else
	def parse(self, file, grammar, report=False):
		block = parseBlock(file, grammar, category=self.category, report=report)
		block_str = joinCodes(block)
		if self.force_else or (file.peekline() and file.peekline().lower() in ["muulloin:", "muuten:"]):
			file.accept("muulloin:", "muuten:")
			else_block = parseBlock(file, grammar, category=self.category, report=report)
			else_str = joinCodes(else_block)
			return "(%s if %s else %s)" % (block_str, self.condition[0], else_str)
		else:
			return "(%s and %s)" % (self.condition[0], block_str)

pgl(".CMD ::= jos .COND : -> if $1:", FuncOutput(IfParser))

# Kerran-lause

class OnceParser:
	def __init__(self, loop=False):
		self.loop = loop
	def parse(self, file, grammar, report=False):
		block = parseBlock(file, grammar, category="CMD", report=report)
		block_str = joinCodes(block)
		
		counter = nextCounter("OnceParser")
		once_id = "once_" + str(counter)

		code = "chooseByCounter(\"%s\", [lambda: %s, " % (once_id, block_str)
		
		while file.peekline() and file.peekline().lower() in ["sitten:"]:
			file.accept("sitten:")
			then_block = parseBlock(file, grammar, category="CMD", report=report)
			then_str = joinCodes(then_block)
			code += "lambda: %s, " % (then_str,)

		if not self.loop and file.peekline() and file.peekline().lower() in ["muulloin:", "muuten:"]:
			file.accept("muulloin:", "muuten:")
			else_block = parseBlock(file, grammar, category="CMD", report=report)
			else_str = joinCodes(else_block)
			code += "], else_block=lambda: %s)" % (else_str,)
		else:
			if self.loop:
				code += "], loop=True)"
			else:
				code += "])"

		return code

pgl(".CMD ::= kerran : -> once:", FuncOutput(OnceParser))
pgl(".CMD ::= ensin : -> once:", FuncOutput(lambda *p: OnceParser(*p, loop=True)))

# Tulostaminen

pgl(".CMD ::= sano .EXPR{nimento} . -> print($1)", FuncOutput(lambda x: 'say(' + x + '.asString())'))

# Pelin lopettaminen

pgl(".CMD ::= lopeta peli . -> end game", FuncOutput(lambda: 'endGame()'))

GRAMMAR_STACK[-1].addCategoryName("CMD", "komento")
	
# Valitsemiskomennot

pgl(".SELECTION-CMD ::= jos .COND : -> if $1:", FuncOutput(lambda cond: IfParser(cond, "SELECTION-CMD", True)))

SELECTION_VALUES = [
	("varmasti", "likely", 1000),
	("hyvin todennäköisesti", "likely", 100),
	("todennäköisesti", "likely", 10),
	("ehkä", "maybe", 0),
	("tuskin", "maybe", -10),
	("epätodennäköistä", "maybe", -10),
	("hyvin epätodennäköistä", "maybe", -10),
	("varmasti ei", "maybe", -1000),
]

def addSelectionValueCommand(phrase_pattern, english_name, value):
	pgl(".SELECTION-CMD ::= %s -> %s" % (phrase_pattern, english_name), FuncOutput(lambda: str(value)))

for t in SELECTION_VALUES:
	addSelectionValueCommand(*t)

GRAMMAR_STACK[-1].addCategoryName("SELECTION-CMD", "todennäköisyyslause")

class SelectionParser:
	def __init__(self, obj):
		self.obj = obj
	def parse(self, reader, grammar, report=False):
		grammar = grammar.copy()
		addParamPhrases(grammar, None, self.obj if isinstance(self.obj, RClass) else self.obj.rclass, None, varname="_arg")
		block = parseBlock(reader, grammar, category="SELECTION-CMD", report=report)
		self.obj.addSelectionRule("lambda _arg: " + joinCodes(block))

class ActionSelectionParser:
	def __init__(self, action, params):
		self.action = action
		self.params = params
	def parse(self, reader, grammar, report=False):
		grammar = grammar.copy()
		lambdaparams = []
		for i, (c, p, n) in enumerate(self.params):
			addParamPhrases(grammar, None, p.type(), n, varname="_" + str(i))
			lambdaparams.append("_" + str(i))
		block = parseBlock(reader, grammar, category="SELECTION-CMD", report=report)
		self.action.addSelectionRule(self.params, "lambda " + ", ".join(lambdaparams) + ": " + joinCodes(block))

pgl(".SELECTION-DEF ::= tarkoittaako pelaaja .CLASS{osanto} : -> does the player mean $1:", FuncOutput(lambda clazz: SelectionParser(clazz)))
pgl(".DEF ::= .SELECTION-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("SELECTION-DEF", "todennäköisyysmääritys")

# Komentojen jäsentäminen

def parseBlock(reader, grammar, category="CMD", report=False):
	line = reader.nextline()
	if line != "<indent>\0":
		sys.stderr.write("\nOdotettiin sisennystä rivillä %d.\n" % (reader.linenum))
		return []
	ans = []
	while True:
		line = reader.nextline()
		if line is None or line == "<dedent>\0":
			break
		del ERROR_STACK[:]
		ERROR_STACK.append([])
		alternatives = grammar.matchAll(tokenize(line), category, set())
		if len(alternatives) != 1:
			sys.stderr.write("\nVirhe jäsennettäessä riviä %d: `%s' (%s, %d vaihtoehtoa).\n" % (reader.linenum, line, category, len(alternatives)))
			reader.skipToDedent()
			for _, i in alternatives:
				print(i)
			for error in groupCauses(ERROR_STACK[-1]):
				error.print(finnish=True)
			break
		if alternatives[0][1][-1] == ":":
			ans.append(alternatives[0][0]().parse(reader, grammar, report=report))
		else:
			val = alternatives[0][0]()
			if val is not None:
				ans.append(val)
	return ans

# Tiedoston lataaminen

def takeWhitespace(string):
	ans = ""
	while string[0] in " \t":
		ans += string[0]
		string = string[1:]
	return ans

class FileReader:
	def __init__(self, file):
		self.lines = []
		self.times = []
		self.prev_time = 0
		self.profiling = False
		self.i = 0
		
		stack = [""]
		linenum = 0
		while True:
			linenum += 1
			line = file.readline()
			if not line:
				break
			if not line.strip() or line.strip()[0] == ">":
				continue
			indent = takeWhitespace(line)
			if len(indent) > len(stack[-1]):
				stack.append(indent)
				self.lines.append((linenum, "<indent>\0"))
			while len(indent) < len(stack[-1]):
				stack.pop()
				self.lines.append((linenum, "<dedent>\0"))
			if indent != stack[-1]:
				sys.stderr.write("Virheellinen sisennys rivillä %d.\n" % (linenum,))
			self.lines.append((linenum, line.strip()))
		self.maxlines = linenum
	def nextline(self):
		if self.profiling:
			if self.i > 0:
				t = time.time() - self.prev_time
				self.times.append(t)
			self.prev_time = time.time()
		else:
			self.times.append(0)
		if self.i == len(self.lines):
			return None
		linenum, line = self.lines[self.i]
		self.linenum = linenum
		self.i += 1
		return line
	def peekline(self):
		if self.i == len(self.lines):
			return None
		_, line = self.lines[self.i]
		return line
	def accept(self, *lines):
		line = self.nextline()
		if not line or line.lower() not in lines:
			sys.stderr.write("Virhe jäsennettäessä tiedoston riviä %d: `%s'. Odotettiin riviä `%s'." % (
				self.linenum,
				line,
				"' tai `".join(lines)
			))
	def skipToDedent(self):
		while True:
			line = self.nextline()
			if line is None or line == "<dedent>\0":
				break
	def profile(self):
		self.profiling = True
	def printProfilingData(self):
		for t, line in sorted(zip(self.times, self.lines)):
			print("`" + line[1] + "'", t, "s")

def loadFile(file, report=True):
	reader = FileReader(file)
	while True:
		line = reader.nextline()
		if report:
			sys.stderr.write("\rLadataan tiedostoa " + file.name + " (%.2f %%)" % (reader.linenum / reader.maxlines * 100))
		if line is None:
			break
		if line == "<indent>":
			sys.stderr.write("Odottamaton sisennys rivillä %d.\n" % (reader.linenum))
			reader.skipToDedent()
			continue
		if re.fullmatch(r'"[^"]+"', line):
			string = line[1:-1].replace("'", '"')
			obj = OBJECTS_IN_ORDER[-1]
			obj.data["kuvaus"] = createStringObj(string)
			continue
		del ERROR_STACK[:]
		ERROR_STACK.append([])
		a = getCombinedGrammar().matchAll(tokenize(line), "DEF", set())
		if len(a) == 1:
			t = a[0][0]()
			if a[0][1][-1] == ":":
				t.parse(reader, getCombinedGrammar(), report=True)
		else:
			sys.stderr.write("\nVirhe jäsennettäessä riviä %d: `%s' (DEF, %d vaihtoehtoa).\n" % (reader.linenum, line, len(a)))
			for _, i in a:
				print(i)
			for error in groupCauses(ERROR_STACK[-1]):
				error.print(finnish=True)
			
	if report:
		sys.stderr.write("\rLadataan tiedostoa " + file.name + " (100.00 %)\n")

# Tiedoston tuominen

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # Hakemisto, jossa retken mukana olevat tiedostot ovat
PATH = [SCRIPT_DIR]
LOADED_FILES = []

def importFile(filename):
	# kokeillaan onko tiedosto missään hakuhakemistossa (mm. SCRIPT_DIR)
	for directory in PATH:
		for suffix in ["retki", "txt"]:
			path = os.path.join(directory, filename + "." + suffix)
			if os.path.isfile(path):
				filename = path
				break
		else:
			continue
		break
	
	if not os.path.isfile(filename):
		sys.stderr.write("\rTiedostoa ei löytynyt: %s (hakuhakemistot: %s)\n" % (filename, repr(PATH)))
		return
	
	if filename in LOADED_FILES:
		return
	LOADED_FILES.append(filename)
	
	with open(filename, "r") as file:
		loadFile(file)

pgl(".IMPORT-DEF ::= Tuo .* . -> import $1", FuncOutput(lambda file: importFile("".join(t.token for t in file))))
pgl(".DEF ::= .IMPORT-DEF -> $1", identity)
GRAMMAR_STACK[-1].addCategoryName("IMPORT-DEF", "tuontikäsky")

# Standardikirjasto

def loadStandardLibrary():
	importFile("std")

# Kääntäminen

def compileAll(file=sys.stdout):
	compiled_classes = [cl.toPython() for cl in CLASSES_IN_ORDER]
	compiled_objects = [ob.toPython() for ob in getObjects()]
	print("from suomilog.patternparser import Grammar, Token", file=file)
	print("from suomilog.finnish import addNounToDictionary", file=file)
	print("from retki.language import *", file=file)
	for noun in NOUNS:
		print("addNounToDictionary(%s)" % (repr(noun),), file=file)
	print("OBJECTS = {}", file=file)
	print("GRAMMAR = Grammar()", file=file)
	for decl, _ in compiled_classes+compiled_objects:
		if decl:
			print(decl, file=file)
	for _, code in compiled_classes+compiled_objects:
		if code:
			print(code, file=file)
	for key in GLOBAL_SCOPE.variables:
		obj = GLOBAL_SCOPE.variables[key]
		print('GLOBAL_SCOPE.variables[%s] = %s' % (repr(key), obj.toPythonRef()), file=file)
	for key in ACTIONS:
		print(ACTIONS[key].toPython(), file=file)
	for listener in ACTION_LISTENERS:
		if not listener.disabled:
			print(listener.toPython(), file=file)
	for var, dicti in [("CHECKS", CHECKS), ("MODIFYS", MODIFYS)]:
		for key in dicti:
			print('%s[%s] = %s' % (var, repr(key), dicti[key]), file=file)
	print("playGame(GRAMMAR)", file=file)

# Pääohjelma

def compileFile(infile, outfile):
	saveObjects()
	loadStandardLibrary()
	PATH.insert(0, os.path.dirname(os.path.realpath(infile.name)))
	loadFile(infile)
	compileAll(outfile)

def interactive():
	saveObjects()
	loadStandardLibrary()

	def complete_file(t, s):
		path, file = os.path.split(t)
		alternatives = []
		try:
			for c in sorted(["/kielioppi", "/käsitteet", "/debug ", "/virheet", "/match ", "/eval ", "/lataa ", "/käännä", "/pelitila", "/komentotila", "/määrittelytila"]):
				if c.startswith(t):
					alternatives.append(c)
			for f in filter(lambda f: f.startswith(file), os.listdir(path or ".")):
				alt = os.path.join(path, f)
				if os.path.isdir(alt):
					alternatives.append(os.path.join(alt, ""))
				else:
					alternatives.append(alt)
			return alternatives[s] if s < len(alternatives) else None
		except Exception as e:
			print(e)
	readline.set_completer(complete_file)
	readline.set_completer_delims(" ")
	readline.parse_and_bind('tab: complete')
	
	def printStatistics():
		n_patterns = sum([len(category) for category in GRAMMAR_STACK[-1].patterns.values()])
		print("Ladattu", n_patterns, "fraasia.")
	
	mode = ["DEF", "CMD", "PLAYER-CMD"]
	mode_chars = ["!", "?"]
	
	printStatistics()
	while True:
		try:
			line = input(">> ")
		except EOFError:
			break
		if not line:
			continue
		if line == "/kielioppi":
			GRAMMAR_STACK[-1].print()
			print("Kielioppipinossa on %d kielioppi%s." % (len(GRAMMAR_STACK), "a" if len(GRAMMAR_STACK) != 1 else ""))
			continue
		elif line == "/käsitteet":
			def printClass(clazz, indent):
				print(" "*indent + clazz.name + "{" + ", ".join(sorted(clazz.fields.keys())) + "}")
				for subclass in sorted(clazz.direct_subclasses, key=lambda c: c.name):
					printClass(subclass, indent+1)
			printClass(yläkäsite, 0)
			continue
		elif line == "/debug 0":
			setDebug(0)
			continue
		elif line == "/debug 1":
			setDebug(1)
			continue
		elif line == "/debug 2":
			setDebug(2)
			continue
		elif line == "/debug 3":
			setDebug(3)
			continue
		elif line == "/virheet":
			errors = groupCauses(ERROR_STACK[-1])
			if len(errors) > 0:
				print("Mahdollisia virheitä:")
				for error in errors:
					error.print(finnish=True)
			else:
				print("Ei virheitä.")
			continue
		elif line.startswith("/match"):
			args = line[6:].strip()
			cat = args[:args.index(" ")]
			expr = args[args.index(" ")+1:]
			print("Matching `%s' ~ .%s" % (expr, cat))
			ints = getCombinedGrammar().matchAll(tokenize(expr), cat, set())
			for _, string in ints:
				print(string)
			continue
		elif line.startswith("/eval"):
			try:
				print(eval(line[5:].strip()))
			except:
				traceback.print_exc()
			continue
		elif line.startswith("/lataa"):
			try:
				importFile(line[6:].strip())
			except:
				traceback.print_exc()
			printStatistics()
			continue
		elif line == "/käännä":
			compileAll()
			continue
		elif line.startswith("/pelitila"):
			mode = ["PLAYER-CMD", "CMD", "DEF"]
			continue
		elif line.startswith("/komentotila"):
			mode = ["CMD", "DEF", "PLAYER-CMD"]
			continue
		elif line.startswith("/määrittelytila"):
			mode = ["DEF", "CMD", "PLAYER-CMD"]
			continue
		del ERROR_STACK[:]
		ERROR_STACK.append([])
		phrase_type = mode[0]
		if line[0] in mode_chars:
			phrase_type = mode[mode_chars.index(line[0])+1]
			line = line[1:]
		silent = mode[0] == phrase_type == "PLAYER-CMD"
		interpretations = getCombinedGrammar().matchAll(tokenize(line), phrase_type, set())
		if len(interpretations) == 0:
			print("Ei tulkintaa.")
		elif len(interpretations) == 1:
			if not silent:
				print(interpretations[0][1])
			try:
				string = interpretations[0][0]()
				if not silent:
					print(string)
				if string:
					eval(string)
			except:
				traceback.print_exc()
				for name in STACK_NAMES:
					print(name)
				del STACK_NAMES[:]
		else:
			print("Löydetty", len(interpretations), "tulkintaa:")
			for _, interpretation in interpretations:
				print(interpretation)
		if not mode[0] == phrase_type == "PLAYER-CMD":
			printStatistics()
		else:
			# tulosta rivinvaihto, sillä peli ei ole välttämättä tulostanut sellaista
			print()

def main():
	parser = argparse.ArgumentParser(description='Finnish Interactive Fiction language inspired by Inform 7')
	parser.add_argument('input', type=argparse.FileType('r'), nargs='?', help='source code file')
	parser.add_argument('--output', "-o", type=argparse.FileType('w'), nargs='?', help='target code file')
	
	args = parser.parse_args()
	
	output = args.output or sys.stdout
	
	if args.input:
		compileFile(args.input, output)
	else:
		interactive()
