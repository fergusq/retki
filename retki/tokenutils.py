# Retki
# Copyright (C) 2018 Iikka Hauhio
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

from collections import defaultdict
from typing import AbstractSet
import pypykko.utils as pykko
from suomilog.finnish import SINGULAR_AND_PLURAL_CASES, inflect_nominal, baseformAndBits
from suomilog.grammar import Token, match_bits

def nameToBaseform(tokens: list[Token], bits: set[str] | None, rbits: set[str]):
	ans = []
	found = False
	for token in reversed(tokens):
		for bf, tbits in token.alternatives:
			if not found:
				if rbits <= tbits:
					ans.append((bf, bits or {"$"}))
					found = True
					break
			else:
				if rbits <= tbits and (tbits & {"adjectival", ":pronoun", ":numeral"}):
					ans.append((bf, bits or {"$"}))
					break
		else:
			ans.append((token.surfaceform, set()))
	return reversed(ans)

def tokensToString(tokens: list[Token], rbits={"+nom", "+sg"}):
	return " ".join([text for text, bits in nameToBaseform(tokens, set(), rbits)])

def tokensToInflectedString(tokens: list[Token], case: str, rbits={"+nom", "+sg"}):
	return " ".join([
		list(inflect_nominal(text, ("+pl" if "+pl" in rbits else "+sg"), case) or {text})[0]
		if "$" in bit else text
		for text, bit in nameToBaseform(tokens, set(), rbits)
	])

def nameToCode(name: list[Token], bits: set[str] | None = None, rbits={"+nom", "+sg"}):
	return " ".join([token + ("{" + ",".join(tbits) + "}" if tbits else "") for token, tbits in nameToBaseform(name, bits, rbits)])

def tokensToCode(tokens: list[Token]):
	return " ".join([token.surfaceform for token in tokens])

DICTIONARY: defaultdict[str, list[tuple[str, set[str]]]] = defaultdict(list)

def addNounToDictionary(noun: str):
	for plural in ["+sg", "+pl"]:
		for case in SINGULAR_AND_PLURAL_CASES:
			DICTIONARY[list(inflect_nominal(noun, plural, case))[0].lower()].append((noun, {case, plural}))

def split2tokens(text: str) -> list[str]:
	tokens = [""]
	for char, next_char in zip(text, text[1:]+" "):
		if char.isalnum() or char == "-" or char == ":" and next_char.isalpha():
			tokens[-1] = tokens[-1] + char
		
		else:
			tokens.append(char)
			tokens.append("")

	return [t for t in tokens if t]

def get_pykko_analyses(token: str) -> list[pykko.PykkoAnalysis]:
	if token == token.capitalize():
		analyses = pykko.analyze(token.lower(), only_best=False)
		analyses += pykko.analyze(token)
	else:
		analyses = pykko.analyze(token)

	# Poistetaan arvaimen tulokset paitsi jos kaikki on arvattua
	if not all("Guesser" in a.source for a in analyses):
		analyses = [a for a in analyses if "Guesser" not in a.source]

	# Nämä sanat on kielletty elleivät ne ole ainoita tulkintoja
	# Muuten esim. "lasi" -> la + omistusliite
	banned_words = {"do", "re", "mi", "fa", "so", "la", "si"}
	if not all((set(a.lemma.split("|")) & banned_words) for a in analyses):
		analyses = [a for a in analyses if not (set(a.lemma.split("|")) & banned_words)]

	# Kielletään myös omistusliitteet
	for poss in ["+poss1sg", "+poss2sg", "+poss1pl", "+poss2pl"]:
		if not all(poss in a.morphtags for a in analyses):
			analyses = [a for a in analyses if poss not in a.morphtags]

	# Pykko antaa joskus hyvin harvinaisia tulkintoja
	# Esim. "avoin" on sen mielestä sana "avo" ⟨rare⟩
	for info in ["rare", "poet", "dial", "coll"]:
		if not all(info in a.info for a in analyses):
			analyses = [a for a in analyses if info not in a.info]
	
	return analyses

def tokenize(text: str) -> list[Token]:
	tokens: list[Token] = []
	token: str
	for token in split2tokens(text):
		if token.strip() == "":
			continue

		alternatives: list[tuple[str, set[str]]] = []
		analyses = get_pykko_analyses(token)

		for word in analyses:
			baseform, bits = baseformAndBits(word)
			if bits & {":adjective", "+part_ma", ":adjective", ":participle"}:
				bits |= {"adjectival"}
			baseform = baseform.replace("|", "")
			if not (bits & {":proper", ":proper-pl"}) and baseform == baseform.capitalize():
				baseform = baseform.lower()
			alternatives.append((baseform, bits))

		# Jos sana löytyy suomilogin omasta sanakirjasta, lisää myös sieltä vaihtoehdot
		if token.lower() in DICTIONARY:
			alternatives += DICTIONARY[token.lower()]

		tokens.append(Token(token, alternatives))

	return tokens

def baseform(token: Token, bits: AbstractSet[str]) -> str | None:
	for baseform, tbits in token.alternatives:
		if match_bits(tbits, bits):
			return baseform

	return None

def tokenBits(token: Token) -> set[str]:
	bits = set()
	for _, tbits in token.alternatives:
		bits |= tbits

	return bits