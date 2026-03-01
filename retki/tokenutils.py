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
from pypykko.tokenizer import text2tokens as pykko_tokenize
from suomilog.finnish import inflect_nominal, baseformAndBits
from suomilog.grammar import Token, match_bits

def nameToBaseform(tokens: list[Token], bits, rbits):
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
				if rbits <= tbits and tbits & {":adjective", "+part_ma", ":adjective", ":numeral", ":participle"}:
					ans.append((bf, bits or {"$"}))
					break
		else:
			ans.append((token.surfaceform, set()))
	return reversed(ans)

def tokensToString(tokens, rbits={"+nom", "+sg"}):
	return " ".join([text for text, bits in nameToBaseform(tokens, {}, rbits)])

def tokensToInflectedString(tokens, case: str, rbits={"+nom", "+sg"}):
	return " ".join([
		list(inflect_nominal(text, ("+pl" if "+pl" in rbits else "+sg"), case) or {text})[0]
		if "$" in bit else text
		for text, bit in nameToBaseform(tokens, {}, rbits)
	])

def nameToCode(name, bits=None, rbits={"+nom", "+sg"}):
	return " ".join([token + ("{" + ",".join(tbits) + "}" if tbits else "") for token, tbits in nameToBaseform(name, bits, rbits)])

def tokensToCode(tokens):
	return " ".join([token.toCode() for token in tokens])

DICTIONARY: defaultdict[str, list[Token]] = defaultdict(list)

def tokenize(text: str) -> list[Token]:
	tokens: list[Token] = []
	token: str
	for token in pykko_tokenize(text):
		if token.strip() == "":
			continue

		alternatives = []
		for word in pykko.analyze(token):
			baseform, bits = baseformAndBits(word)
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