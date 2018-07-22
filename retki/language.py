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

import sys, readline
import math
from suomilog.finnish import tokenize
from .tokenutils import *

# Bittiluokka

class Bits:
	def __init__(self, bits=None):
		self.bits = bits or set()
	def bitOn(self, bit):
		self.bits.add(bit)
		return self
	def bitOff(self, bit):
		if bit in self.bits:
			self.bits.remove(bit)
		return self
	def bitsOn(self, bits):
		for bit in bits:
			self.bitOn(bit)
		return self
	def bitsOff(self, bits):
		for bit in bits:
			self.bitOff(bit)
		return self

# Evaluominen

def evalOrCall(f, p):
	if isinstance(f, str):
		return eval(f)(*p)
	else:
		return f(*p)

# Ulostulo

class FuncOutput:
	def __init__(self, f):
		self.func = f
	def eval(self, args):
		return lambda: self.func(*[arg() for arg in args])

identity = FuncOutput(lambda x: x)

class SumOutput:
	def __init__(self, f=lambda: 0):
		self.f = f
	def eval(self, args):
		return sum(args) + self.f()

# Pythoniksi muuntamista varten

def toPython(obj):
	if "toPython" in dir(obj):
		return obj.toPython()
	elif isinstance(obj, list):
		return "[" + ", ".join([toPython(val) for val in obj]) + "]"
	elif isinstance(obj, tuple):
		return "(" + ", ".join([toPython(val) for val in obj]) + ("," if len(obj) == 1 else "") + ")"
	else:
		return repr(obj)

# Olioluokka

OBJECTS = None

def saveObjects():
	global OBJECTS
	OBJECTS = {}

def getObjects():
	return OBJECTS.values()
	
OBJECTS_IN_ORDER = []

def searchLastObject(pattern):
	for obj in reversed(OBJECTS_IN_ORDER):
		if pattern.matches(obj):
			return obj
	return None

class RObject(Bits):
	def __init__(self, rclass, name, bits=None, obj_id=None, extra=None, name_tokens=None, srules=None, aliases=None, data=None):
		Bits.__init__(self, bits)
		if not obj_id:
			increaseCounter()
			self.id = getCounter()
		else:
			self.id = obj_id
		if OBJECTS is not None and not rclass.primitive:
			OBJECTS[self.id] = self
		if not rclass.primitive:
			OBJECTS_IN_ORDER.append(self)
		self.rclass = rclass
		self.data = data or {}
		self.extra = extra or {}
		self.name = name
		self.name_tokens = name_tokens
		self.aliases = aliases or []
		self.selection_rules = srules or []
		if name and "nimi koodissa" not in self.data:
			self.data["nimi koodissa"] = createStringObj(name)
	def __repr__(self):
		return self.asString()
	def copy(self):
		data_copy = {}
		for key in self.data:
			if isinstance(self.data[key], RObject):
				data_copy[key] = self.data[key]
			elif isinstance(self.data[key], dict):
				data_copy[key] = self.data[key].copy()
			elif isinstance(self.data[key], set):
				data_copy[key] = self.data[key].copy()
			else:
				raise Exception("not implemented")
		return RObject(
			self.rclass, self.name, self.bits.copy(),
			extra=self.extra.copy(), name_tokens=self.name_tokens, srules=self.selection_rules.copy(),
			data=data_copy
		)
	def toPythonRef(self):
		if self.rclass.primitive:
			return evalOrCall(self.rclass.primitive, [self])
		else:
			return 'OBJECTS[' + repr(self.id) + ']'
	def toPython(self):
		if self.rclass.primitive:
			return "", ""
		
		var = 'OBJECTS[' + repr(self.id) + ']'
		
		# muodostetaan parserisäännöt aliaksista ja
		names = self.aliases.copy()
		if self.name_tokens:
			names.append(self.name_tokens)
		if self.rclass.name_tokens:
			names.append(self.rclass.name_tokens)
		
		grammar = ""
		for name in names:
			grammar += ";GRAMMAR.parseGrammarLine('.EXPR-%d ::= %s', FuncOutput(lambda: (%s, %s.likeliness())))" % (
				self.rclass.id,
				nameToCode(name, bits={"$"}, rbits={"nimento", "yksikkö"}),
				var, var
			)
		
		# ulostulo on tuple, jonka ensimmäinen arvo luo olion ja parserisäännöt, ja toinen arvo luo kentät
		return (
			# ensimmäinen arvo:
			'%s = RObject(CLASSES[%s], %s, %s, %s, %s, %s, %s)' % (
				var,
				repr(self.rclass.name), repr(self.name),
				repr(self.bits), repr(self.id), toPython(self.extra),
				repr(self.name_tokens),
				"[" + ", ".join(self.selection_rules) + "]")
			+ grammar,
			# toinen arvo:
			";".join([
				# olioviittauskentät
				'%s.data[%s] = %s' % (var, repr(key), self.data[key].toPythonRef()) for key in self.data if isinstance(self.data[key], RObject)
			] + [
				# karttakentät
				'%s.data[%s] = {%s}' % (
					var,
					repr(key),
					", ".join([keykey.toPythonRef() + ": " + self.data[key][keykey].toPythonRef() for keykey in self.data[key]])
				)
				for key in self.data if isinstance(self.data[key], dict)
			] + [
				# joukkokentät
				'%s.data[%s] = {%s}' % (var, repr(key), ", ".join([val.toPythonRef() for val in self.data[key]]))
				for key in self.data if isinstance(self.data[key], set)
			])
		)
	def equals(self, obj):
		if self.id == obj.id:
			return True
		if self.name != obj.name:
			return False
		if self.rclass != obj.rclass:
			return False
		if len(self.data) != len(obj.data):
			return False
		for key in self.data:
			if key not in obj.data or not self.data[key].quickEquals(obj.data[key]):
				return False
		if self.extra != obj.extra:
			return False
		return True
	def quickEquals(self, obj):
		return self.id == obj.id or self.rclass == obj.rclass and self.rclass.primitive and self.extra == obj.extra
	def get(self, field_name):
		if field_name not in self.data:
			for clazz in self.rclass.superclasses():
				if field_name in clazz.fields and clazz.fields[field_name].default_value:
					self.data[field_name] = clazz.fields[field_name].default_value
					break
			else:
				self.data[field_name] = None
		return self.data[field_name]
	def set(self, field_name, val):
		self.data[field_name] = val
	def getMap(self, field_name, key_val):
		key = key_val.toKey()
		if field_name not in self.data:
			self.data[field_name] = {}
		if key not in self.data[field_name]:
			for clazz in self.rclass.superclasses():
				if field_name in clazz.fields and clazz.fields[field_name]:
					return clazz.fields[field_name].default_value
			return None
		return self.data[field_name][key]
	def setMap(self, field_name, key_val, val):
		key = key_val.toKey()
		if field_name not in self.data:
			self.data[field_name] = {}
		self.data[field_name][key] = val
	def appendSet(self, field_name, val):
		if field_name not in self.data:
			self.data[field_name] = set()
		field = self.data[field_name]
		if isinstance(val, RPattern):
			if not self.containsSet(field_name, val):
				field.add(val.newInstance(tokenize("uusi arvo")))
		else:
			field.add(val)
	def removeSet(self, field_name, val):
		if field_name not in self.data:
			return
		field = self.data[field_name]
		if isinstance(val, RPattern):
			for obj in field:
				if val.matches(obj):
					field.remove(obj)
		else:
			if val in field:
				field.remove(val)
	def containsSet(self, field_name, val):
		if field_name not in self.data:
			return False
		field = self.data[field_name]
		if isinstance(val, RPattern):
			if val.obj:
				return val.obj in field and val.matches(val.obj)
			else:
				for obj in field:
					if val.matches(obj):
						return True
				return False
		else:
			return val in field
	def forSet(self, field_name, var_name, pattern, f, group=False, count_var_name=None):
		if field_name not in self.data:
			return []
		pushScope()
		ans = []
		if not group:
			for val in self.data[field_name]:
				if pattern.matches(val):
					putVar(var_name, val)
					ans.append(f())
		else:
			# TODO
			groups = []
			for val in self.data[field_name]:
				if pattern.matches(val):
					for group in groups:
						if group[0].equals(val):
							group.append(val)
							break
					else:
						groups.append([val])
			for group in groups:
					putVar(count_var_name, createIntegerObj(len(group)))
					putVar(var_name, group[0])
					ans.append(f())
		popScope()
		return ans
	def onceSet(self, field_name, var_name, pattern, f):
		if field_name not in self.data:
			return False
		pushScope()
		for val in self.data[field_name]:
			if pattern.matches(val):
				putVar(var_name, val)
				if f():
					return True
		popScope()
		return False
	def createCopies(self, n, condition):
		for i in range(n):
			obj = self.copy()
			condition.doModify(obj)
	def setExtra(self, name, data):
		self.extra[name] = data
		return self
	def addSelectionRule(self, rule):
		self.selection_rules.append(rule)
	def addVariableAlias(self, alias):
		self.aliases.append(alias)
	def likeliness(self):
		ans = 0
		for rule in self.selection_rules:
			ans += evalOrCall(rule, [self])
		return ans
	def asString(self, case="nimento", capitalized=False):
		do_lower = True
		if case != "nimento":
			if self.name_tokens:
				name_tokens = self.name_tokens
			elif self.name:
				name_tokens = tokenize(self.name)
			elif "str" in self.extra:
				name_tokens = tokenize(self.extra["str"])
				do_lower = False
			elif "int" in self.extra:
				name_tokens = tokenize(str(self.extra["int"]))
				do_lower = False
			else:
				name_tokens = self.rclass.name_tokens or tokenize(self.rclass.name)
			ans = tokensToInflectedString(name_tokens, case)
		elif self.name:
			ans = self.name
		elif "str" in self.extra:
			ans = self.extra["str"]
			do_lower = False
		elif "int" in self.extra:
			ans = str(self.extra["int"])
			do_lower = False
		else:
			ans = "[eräs " + self.rclass.name + "]"
		if capitalized:
			return ans.capitalize()
		elif do_lower:
			return ans.lower()
		else:
			return ans
	def toKey(self):
		if "str" in self.extra:
			return self.extra["str"]
		else:
			return self

# Luokat

class Counter:
	counter = 0

def increaseCounter():
	Counter.counter += 1

def getCounter():
	return Counter.counter

CLASSES = {}
CLASSES_IN_ORDER = []

class RClass(Bits):
	def __init__(self, name, superclass, name_tokens, class_id=None, bit_groups=None, bits=None, primitive=None):
		Bits.__init__(self, bits)
		
		CLASSES[name] = self
		CLASSES_IN_ORDER.append(self)
		
		if class_id:
			self.id = class_id
		else:
			increaseCounter()
			self.id = getCounter()
		self.name = name
		self.name_tokens = name_tokens
		self.superclass = superclass
		self.direct_subclasses = []
		self.fields = {}
		self.bit_groups = bit_groups or []
		self.attributePhraseAdders = []
		self.selection_rules = []
		self.primitive = primitive
		
		if superclass:
			self.superclass.direct_subclasses.append(self)
	def toPython(self):
		sc = "None" if self.superclass is None else "CLASSES[" + repr(self.superclass.name) + "]"
		grammar = "" if self.superclass is None else 'GRAMMAR.parseGrammarLine(".EXPR-%d ::= .EXPR-%d{$}", identity)' % (self.superclass.id, self.id)
		return (
			'RClass(%s, %s, %s, %d, %s, %s, %s);%s' % (
				repr(self.name), sc, repr(self.name_tokens), self.id, repr(self.bit_groups), repr(self.bits), self.primitive,
				grammar
			),
			";".join('CLASSES[%s].fields[%s] = %s' % (repr(self.name), repr(field), self.fields[field].toPythonExpr()) for field in self.fields)
		)
	def addField(self, name, field):
		self.fields[name] = field
	def addSelectionRule(self, rule):
		self.selection_rules.append(rule)
	def newInstance(self, name=None, bitsOn=set(), bitsOff=set(), name_tokens=None):
		srules = []
		for clazz in self.superclasses():
			srules += clazz.selection_rules
		return RObject(self, name, (self.allBits()|bitsOn)-bitsOff, name_tokens=name_tokens, srules=srules)
	def superclasses(self):
		if self.superclass == None:
			return [self]
		else:
			return [self] + self.superclass.superclasses()
	def subclasses(self):
		ans = [self]
		for subclass in self.direct_subclasses:
			ans += subclass.subclasses()
		return ans
	def allBits(self):
		ans = set()
		for clazz in self.superclasses():
			ans.update(clazz.bits)
		return ans
	def nameToCode(self, bits):
		if self.name_tokens:
			return nameToCode(self.name_tokens, rbits={"nimento", "yksikkö"}, bits=bits)
		else:
			return self.name + "{" + ",".join(bits) + "}"

class RField:
	def __init__(self, counter, name, vtype, defa=None, is_map=False):
		self.id = counter
		self.name = name
		self.type = vtype
		self.is_map = is_map
		self.default_value = defa
	def toPythonExpr(self):
		defa = "None" if not self.default_value else self.default_value.toPythonRef()
		return 'RField(%d, %s, CLASSES[%s], %s, %s)' % (self.id, repr(self.name), repr(self.type.name), defa, repr(self.is_map))
	def setDefaultValue(self, defa):
		self.default_value = defa
	def copy(self):
		return RField(self.id, self.name, self.type, None, self.is_map)

class RPattern:
	def __init__(self, rclass=None, bitsOn=None, bitsOff=None, conditions=None, obj=None):
		self.rclass = rclass
		self.conditions = conditions or []
		self.my_bitsOn = bitsOn or set()
		self.my_bitsOff = bitsOff or set()
		self.obj = obj
	def toPython(self):
		clazz = "None" if not self.rclass else "CLASSES[" + repr(self.rclass.name) + "]"
		obj = "None" if not self.obj else self.obj.toPythonRef()
		return ("RPattern(" + clazz + ", "
			+ repr(self.my_bitsOn) + ", " + repr(self.my_bitsOff)
			+ ", " + toPython(self.conditions) + ", " + obj + ")")
	def addCondition(self, cond):
		self.conditions.append(cond)
		return self
	def bitOn(self, bit):
		self.my_bitsOn.add(bit)
		return self
	def bitOff(self, bit):
		self.my_bitsOff.add(bit)
		return self
	def bitsOff(self, bits):
		for bit in bits:
			self.bitOff(bit)
		return self
	def newInstance(self, name):
		name_str = tokensToString(name)
		if self.obj:
			obj = self.obj
			obj.bitsOff(self.my_bitsOff)
			obj.bitsOn(self.my_bitsOn)
		else:
			obj = self.rclass.newInstance(name=name_str, name_tokens=name, bitsOn=self.my_bitsOn, bitsOff=self.my_bitsOff)
		for cond in self.conditions:
			cond.doModify(obj)
		return obj
	def modify(self, obj):
		if obj.rclass != self.rclass:
			sys.stderr.write("Yritettiin muuttaa " + obj.asString() + " (" + obj.rclass.name + ") tyyppiin " + self.rclass.name)
		obj.bitsOff(self.my_bitsOff)
		obj.bitsOn(self.my_bitsOn)
		for cond in self.conditions:
			cond.doModify(obj)
	def matches(self, obj):
		if self.obj:
			if not obj == self.obj:
				return False
		if self.rclass:
			if obj.rclass not in self.rclass.subclasses():
				return False
		for cond in self.conditions:
			if not cond.doCheck(obj):
				return False
		return obj.bits >= self.my_bitsOn and not (obj.bits&self.my_bitsOff)
	def type(self):
		return self.rclass or (self.obj and self.obj.rclass) or CLASSES["asia"]

class RCondition:
	def __init__(self, var, check, modify):
		self.var = var
		self.check = check
		self.modify = modify
	def toPython(self):
		return "RCondition(" + repr(self.var) + ", lambda " + self.var + ": " + self.check + ", lambda " + self.var + ": " + self.modify + ")"
	def doCheck(self, x):
		if isinstance(self.check, str):
			return eval(self.check, globals(), {self.var: x})
		else:
			return self.check(x)
	def doModify(self, x):
		if isinstance(self.modify, str):
			return eval(self.modify, globals(), {self.var: x})
		else:
			return self.modify()

CHECKS = {}
MODIFYS = {}

# Näkyvyysalueet ja muuttujat

class RScope(Bits):
	def __init__(self):
		Bits.__init__(self)
		self.variables = {}
	def __repr__(self):
		return "Scope(" + repr(self.variables) + ")"

ALIASES = {}
GLOBAL_SCOPE = RScope()
SCOPE = []
STACK = []
STACK_NAMES = []
ACTION_STACK = [RScope()]

def pushScope():
	SCOPE.append(RScope())
def popScope():
	SCOPE.pop()
def pushStackFrame(name):
	STACK.append(RScope())
	STACK_NAMES.append(name)
def popStackFrame():
	STACK.pop()
	STACK_NAMES.pop()
def pushAction():
	ACTION_STACK.append(RScope())
def popAction():
	ACTION_STACK.pop()
def visibleScopes():
	return [GLOBAL_SCOPE]+SCOPE+STACK[-1:]
def getVar(name):
	for scope in reversed(visibleScopes()):
		if name in scope.variables:
			return scope.variables[name]
	raise Exception("Muuttujaa ei löytynyt: " + name + "(" + repr(visibleScopes()) + ")\n")
def setVar(name, val):
	scopes = visibleScopes()
	for scope in reversed(scopes):
		if name in scope.variables:
			scope.variables[name] = val
			break
	else:
		scopes[-1].variables[name] = val
def putVar(name, val):
	visibleScopes()[-1].variables[name] = val
def addAlias(name, alias):
	if name not in ALIASES:
		ALIASES[name] = []
	ALIASES[name].append(alias)

# Toiminnot

class RAction:
	def __init__(self, name, a_id=None, srules=None):
		if not a_id:
			increaseCounter()
		self.id = a_id or getCounter()
		self.name = name
		
		ACTIONS[self.id] = self
		ACTIONS_BY_NAME[name] = self
		
		self.commands = []
		self.listeners = []
		self.selection_rules = srules or []
	def toPython(self):
		return ";".join([
			"RAction(" + repr(self.name) + ", " + repr(self.id)
			+ ", [" + ", ".join(["(" + toPython(p) + ", " + r + ")" for p, r in self.selection_rules]) + "])"
		] + [
			("GRAMMAR.parseGrammarLine('.PLAYER-CMD ::= %s', "
			+ "FuncOutput(lambda *x: (lambda: ACTIONS[%d].run([p for p, _ in x]), ACTIONS[%d].likeliness([p for p, _ in x]) + sum([p for _, p in x]))))")
			% (pattern, self.id, self.id) for pattern in self.commands
		])
	def addPlayerCommand(self, pattern):
		self.commands.append(pattern)
	def addSelectionRule(self, params, rule):
		self.selection_rules.append((params, rule))
	def likeliness(self, args):
		ans = 0
		for params, rule in self.selection_rules:
			if allPatternsMatch(args, params):
				ans += evalOrCall(rule, args)
		return ans
	def run(self, args, in_scope=False):
		listeners = []
		for listener in self.listeners:
			if listener.action is self and allPatternsMatch(args, listener.params):
				listeners.append(listener)
		if not in_scope:
			pushAction()
		scope = ACTION_STACK[-1]
		special_case_found = False
		for listener in sorted(listeners, key=lambda l: l.priority):
			if listener.is_general_case and special_case_found:
				continue
			if listener.is_special_case:
				special_case_found = True
			listener.run(args)
			if "stop action" in scope.bits:
				break
		if not in_scope:
			popAction()

def allPatternsMatch(args, params):
	return all([p.matches(obj) for obj, (_, p, _) in zip(args, params)])

ACTIONS = {}
ACTIONS_BY_NAME = {}

class RListener:
	def __init__(self, action, params, priority, is_special_case, is_general_case, body):
		self.action = action
		self.params = params
		self.priority = priority
		self.is_special_case = is_special_case
		self.is_general_case = is_general_case
		self.body = body
		ACTION_LISTENERS.append(self)
		action.listeners.append(self)
	def toPython(self):
		return "".join(['RListener(',
			'ACTIONS[', repr(self.action.id), '], ',
			toPython(self.params), ', ',
			repr(self.priority), ', ',
			repr(self.is_special_case), ', ',
			repr(self.is_general_case), ', ',
			'[', ", ".join(["lambda: " + cmd for cmd in self.body]) + ']'
			')'
		])
	def run(self, args):
		pushStackFrame(self.action.name)
		for i, ((c, _, _), a) in enumerate(zip(self.params, args)):
			putVar("_" + str(i), a)
		for cmd in self.body:
			if isinstance(cmd, str):
				eval(cmd)
			else:
				cmd()
			if "stop action" in ACTION_STACK[-1].bits:
				break
		popStackFrame()

# jälkimmäinen sarake kertoo, syrjäytyvätkö tämäntyyppiset säännöt, jos toiseksi jälkimmäisessä sarakkeessa vastaava syrjäyttävä sääntö täsmää

LISTENER_PRIORITIES = [
#	 PRE       CASE     POST       PRI SPECIAL GENERAL
	("ennen", "osanto", "",        20, False,  True),
	("",      "omanto", "sijasta", 40, True,   True),
	("",      "omanto", "aikana",  50, False,  True),
	("",      "omanto", "jälkeen", 80, False,  True),
]

ACTION_LISTENERS = []

# Merkkijonon luominen

def createStringObj(x):
	return CLASSES["merkkijono"].newInstance().setExtra("str", x)

# Kokonaisluvun luominen

def createIntegerObj(x):
	return CLASSES["kokonaisluku"].newInstance().setExtra("int", x)

# Tulostaminen

prev_was_newline = True
print_buffer = ""

def say(text):
	global prev_was_newline, print_buffer
	if not text:
		return
	if not prev_was_newline:
		print_buffer += " "
	print_buffer += text
	prev_was_newline = text[-1] == "\n"

# Pelin lopettaminen

game_running = False

def endGame():
	global game_running
	game_running = False

# Pelin komentotulkki

def playGame(grammar):
	global prev_was_newline, game_running, print_buffer
	game_running = True
	ACTIONS_BY_NAME["pelin alkaminen"].run([])
	while game_running:
		print(print_buffer.strip())
		print_buffer = ""
		prev_was_newline = True
		line = input(">> ")
		interpretations = [i() for i in grammar.matchAll(tokenize(line), "PLAYER-CMD", set())]
		if len(interpretations) == 0:
			print("Ei tulkintaa.")
		else:
			sorted(interpretations, key=lambda i: i[1])[-1][0]()
	print(print_buffer.strip())
