=======
 Retki
=======

Retki is a proof-of-concept programming language inspired by Inform 7 and based
on the Finnish language. It aims to be a readable and natural-feeling language,
to some level understandable to people not knowing it, and easy to learn. To
which level these goals were accomplished is debatable, but the result is not
bad. Many of the proven features of Inform 7 were succesfully implemented in
Finnish.

Below is an example of the language taken from the ``lyhyt-peli.txt`` adventure
game. It contains two things. First, a property called ``kirjoitus`` (text) is
added to the ``esine`` (item) class along with a boolean flag
``kirjoitusta sisältävä`` (containing text). Then an action called ``lukeminen``
(reading) is defined. If the player enters a command like ``lue kirje``, the
action will be executed and, if both ``ennen`` checks are passed, the text
in the given item will be showed to the player.

::

	> Lukeminen

	Esine on joko kirjoitusta sisältämätön tai kirjoitusta sisältävä.
	Esine on yleensä kirjoitusta sisältämätön.

	Esineellä on kirjoitukseksi kutsuttu merkkijono.
	Esineen kirjoitus on yleensä "".

	[Esineen] lukeminen on toiminto.
	Tulkitse "lue [esine]" lukemisena.
	Tulkitse "lue [esinettä]" lukemisena.

	Ennen piilossa olevan esineen lukemista:
		Sano "Et näe sellaista asiaa.".
		Keskeytä toiminto.

	Ennen kirjoitusta sisältämättömän esineen lukemista:
		Sano "[Se] ei sisällä mitään kirjoitusta.".
		Keskeytä toiminto.

	Kirjoitusta sisältävän esineen lukemisen aikana:
		Sano "Luet [siihen] kirjoitetun tekstin:[rivinvaihto][rivinvaihto]".
		Sano "[sen kirjoitus][rivinvaihto]".

Please read the `Finnish documentation <dokumentaatio/RETKI.rst>`_ for more
information.
