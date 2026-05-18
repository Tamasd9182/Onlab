import sys
import os
import google.generativeai as genai

from KonfiguracioKezelo import KonfiguracioKezelo
from AdatKezelo import AdatKezelo
from MestersagesIntelligenciaKezelo import MestersagesIntelligenciaKezelo

from TavolsagElemzo import TavolsagElemzo
from ErzelemElemzo import ErzelemElemzo
from KonkretsagElemzo import KonkretsagElemzo
from SzofajElemzo import SzofajElemzo
from IsmetlodesElemzo import IsmetlodesElemzo

class Fovezerlo:
    def __init__(self):
        self.konfig = KonfiguracioKezelo()
        self.adat = AdatKezelo(self.konfig)
        self.ai = MestersagesIntelligenciaKezelo(self.konfig, self.adat)

    def programInditasa(self):
        while True:
            print("\n" + "="*40)
            print("   ÖNÁLLÓ LABOR - FŐMENÜ")
            print("="*40)
            print("[1] Emberi adatok letöltése")
            print("[2] AI válaszok generálása")
            print("[3] Adatok tisztítása és javítása")
            print("[4] Elemzések és Interaktív Diagramok")
            print("[5] Kilépés")
            
            valasztas = input("Választás (1-5): ").strip()
            
            if valasztas == '1':
                self.adat.emberiValaszokLekereseGSheetbol()
            elif valasztas == '2':
                self.ai.valaszokGeneralasaEsMentese()
            elif valasztas == '3':
                self.tisztitasAlmenu()
            elif valasztas == '4':
                self.elemzesekAlmenu()
            elif valasztas == '5':
                print("Kilépés...")
                sys.exit()
            else:
                print("Érvénytelen választás.")

    def tisztitasAlmenu(self):
        while True:
            print("\n--- TISZTÍTÁS ÉS JAVÍTÁS ALMENÜ ---")
            print("[1] Kézi javítás: Emberi adatok TXT-be")
            print("[2] Kézi javítás: Emberi adatok visszaállítása TXT-ből")
            print("[3] Automata Gépi Javítás")
            print("[4] AI válaszok automatikus tisztítása")
            print("[5] Vissza")
            
            valasztas = input("Választás (1-5): ").strip()
            if valasztas == '1':
                self.adat.adatokLapitasaTxtbe()
            elif valasztas == '2':
                self.adat.adatokVisszaallitasaTxtbol()
            elif valasztas == '3':
                self.gepiJavitas()
            elif valasztas == '4':
                self.adat.aiValaszokTisztitasaCsvben()
            elif valasztas == '5':
                break
            else:
                print("Érvénytelen választás.")

    def gepiJavitas(self):
        """A Gemini 3 Flash modellt használó, automata adattisztító folyamat."""
        print("\n" + "="*50)
        print("   AI AUTOMATA ADATTISZTÍTÁS (GEMINI 3 FLASH)   ")
        print("="*50)
        
        print("[1/4] Adatok kigyűjtése és lapítása TXT fájlba...")
        self.adat.adatokLapitasaTxtbe()
        
        fajl_neve = "lapitott_adatok.txt" 

        try:
            with open(fajl_neve, "r", encoding="utf-8") as f:
                nyers_szoveg = f.read()
        except FileNotFoundError:
            print(f"[HIBA] Nem található a '{fajl_neve}' fájl!")
            return

        print("[2/4] Adatok küldése az AI-nak... (Ez a mennyiségtől függően percekig is eltarthat!)")
        
        API_KULCS = "AIzaSyCsbSPZyoAqkwl8BYbeEmGGERQMOQJWAxg"
        genai.configure(api_key=API_KULCS) 
        
        model = genai.GenerativeModel('models/gemini-3-flash-preview')

        prompt = f"""
        Az alábbi szöveg egy kérdőíves felmérés nyers eredménye. A feladatod, hogy PONTOSAN ugyanannyi sorban és ugyanabban a szerkezeti formátumban add vissza a szöveget, ahogy kapod, de a válaszokat tisztítsd meg az alábbi szabályok szerint:
        
        SZIGORÚ SZABÁLYOK AZ AI RÉSZÉRE:
        1. JAVÍTÁS: Javítsd a durva elgépeléseket és helyesírási hibákat.
        2. LÉNYEGRE TÖRÉS: Ha a válasz egy teljes mondat vagy felesleges magyarázkodás, de a lényege egyetlen szó, akkor csak azt az egy szót hagyd meg (pl: "Erre a szóra az jut eszembe, hogy asztal" -> "asztal").
        3. SOROK SZÁMA: Szigorúan TILOS sorokat összevonni vagy törölni! Ha a forrásban 36 sor van, a válaszban is PONTOSAN 36 sornak kell lennie!
        4. ÜRES CELLÁK: Ha egy sorban nincs javítandó szó, vagy a válasz hiányzik, ne töröld a sort! Add vissza változatlanul azt a sort vagy írd be, hogy "HIBA", de a sor maradjon meg!
        5. TILTÁS: Ne írj semmilyen bevezető szöveget, magyarázatot, vagy lezárást. Csak és kizárólag a megtisztított adatsorokat add vissza!
        
        Nyers adatok:
        {nyers_szoveg}
        """

        try:
            valasz = model.generate_content(prompt)
            tisztitott_szoveg = valasz.text

            print("[3/4] Az AI végzett. Tisztított adatok felülírása a TXT fájlban...")
            with open(fajl_neve, "w", encoding="utf-8") as f:
                f.write(tisztitott_szoveg)

            print("[4/4] Adatok visszaállítása táblázatos formátumba...")
            self.adat.adatokVisszaallitasaTxtbol()
            
            print("\n[SIKER] Az AI Automata tisztítás és táblázatba rendezés befejeződött!")

        except Exception as e:
            print(f"\n[Kritikus Hiba] Az AI kommunikáció vagy a feldolgozás során hiba történt:\n{e}")

    def elemzesekAlmenu(self):
        while True:
            print("\n--- ELEMZÉSEK ÉS INTERAKTÍV DIAGRAMOK ---")
            print("[1] Asszociációs távolság mérése")
            print("[2] Érzelemelemzés")
            print("[3] Konkrétságmérés")
            print("[4] Szófajelemzés")
            print("[5] Szóismétlés")
            print("[6] Vissza a főmenübe")

            valasztas = input("Választás (1-6): ").strip()

            if valasztas == '1':
                print("\n[Rendszer] Távolságmérő és Diagram modul betöltése...")
                vizualizalo = TavolsagElemzo()
                vizualizalo.interaktiv_menu()
            elif valasztas == '2':
                print("\n[Rendszer] Érzelemelemző és Diagram modul betöltése...")
                erzelem_vizualizalo = ErzelemElemzo()
                erzelem_vizualizalo.interaktiv_menu()
            elif valasztas == '3':
                print("\n[Rendszer] Konkrétságműszer és Diagram modul betöltése...")
                konkret_vizualizalo = KonkretsagElemzo()
                konkret_vizualizalo.interaktiv_menu()
            elif valasztas == '4':
                print("\n[Rendszer] Szófajelemző és Diagram modul betöltése...")
                szofaj_vizualizalo = SzofajElemzo()
                szofaj_vizualizalo.interaktiv_menu()
            elif valasztas == '5':
                print("\n[Rendszer] Szóismétlés mérő és Diagram modul betöltése...")
                ismetlodes_vizualizalo = IsmetlodesElemzo()
                ismetlodes_vizualizalo.interaktiv_menu()
            elif valasztas == '6':
                break
            else:
                print("Érvénytelen választás.")

if __name__ == "__main__":
    alkalmazas = Fovezerlo()
    alkalmazas.programInditasa()