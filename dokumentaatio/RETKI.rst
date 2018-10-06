=======
 Retki
=======

.. contents:: Sisällys
   :backlinks: none

--------------------
 Summary in English
--------------------

Retki is a programming language inspired by Inform 7.
It tries to be as natural Finnish as possible, although with great limitations.
Below is an example of Retki source code::

	Ennen piilossa olevan esineen ottamista:
		Jos pelaajan esineluettelo ei sisällä sitä:
			Sano "Et näe mitään [sitä].".
			Keskeytä toiminto.

Retki has borrowed many features from Inform 7 including rules.
but is much more limited in its current version.

The rest of the document is written in Finnish as it is assumed that one must
first know Finnish to use this programming language.

----------
 Alkupuhe
----------

Olen viime aikoina ollut erityisen kiinnostunut luonnolliseen kieleen perustuvista ohjelmointikielistä.
Sellaisia on yritetty tehdä vuosien aikana useita, joskin suurin osa yrityksistä on johtanut ellei täydelliseen epäonnistumiseen niin ainakin suureen epäkäytännöllisyyteen.
On siis hyvä esittää kysymys, voiko luonnollisella kielellä ohjelmoida ollenkaan.
Tätä pohtiekseni olen suunnitellut useita erityyppisiä kieliä ja samalla kohdannut ne samat haasteet, joihin edeltäjäni ovat törmänneet.

Eräs varhaisimpia luonnolliseen kieleen pohjautuvia järjestelmiä oli tietokantakyselykieli INTELLECT [Shneiderman92]_.
Se pyrki tulkitsemaan käyttäjän luonnollisella kielellä antaman kysymyksen ja sen jälkeen muunsi sen omaan sisäiseen esitysmuotoonsa
ja lopulta käytetyn tietokannan omalle kyselykielelle, esimerkiksi SQL:ksi.

Esimerkki INTELLECTin toiminnasta: [Harris84]_
	
	**Käyttäjän antama syöte:** GIVE ME THE NAMES OF THE WOMEN IN THE WESTERN REGION WHO ARE OVER QUOTA
	
	**Tulkinta:** PRINT THE LAST NAME AND 82 YTD ACT % OF QUOTA OF ALL SALES PEOPLE WITH SEX = FEMALE & REGION = WEST & 82 YTD ACT % QUOTA OVER 100 00
	
Toinen esimerkki: [Shneiderman92]_
	
	**Käyttäjän antama syöte:** FEMALE EMPLOYEES IN NEW YORK CITY
	
	**Tulkinta:** PRINT THE NAME OF ALL EMPLOYEES WITH SEX = FEMALE & CITY = NEW YORK

INTELLECTin valmistaneen Artificial Intelligence Corporation työntekijä Larry Harris kuvaa järjestelmän kanssa esiintyneitä ongelmia seuraavasti: [Harris84]_

	– –
	
	The first issue is density of coverage. How many ways of making the same request will be accepted by a natural language system? How many slight variations of that request will be rejected? The user may question the system at one point in time and receive an answer. Later, the user may type in what he or she believes is exactly the same request, only to have it rejected by the system. In fact, the user may have merely left out an article or transposed two words - very slight variations which are insignificant to the user but which are sufficient to cause the system to reject the sentence. This problem annoys users, and it may cause them to lose confidence in the system and their ability to use it. They may think that the system is not dependable or that it does not always work in the same way.
	
	– –
	
	The second issue is the transportability of the domain of discourse. It must be possible to transport the system from one application’s domain to another. The examples above showed INTELLECT applied to a sales data base. Other domains to which INTELLECT has been applied include: a human resources data base, a product data base, a financial database, inventory, and a variety of resource allocation applications. Each application requires transporting the system from one domain of discourse to another.
	
	That process must be carried out by people without specific AI training. – –

Tiivistäen, Harris kuvailee kahta ongelmaa.
Ensinnäkin käyttäjän voi olla vaikea ymmärtää sitä, minkälaisia kyselyitä järjestelmä hyväksyy ja minkälaisia ei.
Viattomat muutokset kuten sanajärjestyksen muuttaminen voivat aiheuttaa virheen järjestelmässä.
Käyttäjän on vaikea tai mahdoton ymmärtää mitä hän tekee väärin, varsinkin jos kielen käyttöohjeissa lukee pelkästään "kirjoita miten tuntuu luonnolliselta".
Olen itse törmännyt vastaavaan ongelmaan Wolfram Alpha -järjestelmän kanssa.

Toinen ongelma on kielen alakohtaisuus.
Tietokantakyselykieli on täysin riippuvainen tietokannan sisällöstä, sillä sen on ymmärrettävä sisältöön liittyviä fraaseja.
Koska INTELLECT pyrkii hallitsemaan useita synonyymejä ja vaihtoehtoisia lausuntatapoja, on uutta tietokantaa varten luotavan sanaston koko iso.
Perinteisissä kielissä tällaista ongelmaa ei ole, sillä sama standardoitu kyselykieli toimii kaikkiin tietokantoihin.

Näistä ongelmista voimme tehdä seuraavat johtopäätökset:

1. Ohjelmointikielen tulisi olla niin yksinkertainen, että käyttäjä voi ilman vaikeuksia päätellä, onko annettu lause syntaktillisesti oikein vai ei. Myös hyvä dokumentaatio on tarpeen.
2. On vaikea tehdä yleiskäyttöistä luonnolliseen kieleen pohjautuvaa ohjelmointikieltä, mutta alakohtaisten/erityistarpeeseen luotujen ("domain specific") kielten luominen on mahdollista.

Toiseen kohtaan liittyy myös vahvasti monitulkintaisuus-ongelma.
Koska ihminen on ymmärtää kontekstia, ei ihmisen kielen ole tarpeellista olla yksiselitteinen.
Siksi eri aloilla voi olla samaa tarkoittavia sanoja ja ilmauksia ja kielessä esiintyy muutenkin monitulkintaisuutta.
On useita tapoja ratkaista tämä ongelma.

Järjestelmä voi pyrkiä arvaamaan, mitä käyttäjä kysyy (Wolfram Alphan toimintatapa).
Tämä voidaan toteuttaa tilastollisesti tai etukäteen määritellysti antamalla sanojen eri merkityksille etäisyyksiä ja tämän jälkeen valitsemalla ne tulkinnat, jotka ovat lähellä toisiaan, siis samassa kontekstissa.
Kuitenkin arvaaminen on huono vaihtoehto, sillä se ei välttämättä johda käyttäjän haluamaan lopputulokseen.
Siksi monet järjestelmät kysyvät käyttäjältä tarvittaessa, mitä tämä tahtoo (INTELLECTin toimintatapa).
Näin järjestelmä tekee aina, mitä halutaan.

Kysyminen voi kuitenkin olla epäkäytännöllistä, jos järjestelmän on tarkoitus tulkita yksittäisten kyselyiden sijasta pitkiä komentolistauksia.
Tällaisissa tilanteissa on mahdollista vain hylätä kaikki monitulkintaiset rivit virheellisinä.
Jotta ohjelmointi olisi mahdollista, on tässä tapauksessa kieli suunniteltava sellaiseksi, että on vaikea tehdä monitulkintaisia lauseita.

Minun oma kieleni Tampio [Hauhio18]_ ratkaisee monitulkintaisuusongelman pakottamalla kaikki kielessä sanat ja fraasit käyttämään joukkoa tarkkaan määriteltyjä rakenteita ja muotoja.
Esimerkiksi jokaisen muuttujan on koostuttava adjektiivista ja substantiivista ja
funktiot voivat olla vain ns. genetiivi- ("2:n neliöjuuri") ja essiivi-muotoisia ("2 lisättynä 3:een").
Nämä säännöt ovat kuitenkin turhan rajoittavia: esimerkiksi adjektiiveja ei voi käyttää kielessä enää mihinkään, kun ne on varattu jo muuttujia varten.
Entä miksi "2 pyöristettynä 3 desimaaliin" on sallittu, mutta "annettu sana isolla alkukirjaimella" ei ole? (Vastaus: koska Tampio ei muuten tiedä, onko "iso alkukirjain" muuttuja vai funktio, valitsin että adjektiivi-substantiivi-pari on aina muuttuja.)

Tampio on yleiskäyttöinen kieli ja se tukee mitä tahansa sanoja.
On kuitenkin toinenkin mahdollisuus: tehdä hyvin alakohtainen kieli ja hyväksyä vain joitakin sanoja.
Mutta tämäkin on rajoittavaa: entä jos haluan käyttää joitakin muita sanoja kuin mitä kielen suunnittelija on etukäteen päättänyt?

Ratkaisuksi tähän keksin järjestelmän, jota kutsun *itseään täydentäväksi kieliopiksi*.
Kun jäsennin löytää muuttujan, funktion tai muun rakenteen määrityksen, se lisää tätä muuttujaa vastaavat säännöt kielioppitauluunsa ja muistaa ne sen jälkeen jäsentäessään uusia rivejä.
Tämän ansiosta ei ole vaaraa, että esimerkiksi "iso alkukirjain" voitaisiin tulkita sekä muuttujaksi että funktioksi, sillä järjestelmä tietää tämän jo ennen lausekkeen jäsentämistä.
Menetelmä on toimiva, mutta siinä on joitakin suuria heikkouksia, joihin palaan Retken toteutusta käsittelevässä luvussa.

Uutta kieltäni varten päätin ottaa mallia englanninkielisestä Inform 7 -kielestä, joka on suunniteltu tekstiseikkailujen ohjelmoimista varten [Short06]_.
I7 on mielestäni hyvin onnistunut kieli, paljolti alakohtaisuutensa ansiosta.
Kieltä käytetään pelien tapahtumapaikkojen ja hahmojen kuvailuun, mihin luonnollista kieltä yleensäkin käytetään.

.. [Shneiderman92] Shneiderman, B.: *Designing the User Interface - Strategies for Effective Human-Computer Interaction*, Addison-Wesley, 1992.
.. [Harris84] Harris, L.: Experience with INTELLECT: Artificial Intelligence Technology Transfer, *The AI Magazine*, Summer 1984. https://www.aaai.org/ojs/index.php/aimagazine/article/view/437/373
.. [Hauhio18] Hauhio, I.: Ohjelmoi suomeksi, *Skrolli*, 1/2018. Ks. myös https://github.com/fergusq/tampio
.. [Short06] Short, E.: Some Observations on Using Inform 7, *Brass Lantern*, 2006. http://brasslantern.org/writers/iftheory/i7observations.html

----------
 Johdanto
----------

Retki on ohjelmointikieli, jonka syntaksi pyrkii noudattamaan suomen kirjakielen sääntöjä.
Useat sen rakenteet on lainattu Inform 7 -kielestä, joskaan ei kaikkia.

Retkellä on periaatteessa mahdollista kirjoittaa minkä tahansa laisia ohjelmia, mutta se on esikuvansa tavoin suunniteltu tekstiseikkailuja varten.

Alla on katkelma ``lyhyt-peli.txt``-esimerkistä. Se on tyypillinen huoneen määrittely.

::

	Olohuone on huone eteisestä pohjoiseen.
	"Olohuone tuntuu ahtaalta."

	Sohva on kiinteä esine olohuoneessa.
	"Vanha punainen sohva."

	Pöytä on kiinteä tukeva sisältäjä olohuoneessa.
	"Vanha puinen pöytä."

	Kirje on kirjoitusta sisältävä esine pöydän päällä.
	"Taitellulle paperiarkille on kirjoitettu koukeroista tekstiä."
	Kirjeen kirjoitus on "Hyvä pelaaja! Tervetuloa esimerkkipeliin. Tehtävänäsi on löytää avain, jolla pääset pois tästä talosta.".

.. compound::

	Esimerkistä voi tehdä joitakin huomioita.
	Ensinnäkin jokaisen esineen määrittely on melko tiivis ja ymmärrettävä.
	Määrittelyt noudattavat intuitiivista muotoa
	
	::
	
		(Esine) on (bitit) (tyyppi) (paikka).
	
	mikä ei ole luonnollisista kielistä inspiroituneille ohjelmointikielille tyypillisen verboosia.
	Niinpä kielen käyttäminen ei ainakaan tässä tarkoituksessa ole epäkäytännöllistä.

Toiseksi pöydästä käytetään kyseenalaista termiä "tukeva sisältäjä".
Tämä on anglismi käsitteestä "supporting container" ja se viittaa esineeseen, joka sisältää muita esineitä ja erityisesti siten, että esineet ovat sen päällä.
On olemassa myös "ympäröiviä sisältäjiä", jotka sisältävät esineitä sisällään.
En ole keksinyt näille tähän mennessä parempia termejä, ja olen halukas muuttamaan niitä tarvittaessa.
Ohjelmointikielen luonnollisuutta tulee kuitenkin aina rajoittamaan se, että suurelle osalle tarvittavista käsitteistä ei edes ole sanoja.

Tässä dokumentissa käsittelen sekä Retki-kielen kielioppia, sen toteutusta sekä näiden heikkouksia.
Mukana on myös kappale kääntäjän asentamista ja peruskäyttöä varten.

-----------------------
 Asentaminen ja käyttö
-----------------------

Riippuvuudet
============

Voikko
------

Retki tarvitsee libvoikko-kirjaston suomenkielen morfologiaa varten.
Se löytyy useimmista Linux-jakeluista nimellä ``libvoikko``.

Jotta Voikko toimisi oikein, on asennettava myös suomen kielen morfologinen sanakirja.

* Voikon versiota 3.8 varten lataa `tämä <sanakirja1_>`_ versio sanakirjasta.

* Voikon versiota 4 varten lataa `tämä <sanakirja2_>`_ versio sanakirjasta.

.. _sanakirja1: http://www.puimula.org/htp/testing/voikko-snapshot/dict-morpho.zip
.. _sanakirja2: https://www.puimula.org/htp/testing/voikko-snapshot-v5/dict-morpho.zip

Pura zip-paketti ``~/.voikko/``-kansioon.

Python 3
--------

Retki tarvitse Python 3.5:n.

Paketit
-------

Asentaminen on helpointa pip-ohjelman avulla, mutta jos sitä ei ole,
on asennettava Python-kirjastot voikko_ ja suomilog_.

.. _voikko: https://github.com/fergusq/voikko
.. _suomilog: https://github.com/fergusq/suomilog

Asentaminen
===========

Retki-kääntäjä on saatavilla PyPi:ssä::

	pip3 install retki

Käyttäminen
===========

Retkeä voi käyttää joko interaktiivisessa tilassa tai kääntäjätilassa.

Esimerkkipelin kääntäminen ja ajaminen::

	retki examples/lyhyt-peli.txt -o peli.py
	python3 peli.py

Esimerkkiohjelman kirjoittamisesta on kerrottu lisää osiossa `Tekstiseikkailupelin kirjoittaminen`_.

Interaktiivinen tila
--------------------

Interaktiivisessa tilassa on mahdollista testata ohjelmaa tutkimalla muuttujien arvoja,
määrittelemällä uusia olioita suorituksen aikana ja pelaamalla samalla työn alla olevaa peliä.

-------------
 Retki-kieli
-------------

Lähdekooditiedosto
==================

Retki-kielinen lähdekooditiedosto on joukko määrityksiä ("definition").
Retki tukee tällä hetkellä 15 eri määritystyyppiä [#määritykset]_.

.. [#määritykset] Määrityksiä ovat luokkamääritys, bittikenttämääritys, bittikentän oletusarvomääritys, oliokenttämääritys, joukkokenttämääritys, kuvauskenttämääritys, kentän oletusarvomääritys, kentän arvon määritys, muuttujamääritys, ehtomääritys, toimintomääritys, kuuntelijamääritys, komentomääritys, pelaajakomentomääritys ja todennäköisyysmääritys.

Luokkamääritykset
=================

Luokkia kutsutaan retkessä *käsitteiksi*.
Kaikilla käyttäjän luomilla luokilla on yhteinen yläluokka "asia".

Jos luokka on suoraan asian alaluokka, on mahdollista sanoa vain::

	Olento on käsite.

Muusta kuin asiasta periyttäminen onnistuu alakäsite-avainsanan avulla::

	Ihminen on olennon alakäsite.

Nyt siis luokkahierarkia näyttäisi tältä::

	asia
	 olento
	  ihminen

Bittikenttämääritys
===================

Bitit ovat adjektiiveja, jotka voivat liittyä luokkaan ja sen instansseihin.
Niitä voi ajatella boolean-tyyppisinä kenttinä::

	Ihminen voi olla väsynyt.
	Asia voi olla kaunis.

Bitille on mahdollista määritellä myös vastakohta, jolloin on määriteltävä, onko bitin oletusarvoinen tila ("bittikentän oletusarvomääritys")::

	Ihminen on joko kiltti tai ilkeä.
	Ihminen on yleensä kiltti.

On myös mahdollista luoda kolme toistensa poissulkevaa bittiä::

	Leipä on joko hyvänmakuinen, pahanmakuinen tai neutraali.
	Leipä on yleensä neutraali.

Oliokenttämääritys
==================

Oliokenttä sisältää viittauksen johonkin olioon (ei siis bittiä, joukkoa tai kuvausta).

Oliokenttä voidaan määritellä kummalla tahansa seuraavista tavoista::

	Ihmisellä on nimi, joka on merkkijono.
	Ihmisellä on kotipaikaksi kutsuttu paikka.

Oliokentän oletusarvo määritellään seuraavasti::

	Ihmisen kotipaikka on yleensä Helsinki.

Olion kentän arvoa voi muuttaa kentän arvon määrityksellä::

	Jaakon nimi on "Jaakko Virtanen".

Joukkokenttämääritys
====================

Joukkokenttä voi sisältää nolla tai useamman viittauksen tietyntyyppisiin olioihin::

	Ihmisellä on esineluetteloksi kutsuttu joukko esineitä.

Kuvauskenttämääritys
====================

Kuvauskenttä on hajautustaulu, joka sisältää (avain,arvo) -pareja::

	Kutakin suuntaa kohden huoneella voi olla siinä suunnassa olevaksi naapurihuoneeksi kutsuttu huone.

Kuvauskentällä voi olla oletusarvo::

	Ihmisen suunnassa oleva naapurihuone on yleensä eteinen.

Muuttujamääritys
================

Muuttujan luominen on Retki-kielessä ainoa tapa luoda uusi olio (lukuunottamatta merkkijonoja).

Muuttuja luodaan seuraavasti::

	Jaakko on ihminen.
	Maija on väsynyt ihminen.

Luokan nimen lisäksi muuttujamäärittelyn yhteydessä on mahdollista käyttää bittejä ja ehtoja kuten hahmoissa (ks. alempana).

Ehtomääritys
============

Ehto on funktio, joka käyttäytyy kuin bitti.
Ehto määritellään joukkona ehtolauseita, joiden on kaikkien oltava totta.

::

	Määritelmä. Kun esine (E) on "näkyvillä":
		jokin seuraavista:
			E on pelaajan sijainnissa
			pelaajan esineluettelo sisältää E:n

	Määritelmä. Kun esine (E) on "piilossa":
		E ei ole pelaajan sijainnissa
		pelaajan esineluettelo ei sisällä E:tä

Ehtoa voi käyttää kahdella tavalla.
Ensinnäkin kuuntelija tai silmukka voidaan rajata hahmolla koskemaan vain olioita, joille tietty ehto on tosi.
Toiseksi ehto voidaan pakottaa todeksi, jolloin annettua oliota muokataan siten, että ehto on tosi.
Esimerkiksi jos muuttujamäärityksessä luodaan "näkyvillä oleva esine",
koodi lisää olion pelaajan sijaintiin (mutta ei esineluetteloon, sillä riittää, että vain yksi ehdoista on totta).

::

	Puhelin on näkyvillä oleva esine.

Vastaavasti, jos suoritetaan komento "puhelin on nyt piilossa", se poistetaan sekä pelaajan sijainnista että esineluettelosta::

	Puhelin on nyt piilossa.

(Jälkimmäinen on siis komento, ei määritys, ks. alla.)

Ehtolauseet
-----------

============================================= ===============================
Ehtolause                                     Tulkinta todeksi pakottamisessa
============================================= ===============================
(joukkokenttä) sisältää (arvon)               Arvo lisätään joukkoon.
(joukkokenttä) sisältää yhdenkin (hahmon)     Uusi hahmoa vastaava arvo lisätään joukkoon.
(joukkokenttä) ei sisällä (arvoa)             Arvo poistetaan joukosta.
(joukkokenttä) ei sisällä yhtäkään (hahmoa)   Kaikki hahmoa vastaavat arvot poistetaan joukosta.
(arvo) on (bitti)                             Bitti laitetaan päälle ja sen vastabitit laitetaan pois päältä.
(arvo) on (ehto)                              Ehto pakotetaan todeksi.
kaikki seuraavista:                           Kaikki sisennetyt ehdot pakotetaan todeksi.
jokin seuraavista:                            Ensimmäinen sisennetty ehto pakotetaan todeksi.
jokaiselle (hahmolle) (joukkokentässä) pätee: Kaikki sisennetyt lauseet pakotetaan todeksi kaikille hahmoon täsmääville arvoille joukkokentässä.
jollekin (hahmolle) (joukkokentässä) pätee:   Ensimmäinen hahmoon täsmäävä arvo pakotetaan noudattamaan sisennettyjä ehtoja. Jos yksikään arvo ei täsmää hahmoon, syntyy virhe.
============================================= ===============================

Kokonaisluvuille on määritelty lisäksi seuraavat ehtolauseet, joita **ei** voi pakottaa todeksi.
Lauseille on sekä symboliset että sanalliset versiot.

================================ ====================
Symbolinen ehtolause             Sanallinen ehtolause
================================ ====================
(kokonaisluku) = (kokonaisluku)  (kokonaisluku) on yhtä suuri kuin (kokonaisluku)
(kokonaisluku) /= (kokonaisluku) (kokonaisluku) ei ole (kokonaisluku)
(kokonaisluku) < (kokonaisluku)  (kokonaisluku) on pienempi kuin (kokonaisluku)
(kokonaisluku) > (kokonaisluku)  (kokonaisluku) on suurempi kuin (kokonaisluku)
(kokonaisluku) <= (kokonaisluku) (kokonaisluku) on pienempi tai yhtä suuri kuin (kokonaisluku), (kokonaisluku) on enintään (kokonaisluku)
(kokonaisluku) >= (kokonaisluku) (kokonaisluku) on suurempi tai yhtä suuri kuin (kokonaisluku), (kokonaisluku) on vähintään (kokonaisluku)
================================ ====================

Toimintomääritys
================

Toiminnot ovat aliohjelmien vastine Retkessä, ja ne vastaavat Inform 7:n actioneita ja activityjä.

Toiminnolla voi olla nolla, yksi tai kaksi parametria.
Määrityksessä parametrien tyypit on laitettava hakasulkuihin (tämä on ainoa suuri virhe Retken oikeinkirjoituksessa verrattuna suomen oikeinkirjoitukseen).

::

	Hyppiminen on toiminto.
	[Esineen] ottaminen on toiminto.
	[Merkkijonon] tulostaminen on toiminto.
	[Asian] [pöydän] päälle asettaminen on toiminto.

Komentomääritys
===============

Komentomääritys luo komennon, jolla toiminnon voi laukaista kuuntelijan sisällä.

::

	Tulostamisen komento on "tulosta [merkkijono]".

Pelaajakomentomääritys
======================

Pelaajakomentomääritys luo komennon, jolla pelaaja voi laukaista toiminnon pelissä.

::

	Tulkitse "hypi" hyppimisenä.
	Tulkitse "ota [esine]" esineen ottamisena.
	Tulkitse "aseta [asia] [pöydän] päälle" päälle asettamisena.

Sekä komentomäärityksessä että pelaajakomentomäärityksessä tyyppien ja mahdollisten postpositioiden nimet voi tai voi olla merkitsemättä koodiin,
mutta ne on pakko merkitä, jos kääntäjä ei pysty muuten päättelemään, mikä toiminto on kyseessä (esimerkiksi jos sekä "esineen ottaminen" että "ruoan ottaminen" ovat toimintoja).

Todennäköisyysmääritys
======================

Todennäköisyysmäärityksellä voi määritellä todennäköisyyden sille, tarkoittaako pelaaja tiettyä esinettä (tai luokkaa) käyttäessään jotakin sanaa komennossaan.

Tarkoitusmäärittelyn muoto on::

	Tarkoittaako pelaaja (luokkaa/muuttujaa):
		(todennäköisyys)
	
Todennäköisyys voi olla yksi seuraavista:

====================== =====
Lauseke                Arvo
====================== =====
varmasti               1000
hyvin todennäköisesti  100
todennäköisesti        10
ehkä                   0
tuskin                 -10
epätodennäköistä       -10
hyvin epätodennäköistä -100
varmasti ei            -1000
jos (ehto): muuten:    Ehdon mukaan joko seuraava sisennetty todennäköisyys tai muuten-lohkon jälkeen tuleva sisennetty todennäköisyys
====================== =====

Jos pelaajan syöttämä lause on monitulkintainen,
jokaisen vaihtoehdon todennäköisyysarvot lasketaan (jos yhdellä vaihtoehdolla on monta todennäköisyyssääntöä, ne lasketaan yhteen)
ja todennäköisin vaihtoehto valitaan.

::

	Tarkoittaako pelaaja esinettä:
		Jos se on näkyvillä:
			ehkä
		Muuten:
			hyvin epätodennäköistä

	Muistikirja on esine.
	Tarkoittaako pelaaja muistikirjaa:
		varmasti

Ylläoleva sääntö sanoo, että näkyvillä olevat esineet ovat todennäköisempiä kuin piilossa olevat, paitsi muistikirja, johon pelaaja viittaa aina, jos lause on monitulkintainen.
Esimerkiksi ``ota esine`` viittaa aina muistikirjaan, kuten myös ``ota muistikirja``, mutta ``ota muki`` viittaa johonkin näkyvillä olevaan mukiin.

Kuuntelijamääritys
==================

Kuuntelijat vastaavat Inform 7:n sääntöjä.
Jos kuuntelijan toiminto laukaistaan ja kuuntelijan hahmot täsmäävät, kuuntelijan sisällä olevat komennot suoritetaan.

Kuuntelijoita on neljää tyyppiä: ennen, sijasta, aikana ja jälkeen -kuuntelijat.
Nämä suoritetaan seuraavasti:

1. Ensin kaikki sopivat ennen-kuuntelijat suoritetaan.
2. Kaikki sopivat juuri ennen -kuuntelijat suoritetaan.
3. Jos yksikin sijasta-kuuntelija sopii, se suoritetaan ja toiminnon suoritus keskeytetään.
4. Kaikki sopivat aikana-kuuntelijat suoritetaan.
5. Kaikki sopivat heti jälkeen -kuuntelijat suoritetaan.
6. Kaikki sopivat jälkeen-kuuntelijat suoritetaan.

Ideaalisesti ennen-kuuntelijat sisältävät ehtoja ja keskeyttävät toiminnon tarvittaessa.
Sijasta-kuuntelijat sisältävät ennen-lauseita tilannekohtaisempia sääntöjä.
Aikana-kuuntelija suorittaa toiminnon varsinaisen suorittamisen.
Jälkeen-kuuntelijat ilmoittavat pelaajalle toiminnon lopputuloksesta.

::

	[Esineen] ottaminen on toiminto.
	Tulkitse "ota [esine]" ottamisena.

	Ennen piilossa olevan esineen ottamista:
		Sano "Et näe mitään [sitä].".
		Keskeytä toiminto.

	Ennen kiinteän esineen ottamista:
		Sano "Et pystyisi liikuttamaan sitä.".
		Keskeytä toiminto.

	Tylsän esineen ottamisen sijasta:
		Sano "Sinun ei tee mieli koskea mihinkään.".

	Esineen ottamisen aikana:
		Se on nyt piilossa.
		Lisää se pelaajan esineluetteloon.

	Esineen ottamisen jälkeen:
		Sano "Sinulla on nyt [se].".

Kuuntelijan sisällä voi käyttää toimintojen yhteydessä määriteltyjä komentoja, sekä seuraavia:

Komennot
--------

.. list-table:: Komennot
	:header-rows: 1

	* - Komento
	  - Selitys
	* - (Arvo) on nyt (bitti).
	  - Laittaa bitin päälle.
	* - (Arvo) on nyt (ehto).
	  - Pakottaa ehdon todeksi.
	* - (Arvo) ei ole enää (bitti).
	  - Poistaa bitin (tämän voi tehdä vain jos bitille ei ole määritelty vastabittejä).
	* - (Muuttuja) on nyt (arvo).
	  - Muuttaa muuttujan arvoa.
	* - (Arvo) (muuttujana):
	  - Muuttaa muuttujan arvoa, suorittaa sisennetyt komennot ja palauttaa muuttujan arvon takaisin alkuperäiseksi.
	* - Lisää (arvo) (joukkokenttään).
	  - Lisää arvon joukkoon.
	* - Poista (arvo) (joukkokentästä).
	  - Poistaa arvon joukosta.
	* - Toista jokaiselle (hahmolle) (joukkokentässä):
	  - Toistaa sisennetyt komennot jokaiselle hahmoon täsmäävälle arvolle joukossa.
	* - Toista jokaiselle ryhmälle samanlaisia (hahmoja) (joukkokentässä):
	  - Toistaa sisennetyt komennot jokaiselle uniikille hahmoon täsmäävälle arvolle joukossa (arvoon viitataan pronominilla "ne", "ryhmän koko" on samanlaisten arvojen määrä).
	* - Toista (kokonaisluku) kertaa:
	  - Toistaa sisennetyt komennon halutun määrän kertoja.
	* - Toista jokaiselle kokonaisluvulle (nimi) välillä (kokonaisluvusta) (kokonaislukuun):
	  - Toistaa sisennetyt komennot jokaiselle kokonaisluvulle annetulla välillä.
	* - Jos (ehtolause):
	  - Suorittaa sisennetyt komennot, jos ehtolause on tosi.
	* - Sano (merkkijono).
	  - Tulostaa merkkijonon pelaajalle.
	* - Keskeytä toiminto.
	  - Keskeyttää nykyisen toiminnon suorittamisen.
	* - Lopeta peli.
	  - Keskeyttää ohjelman suorituksen.

Hahmot
======

Hahmo on tapa tunnistaa ja luoda tietyntyyppisiä olioita.
Se koostuu luokan nimestä, biteistä ja ehdoista.

::

	valaistu käytävä
	pöydän päällä oleva esine
	kiinteä olohuoneessa oleva esine

Hahmoa voi käyttää muuttujan luomiseen sekä kuuntelijan ja silmukan rajaamiseen koskemaan vain tiettyjä arvoja.

Muuttujamäärittelyssä on myös mahdollista käyttää seuraavaa erikoissyntaksia ehtojen määrittämiseksi::

	Muki on esine pöydän päällä.
	Tuoli on kiinteä esine olohuoneessa.

Sisäänrakennetut luokat
=======================

Retkeen on sisäänrakennettu käsitteet ``yläkäsite``, ``asia``, ``merkkijono`` ja ``kokonaisluku``.
Näistä "yläkäsitettä" ei ole tarkoitus käyttää ja "merkkijono" sekä "kokonaisluku" ovat primitiivisiä.
Kaikkien käyttäjän luomien luokkien tulisi periä "asia".

::

	yläkäsite
	 merkkijono
	 kokonaisluku
	 asia

Pelin alkaminen
===============

``Pelin alkaminen`` on sisäänrakennettu toiminto, joka suoritetaan aina ohjelman käynnistyessä.
Se vastaa siis monien kielten ``main``-funktiota.
Pelin alkamiselle voi lisätä kuuntelijoita samalla tavalla kuin muillekin toiminnoille::

	Pelin alkamisen jälkeen:
		Sano "Tervetuloa peliin!".

----------
 Toteutus
----------

Jäsennin
========

Retki on toteutettu Suomilog-kirjaston (ja sen käyttämän Voikko-kirjaston) avulla.
Suomilog parsii kontekstivapaita kielioppeja, joihin on lisätty lisätietoa taivutusmuodoista.

Retki-kääntäjä koostuu kielioppisäännöistä ja funktioista, jotka suoritetaan kun sääntö pätee.
Eräs säännöistä on luokan määrittelyyn käytetty sääntö:

.. code:: python
   :number-lines:

	pgl(".CLASS-DEF ::= .* on .CLASS{omanto} alakäsite . -> class $1 : $2", FuncOutput(defineClass))

``pgl`` (parseGrammarLine) lisää uuden säännön kielioppiin.
Tässä tapauksessa se lisää ``.CLASS-DEF``-nimisen säännön.
``.*`` täsmää mihin tahansa ei-tyhjään merkkijonoon ja ``.CLASS{omanto}`` genetiivimuotoiseen luokan nimeen.
Nuolen ``->`` jälkeen säännössä on merkkijonoesitys, joka luodaan jäsennetystä tekstistä debug-tarkoituksia varten.
Viimeiseksi määritellään, että jäsentämisen jälkeen kutsutaan ``defineClass``-funktiota.

``defineClass`` luo rekisteröi luokan ja lisää siihen liittyvät kielioppisäännöt kielioppiin.

.. code:: python
   :number-lines:

	def defineClass(name, superclass):
		name_str = tokensToString(name)
		name_code = nameToCode(name)
		
		if name_str in CLASSES:
			raise Exception("redefinition of class " + name_str)
		
		rclass = RClass(name_str, superclass, name)
	
		for clazz in reversed(superclass.superclasses()) if superclass else []:
			for fname in clazz.fields:
				rclass.fields[fname] = clazz.fields[fname].copy()
		
		...

``tokensToString`` muodostaa luokan nimestä merkkijonoesityksen.
``nameToCode`` etsii nimestä ne sanat, jotka taipuvat (nominatiivissa olevat substantiivit ja adjektiivit)
ja luo kielioppikoodin, joka täsmää nimeen.

Luokkaolion luomisen jälkeen luokalle lisätään kaikki sen yläluokkien kentät.
Tämän jälkeen ``defineClass`` määrittelee useita kielioppisääntöjä, esimerkiksi alla olevan.

.. code:: python
   :number-lines: 27

	pgl(".CLASS ::= %s -> %s" % (name_code, name_str), FuncOutput(lambda: rclass))

``.CLASS`` määritellään täsmäämään luokan nimeen, ja tämän ehdon täsmätessä kutsutaan lambdaa, joka palauttaa luokaa vastaavan olion.
Kun esimerkiksi ``.CLASS-DEF``:n sisältämä ``.CLASS`` täsmää tähän luokkaan, lambdan palauttama olio annetaan argumenttina ``defineClass``-funktiolle (``superclass``-parametriin).

Edut
----

Itseään täydentävä kielioppi mahdollistaa mielivaltaisten luonnollisen kielen tukemien rakenteiden jäsentämisen.
Jäsentimen ei itsessään tarvitse tietää mitään siitä, minkälaisia mahdollisia rakenteita suomen kielessä on, sillä käyttäjä voi määritellä uusia kielioppisääntöjä.

Koska jokaisella tietotyypillä on oma lausekesääntönsä kielioppissa, on mahdollista siirtää kaikki tyyppitarkistus jäsentämisen osaksi.
Tästä on hyötyä, sillä se mahdollistaa helpommin samannimisten, mutta erityyppisten muuttujien luomisen.
Esimerkiksi muuttujaa ``se`` voi käyttää viittaamaan mihin tahansa parametriin, ja kielioppisääntöjen avulla sille valitaan oikea tulkinta,
tai luodaan virhe jos tilanne on monitulkintainen.

Heikkoudet
----------

Kieliopin täydentäminen onnistuu ratkaisemaan moniselitteisyysongelmia, mutta siinä on joitakin heikkouksia.
Ensinnäkin kieliopista voi tulla pitkien ohjelmien kohdalla hyvin suuri, sillä jokainen muuttuja, luokka ja funktio on lisättävä kielioppiin.
Esimerkiksi ``lyhyt-peli.txt``-esimerkin kielioppissa on tiedoston lopussa 1216 sääntöä.
Sääntöjen määrän kasvaessa jäsentäminen muuttuu hitaammaksi ja useita tuhansia rivejä pitkän ohjelman kääntämiseen voi tästä syystä kulua useita minuutteja.

Virheviestit saattavat myös olla sekavampia, sillä tyyppivirheiden sijasta käyttäjälle annetaan kielioppivirheitä.

Koska muuttujia ja funktioita ei ole olemassa ennen niiden määrittelyä, niihin ei myöskään voi viitata ennen sitä.
Tämän johdosta kaksi määrittelyä eivät voi olla toistensa riippuvuuksia.

-------------------------------------
 Tekstiseikkailupelin kirjoittaminen
-------------------------------------

Tässä osiossa käyn läpi ``lyhyt-peli.txt``-esimerkin sisältöä.

``lyhyt-peli.txt`` on kokonainen pieni tekstiseikkailu, jossa pelaajan löydettävä tie ulos talosta, jonka kaikki ulos vievät ovet ovat lukossa.
Esimerkki koostuu kahdesta osasta: tekstiseikkailukirjastosta ja varsinaisesta pelistä.

Tekstiseikkailukirjasto
=======================

Kirjasto määrittelee seuraavat asian alakäsitteet::

	asia
	  esine
	    ovi
	    sisältäjä
	    sytytin
	  huone
	  ihminen
	  suunta

Ja seuraavat toiminnot::

	        esineen avaaminen
	                esineluettelon tulostaminen
	        huoneen esitteleminen
	    merkkijonon fokalisoijalle sanominen
	ihmistä vastaan hyökkääminen
	                katseleminen
	       suuntaan katsominen
	        esineen katsominen
	   esineen alle katsominen
	 esineen taakse katsominen
	        ihmisen katsominen
	ihmiselle asian kertominen
	          asian kuvaileminen
	       suuntaan liikkuminen
	     huoneeseen liikkuminen
	        esineen lukeminen
	         ovesta meneminen
	        esineen ottaminen
	      ihmiselle puhuminen
	     huoneeseen siirtyminen
	        esineen sytyttäminen
	        esineen syöminen

Näistä ``merkkijonon fokalisoijalle sanominen``, ``huoneen esitteleminen``, ``asian kuvaileminen`` ja ``huoneeseen siirtyminen``
ovat pelin sisäisesti käyttämä toimintoja ja kaikki muut ovat komentoja, joita pelaaja voi syöttää.
Monet komennoista ovat vaihtoehtoisia tapoja ilmaista sama asia.
Esimerkiksi komennoissa ``huoneeseen liikkuminen``, ``suuntaan liikkuminen`` ja ``ovesta  meneminen`` määränpäähän viitataan eri tavoin,
mutta lopputulos on sama.

Komennoista
-----------

Osa komennoista ei tee mitään oletuksena.
Esimerkiksi puhuminen on määritelty seuraavasti::

	Ihmiselle puhumisen aikana:
		Sano "[Hän] ei näytä kiinnostuneelta höpinästäsi.".

Vastavaasti lukeminen on määritelty vain, jos esineelle on määritelty kirjoitus ja sytyttäminen vain, jos sytytettävä esine on syttyvä::

	Ennen kirjoitusta sisältämättömän esineen lukemista:
		Sano "[Se] ei sisällä mitään kirjoitusta.".
		Keskeytä toiminto.

	Kirjoitusta sisältävän esineen lukemisen aikana:
		Sano "Luet [siihen] kirjoitetun tekstin:[rivinvaihto][rivinvaihto]".
		Sano "[sen kirjoitus][rivinvaihto]".
	
	Ennen syttymättömän esineen sytyttämistä:
		Sano fokalisoijalle "[Sitä] ei voi sytyttää.".
		Keskeytä toiminto.

Jos peli sisältää sytytettäviä tai luettavia asiota, nämä oletukset voi korvata pelin vaatimilla tavoilla::

	Salainen viesti on kirjoitusta sisältävä syttyvä esine pöydällä.
	
	Salaisen viestin lukemisen sijasta:
		Sano "Saat vaivoin selvää koodikielisestä viestistä.".
		Sano "Kirjeen mukaan sinua kaivataan peitetehtävässä Turussa.".
		Sano "Yhteyshenkilösi on Matti Virtanen, tapaat hänet Kauppatorilla klo 13.".
		Sano "Polta tämä viesti lukemisen jälkeen.".
	
	Salaisen viestin sytyttämisen jälkeen:
		Sano fokalisoijalle "[Se] palaa tuhkaksi.".
		Se on nyt piilossa.

Huoneiden luominen
------------------

Kun huone luodaan, on tarkoitus pakottaa todeksi seuraava ehto::

	Määritelmä. Kun huone (A) on "[huoneesta (B)] [suuntaan (tarkasteltava suunta)]":
		B:n naapurihuone tarkasteltavassa suunnassa on A
		A:n naapurihuone tarkasteltavan suunnan vastasuunnassa on B
		B:n A:han johtava suunta on tarkasteltava suunta
		A:n B:hen johtava suunta on tarkasteltavan suunnan vastasuunta
		A:n naapurihuonejoukko sisältää B:n
		B:n naapurihuonejoukko sisältää A:n

Ehto lisää naapurihuoneet toistensa tietorakenteisiin.
Sen käyttäminen on helppoa::

	Aula on huone.
	Käytävä on huone aulasta pohjoiseen.

Fokalisointi
------------

Fokalisoija-muuttuja sisältää sen ihmisen, jonka näkökulmasta komennot suoritetaan.
Alussa fokalisoija on aina pelaaja, mutta fokalisoijaa voi tarvittaessa muuttaa.
Esimerkiksi NPC-hahmon siirtäminen toiseen huoneeseen on mahdollista seuraavasti::

	Poika on ihminen eteisessä.
	
	Pojalle puhumisen aikana:
		Sano "Poika pelästyy sinua ja juoksee pois.".
		Poika fokalisoijana:
			Siirry nyt olohuoneeseen.

Komento ``Sano fokalisoijalle`` tulostaa annetun viestin vain, jos fokalisoja on pelaaja.
Sitä suositellaan käytettäväksi, jos nykyisen toiminnon voi suorittaa sekä pelaaja että NPC-hahmo.
Jos toiminnon on tarkoitus voida suorittaa vain pelaaja (kuten esimerkiksi ``puhuminen``-toiminnon),
voi sen koodissa käyttää tavallista ``Sano``-komentoa tämän intention selventämiseksi.

Esimerkkipeli
=============

Esimerkkipelissä on tarkoitus löytää avain, jonka avulla pääsee pois talosta.
Avaimen saamiseksi pelaajan on osattava hyödyntää eri esineitä.

Pelin kartta on seuraavanlainen::

	 Takapiha
	     |
	Ruokahuone - Olohuone - Varasto
	     |          |
	  Keittiö    Eteinen
	                |
	              Piha

Kartan luominen on helppoa käyttäen hyväksi ylempänä määriteltyä ehtoa::

	Piha on huone.
	Eteinen on huone pihasta pohjoiseen.
	Olohuone on huone eteisestä pohjoiseen.
	Varasto on pimeä huone olohuoneesta itään.
	Ruokahuone on huone olohuoneesta länteen.
	Takapiha on huone ruokahuoneesta pohjoiseen.
	Keittiö on huone ruokahuoneesta etelään.


Ulkona olevien huoneiden ja talon huoneiden välissä on lukitut ovet.
Näidenkin luominen on helppoa ``välissä``-ehdon avulla::

	Ulko-ovi on ovi eteisen ja pihan välissä.
	Takaovi on ovi takapihan ja ruokahuoneen välissä.
