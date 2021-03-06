from datetime import date
import bottle
import os
import random
import hashlib
from model import Uporabnik, Proracun

imenik_s_podatki = 'uporabniki'
uporabniki = {}
skrivnost = 'TO JE ENA HUDA SKRIVNOST'

if not os.path.isdir(imenik_s_podatki):
    os.mkdir(imenik_s_podatki)

for ime_datoteke in os.listdir(imenik_s_podatki):
    uporabnik = Uporabnik.nalozi_stanje(os.path.join(imenik_s_podatki, ime_datoteke))
    uporabniki[uporabnik.uporabnisko_ime] = uporabnik

def poisci_racun(ime_polja):
    ime_racuna = bottle.request.forms.getunicode(ime_polja)
    proracun = proracun_uporabnika()
    return proracun.poisci_racun(ime_racuna)

def poisci_kuverto(ime_polja):
    ime_kuverte = bottle.request.forms.getunicode(ime_polja)
    proracun = proracun_uporabnika()
    return proracun.poisci_kuverto(ime_kuverte or None)

def trenutni_uporabnik():
    uporabnisko_ime = bottle.request.get_cookie('uporabnisko_ime', secret=skrivnost)
    if uporabnisko_ime is None:
        bottle.redirect('/prijava/')
    return uporabniki[uporabnisko_ime]

def proracun_uporabnika():
    return trenutni_uporabnik().proracun

def shrani_trenutnega_uporabnika():
    uporabnik = trenutni_uporabnik()
    uporabnik.shrani_stanje(os.path.join('uporabniki', f'{uporabnik.uporabnisko_ime}.json'))

@bottle.get('/')
def zacetna_stran():
    bottle.redirect('/proracun/')

@bottle.get('/proracun/')
def nacrtovanje_proracuna():
    proracun = proracun_uporabnika()
    return bottle.template('proracun.html', proracun=proracun)

@bottle.get('/analiza/')
def analiza():
    return bottle.template('analiza.html')

@bottle.get('/pomoc/')
def pomoc():
    return bottle.template('pomoc.html')

@bottle.get('/prijava/')
def prijava_get():
    return bottle.template('prijava.html')

@bottle.post('/prijava/')
def prijava_post():
    uporabnisko_ime = bottle.request.forms.getunicode('uporabnisko_ime')
    geslo = bottle.request.forms.getunicode('geslo')
    h = hashlib.blake2b()
    h.update(geslo.encode(encoding='utf-8'))
    zasifrirano_geslo = h.hexdigest()
    if 'nov_racun' in bottle.request.forms and uporabnisko_ime not in uporabniki:
        uporabnik = Uporabnik(
            uporabnisko_ime,
            zasifrirano_geslo,
            Proracun()
        )
        uporabniki[uporabnisko_ime] = uporabnik
    else:
        uporabnik = uporabniki[uporabnisko_ime]
        uporabnik.preveri_geslo(zasifrirano_geslo)
    bottle.response.set_cookie('uporabnisko_ime', uporabnik.uporabnisko_ime, path='/', secret=skrivnost)
    bottle.redirect('/')

@bottle.post('/odjava/')
def odjava():
    bottle.response.delete_cookie('uporabnisko_ime', path='/')
    bottle.redirect('/')

@bottle.post('/dodaj-preliv/')
def dodaj_preliv():
    proracun = proracun_uporabnika()
    znesek = int(bottle.request.forms['znesek'])
    datum = date.today().strftime('%Y-%m-%d')
    opis = bottle.request.forms.getunicode('opis')
    racun = poisci_racun('racun')
    kuverta = poisci_kuverto('kuverta')
    proracun.nov_preliv(znesek, datum, opis, racun, kuverta)
    shrani_trenutnega_uporabnika()
    bottle.redirect('/')

@bottle.post('/premakni-denar/')
def premakni_denar():
    proracun = proracun_uporabnika()
    kuverta1 = poisci_kuverto('kuverta1')
    kuverta2 = poisci_kuverto('kuverta2')
    znesek = int(bottle.request.forms['znesek'])
    proracun.premakni_denar(kuverta1, kuverta2, znesek)
    shrani_trenutnega_uporabnika()
    bottle.redirect('/')

@bottle.post('/dodaj-racun/')
def dodaj_racun():
    proracun = proracun_uporabnika()
    proracun.nov_racun(bottle.request.forms.getunicode('ime'))
    shrani_trenutnega_uporabnika()
    bottle.redirect('/')

@bottle.post('/dodaj-kuverto/')
def dodaj_kuverto():
    proracun = proracun_uporabnika()
    proracun.nova_kuverta(bottle.request.forms.getunicode('ime'))
    shrani_trenutnega_uporabnika()
    bottle.redirect('/')

@bottle.post('/odstrani-kuverto/')
def odstrani_kuverto():
    proracun = proracun_uporabnika()
    kuverta = poisci_kuverto('kuverta')
    proracun.odstrani_kuverto(kuverta)
    shrani_trenutnega_uporabnika()
    bottle.redirect('/')


bottle.run(debug=True, reloader=True)