=======
 Retki
=======

.. contents:: Sisällys

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
It has also some unique features like the condition-constructor duality,
but in general it is very limited when compared to other similar languages.

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
Ensinnäkin käyttäjän voi olla vaikea ymmärtää sitä, minkälaisia kysylyitä järjestelmä hyväksyy ja minkälaisia ei.
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
Siksi eri aloilla voi olla samaa tarkoittavia sanoja ja ilmauksia.
On useita tapoja ratkaista tämä ongelma.

Järjestelmä voi pyrkiä arvaamaan, mitä käyttäjä kysyy (Wolfram Alphan toimintatapa).
Tämä voidaan toteuttaa tilastollisesti tai etukäteen määritellysti antamalla sanojen eri merkityksille etäisyyksiä ja tämän jälkeen valitsemalla ne tulkinnat, jotka ovat lähellä toisiaan, siis samassa kontekstissa.
Kuitenkin arvaaminen on huono vaihtoehto, sillä se ei välttämättä johda käyttäjän haluamaan lopputulokseen.
Siksi monet järjestelmät kysyvät käyttäjältä, mitä tämä tahtoo (INTELLECTin toimintatapa).
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
Kun jäsennin löytää muuttujan, funktion tai muun rakenteen määrityksen, se lisää tätä muuttujaa vastaavat säännöt kielioppitauluunsa ja muistaa sen jälkeen jäsentäessään uusia rivejä.
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
Retki tukee tällä hetkellä 14 eri määritystyyppiä [#määritykset]_.

.. [#määritykset] Määrityksiä ovat luokkamääritys, bittikenttämääritys, bittikentän oletusarvomääritys, oliokenttämääritys, joukkokenttämääritys, kuvauskenttämääritys, kentän oletusarvomääritys, kentän arvon määritys, muuttujamääritys, ehtomääritys, toimintomääritys, kuuntelijamääritys, komentomääritys ja pelaajakomentomääritys.

Luokkamääritykset
=================

Luokkia kutsutaan retkessä *käsitteiksi*.
Kaikilla luokilla on yhteinen yläluokka "asia".

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
(joukkokenttä) ei sisällä (arvoa)             Arvo poistetaan joukosta.
(arvo) on (bitti)                             Bitti laitetaan päälle ja sen vastabitit laitetaan pois päältä.
(arvo) on (ehto)                              Ehto pakotetaan todeksi.
kaikki seuraavista:                           Kaikki sisennetyt ehdot pakotetaan todeksi.
jokin seuraavista:                            Ensimmäinen sisennetty ehto pakotetaan todeksi.
jokaiselle (hahmolle) (joukkokentässä) pätee: Kaikki sisennetyt lauseet pakotetaan todeksi kaikille hahmoon täsmääville arvoille joukkokentässä.
jollekin (hahmolle) (joukkokentässä) pätee:   Ensimmäinen hahmoon täsmäävä arvo pakotetaan noudattamaan sisennettyjä ehtoja. Jos yksikään arvo ei täsmää hahmoon, syntyy virhe.
============================================= ===============================

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

Kuuntelijamääritys
==================

Kuuntelijat vastaavat Inform 7:n sääntöjä.
Jos kuuntelijan toiminto laukaistaan ja kuuntelijan hahmot täsmäävät, kuuntelijan sisällä olevat komennot suoritetaan.

Kuuntelijoita on neljää tyyppiä: ennen, sijasta, aikana ja jälkeen -kuuntelijat.
Nämä suoritetaan seuraavasti:

1. Ensin kaikki sopivat ennen-kuuntelijat suoritetaan.
2. Jos yksikin sijasta-kuuntelija sopii, se suoritetaan ja toiminnon suoritus keskeytetään.
3. Kaikki aikana-kuuntelijat suoritetaan.
4. Kaikki jälkeen-kuuntelijat suoritetaan.

Ideaalisesti ennen-kuuntelijat sisältävät ehtoja ja keskeyttävät toiminnon tarvittaessa.
Sijasta-kuuntelijat sisältävät ennen-lauseita tilannekohtaisempia sääntöjä.
Aikana-kuuntelija suorittaa toiminnon varsinaisen suorittamisen.
Jälkeen-kuuntelijat ilmoittavat pelaajalle toiminnon lopputuloksesta.

::

	[Esineen] ottaminen on toiminto.
	Tulkitse "ota [esine]" ottamisena.

	Ennen piilossa olevan esineen ottamista:
		Jos pelaajan esineluettelo ei sisällä sitä:
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

============================================== ====================
Komento                                        Selitys
============================================== ====================
(Arvo) on nyt (bitti).                         Laittaa bitin päälle.
(Arvo) on nyt (ehto).                          Pakottaa ehdon todeksi.
(Arvo) ei ole enää (bitti).                    Poistaa bitin (tämän voi tehdä vain jos bitille ei ole määritelty vastabittejä).
(Muuttuja) on nyt (arvo).                      Muuttaa muuttujan arvoa.
Lisää (arvo) (joukkokenttään).                 Lisää arvon joukkoon.
Poista (arvo) (joukkokentästä).                Poistaa arvon joukosta.
Toista jokaiselle (hahmolle) (joukkokentässä): Toistaa sisennetyt komennot jokaiselle hahmoon täsmäävälle arvolle joukossa.
Jos (ehtolause):                               Suorittaa sisennetyt komennot, jos ehtolause on tosi.
Sano (merkkijono).                             Tulostaa merkkijonon pelaajalle.
Keskeytä toiminto.                             Keskeyttää nykyisen toiminnon suorittamisen.
Lopeta peli.                                   Keskeyttää ohjelman suorituksen.
============================================== ====================
