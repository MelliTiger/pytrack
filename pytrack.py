#!/usr/bin/python
#


import pymysql.cursors
from uuid_extensions import uuid7, uuid7str
from pytermgui import report_cursor, move_cursor, set_mode, clear, print_to, bold, cursor_home, terminal, italic, dim, inverse
import datetime as dt
import readchar as rc
import time as ti

# Lage der einzelnen Textblöcke, Vorbelegung des dictionaries
bildschirm = {'zeilenende': 0, 'kopftrenner': 2, 'datentrenner': 0, 'fusstrenner': 0}


def loeschzeile(anfang, ende):
    """Lösche einen Bereich von Zeile <anfang> bis Zeile <ende>
    """
    while anfang < ende:
        move_cursor((0, anfang))
        clear("eol")
        anfang = anfang +1


def janein():
    """ Abfrage auf ja / nein
    Rückgabe true wenn ja
    Rückgabe nein wenn nein"""
    janeinschleife = True
    while janeinschleife:
        antwort = rc.readkey()
        if antwort == "j" or antwort == "J":
            janeinschleife = False
            return True
        elif antwort == "n" or antwort == "N":
            janeinschleife = False
            return False


def screensize(bildschirm):
    """Bildschirmgrösse abfragen und die diversen Trenner befüllen"""
    bildschirm['zeilenende'] = terminal.size[0]
    bildschirm['kopftrenner'] = 2
    bildschirm['datentrenner'] = int(terminal.size[1]/4) 
    bildschirm['fusstrenner'] = terminal.size[1] - 3
    return (bildschirm)


def titelzeile(titel):
    zeilenende = bildschirm['zeilenende']-len(titel)+1
    print_to((1,1), bold("PYTRACK"))
    print_to((zeilenende, 1), bold(titel))
    spalte = 1
    for spalte in range(0, terminal.size[0]):
        spalte = spalte + 1
        print_to((spalte, 2), "=")


def datenfeld(felder):
    """ Ausgabe der Datenfelder im Kopf
    Eingabe

    felder: Dictionary
    
    Ausgabe

    keine
    """
    for spalte in range(0, terminal.size[0]):
        spalte = spalte + 1
        print_to((spalte, bildschirm['datentrenner']), "-")
    datenzeile = bildschirm['kopftrenner']+2
    move_cursor((0, bildschirm['kopftrenner']+1))
    # clear("eos")
    for key, value in felder.items():
        if datenzeile < bildschirm['datentrenner']:
            print_to(((5, datenzeile)), key)
            print_to((25, datenzeile), inverse(value))
            datenzeile = datenzeile + 1   


def fusszeile(prompt, hilfe):
    spalte = 1
    for spalte in range(0,terminal.size[0]):
        spalte = spalte + 1
        print_to((spalte, bildschirm['fusstrenner']), "=")
    move_cursor((0, bildschirm['fusstrenner']+1))
    clear("eol")
    move_cursor((0, bildschirm['fusstrenner']+2))
    clear("eol")
    print_to((5, bildschirm['fusstrenner']+2), dim(hilfe))
    print_to((5, bildschirm['fusstrenner']+1), italic(prompt))


def menu(auswahl, titel):
    
    clear("screen")
    menuschleife = True
    auswahlliste = []
    titelzeile(titel)
    for zeile in auswahl:
        print_to((5, int(zeile['L'])), bold(zeile['K']))
        print_to((10, int(zeile['L'])), zeile['T'])
        auswahlliste += zeile['K']
    fusszeile("Eingabe: ", "Bitte Menüpunkt auswählen")
    while menuschleife:
        antwort = rc.readkey()
        if antwort in auswahlliste:
            menuschleife = False
    return antwort


def abfrage(prompt, hilfetext, texttemp):
    """Eingabezeile Abfrage

    Argumente
    prompt: Fester Textstring für die Eingabeaufforderung
    hilfetext: Fester Hilfetext
    texttemp: Variabler Textstring, nur die Eingabe!

    Rückgabe
    texttemp: Variabler Textstring, nur die Eingabe!
    status: Falls False -> Ende der Eingabe

    Wenn texttemp nicht leer und status = true -> Eingabe nicht abgeschlossen
    Wenn texttemp nicht leer und status = false -> Eingabe beendet
    Wenn texttemp leer und status = false -> Eingabe abgebrochen
    """
    status = True
    fusszeile(texttemp, hilfetext)        
    antwort = rc.readkey()
    if antwort == "\x04": # STRG-D -> Abbruch
        status = False
        texttemp = ""
    elif antwort == "\x7f" or antwort == "\x08" or antwort == "\x1b": # Backspace / STRG-H / ESC -> Eingabe löschen
        if len(texttemp) > 0:
            texttemp = texttemp[:-1]
    elif antwort == "\r":
        status = False
    else:
        texttemp = texttemp + antwort
    return (texttemp, status)


def trackeingabe():
    trackschleife = True
    trackidschleife = True
    anmerkungsschleife = True
    trackname = "tbd"
    typ = "tbd"
    nummer = "tbd"
    trackdatendict = {}
    trackdatendict['Trackname'] = trackname
    trackdatendict['Track_UUID'] = uuid7str()
    trackdatendict['Stand'] = str(dt.datetime.now())
    trackdatendict['Anmerkung'] = "tbd"
    trackdatendict['Fahrt-Typ'] = typ
    trackdatendict['Fahrt-Nummer'] = nummer
    schleifenprompt = ""
    anmerkung = ""
    abfragetemp = { 'abfrage': ' '}
    clear("screen")
#   Gesamte Trackeingabe
    while trackschleife:
#   Auswahl Track-ID
        while trackidschleife:
            sqlquery = "SELECT Track_UUID, Anmerkungen, Stand, Trackname FROM track WHERE Trackname LIKE %(abfrage)s ;"
            datenfeld(trackdatendict)
            antwort = abfrage("Track-ID: ", "Bitte neue Track-ID eingeben", schleifenprompt)
            schleifenprompt = antwort[0]
            status = antwort[1]
            if status:
                abfragetemp['abfrage'] = schleifenprompt+"%"
                datenbankcur.execute(sqlquery, abfragetemp)
                loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
                result = datenbankcur.fetchone()
                if datenbankcur.rowcount == 0:
                    print_to((10, 20), "Kein passender Track gefunden")
                else:
                    ausgabezeile = bildschirm['datentrenner']+3
                    print_to((5, bildschirm['datentrenner']+1), "Trackname")
                    print_to((25, bildschirm['datentrenner']+1), "Anmerkungen")
                    print_to((45, bildschirm['datentrenner']+1), "Track_UUID")
                    print_to((95, bildschirm['datentrenner']+1), "Stand")
                    while result:
                        print_to((5, ausgabezeile), result['Trackname'])
                        print_to((25, ausgabezeile), result ['Anmerkungen'])
                        print_to((45, ausgabezeile), result['Track_UUID'])
                        print_to((95, ausgabezeile), result ['Stand'])
                        result = datenbankcur.fetchone()
                        ausgabezeile = ausgabezeile + 1
            elif status is False and schleifenprompt == "": # Abbruch
                trackidschleife = False
                trackschleife = False
                return
            elif status is False and schleifenprompt != "": # Track-ID speichern
                loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
                ausgabezeile = bildschirm['datentrenner']+3
                print_to((5, ausgabezeile), "Trackname:")
                print_to((25, ausgabezeile), schleifenprompt)
                print_to((5, (ausgabezeile+2)), "Eingabe in Ordnung? ")
                if janein():
                    loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
                    trackidschleife = False
                    ausgabezeile = bildschirm['datentrenner']+3
                    print_to((5, ausgabezeile), "Trackname wird gespeichert")
                    trackname = schleifenprompt
                    trackdatendict['Trackname'] = schleifenprompt
                    ti.sleep(2)
                else:
                    loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
                    ausgabezeile = bildschirm['datentrenner']+3
                    print_to((5, ausgabezeile), "Trackname wird nicht gespeichert")
                    ti.sleep(2)
                status = False
        datenfeld(trackdatendict)
        while anmerkungsschleife:
            loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
            antwort = abfrage("Anmerkung", "Falls vorhanden, Anmerkung eingeben", anmerkung)
            anmerkung = antwort[0]
            status = antwort [1]
            if status:
                pass
            elif status is False and antwort == "": # Abbruch
                anmerkungsschleife = False
                trackschleife = False
            elif status is False and anmerkung != "": # Anmerkung speichern
                ausgabezeile = bildschirm['datentrenner']+3
                print_to((5, ausgabezeile), "Anmerkung:")
                print_to((25, ausgabezeile), anmerkung)
                print_to((5, (ausgabezeile+2)), "Eingabe in Ordnung?")
                if janein():
                    loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
                    anmerkungsschleife = False
                    trackschleife = False
                    ausgabezeile = bildschirm['datentrenner']+3
                    print_to((5, ausgabezeile), "Anmerkung wird gespeichert")
                else:
                    loeschzeile(bildschirm['datentrenner']+1, bildschirm['fusstrenner'])
                    ausgabezeile = bildschirm['datentrenner']+3
                    print_to((5, ausgabezeile), "Anmerkung wird nicht gespeichert")
        verbindungsql = "INSERT INTO track SET Track_UUID=%(Track_UUID)s, Trackname=%(Trackname)s, Stand=%(Stand)s, Anmerkungen=%(Anmerkung)s ;"
        trackdatendict['Trackname'] = trackname
        trackdatendict['Anmerkung'] = anmerkung
        print (trackdatendict)
        datenbankcur.execute(verbindungsql, trackdatendict) 
        verbindung.commit()

def track():
    trackschleife = True
    while trackschleife:
        trackmenue = [{'K': '1', 'L': '11', 'T': 'Track eingeben'},
        {'K': '2', 'L': '12', 'T': 'Track ändern'},
        # {'K': '3', 'L': '13', 'T': 'Fahrzeuge'},
        {'K': '0', 'L': '20', 'T': 'Hauptmenü'}]
        antwort = menu(trackmenue, "Trackmenü")
        if antwort == "1":
            trackeingabe()
        if antwort == "0":
            clear("screen")
            print_to((5,5), 'Programmende')
            trackschleife = False

try:
    screensize(bildschirm)
    schleife = True
    verbindung = pymysql.connect(read_default_file="~/.tba_lh.cnf", database="trackbash", cursorclass=pymysql.cursors.DictCursor)
    with verbindung.cursor() as datenbankcur:
        while schleife:
            hauptmenue = [{'K': '1', 'L': '11', 'T': 'Tracks'},
             {'K': '2', 'L': '12', 'T': 'Fahrpläne'},
             {'K': '3', 'L': '13', 'T': 'Fahrzeuge'},
             {'K': '0', 'L': '20', 'T': 'Beenden'}]
            antwort = menu(hauptmenue, "Hauptmenü")
            if antwort == "1":
                track()
            if antwort == "2":
                pass
            if antwort == "0":
                clear("screen")
                print_to((5,5), 'Programmende')
                schleife = False
except:
    print (datenbankcur._last_executed)    
finally:
    if 'verbindung' in locals() and verbindung:
        verbindung.close()
