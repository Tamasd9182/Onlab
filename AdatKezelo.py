import csv
import re
import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AdatKezelo:
    def __init__(self, konfig_kezelo):
        self.konfig = konfig_kezelo
        self.elvalaszto = " |#| "

    def emberiValaszokLekereseGSheetbol(self, mentes_fajlnev="emberi_nyers_valaszok.csv"):
        hitelesito_fajl = self.konfig.ertekLekerese("google_forms_beallitasok", "hitelesito_fajl")
        tablazat_neve = self.konfig.ertekLekerese("google_forms_beallitasok", "tablazat_neve")

        jogosultsagok = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(hitelesito_fajl, jogosultsagok)
            client = gspread.authorize(creds)
            
            sheet = client.open(tablazat_neve).sheet1  
            nyers_adatok = sheet.get_all_values()
            
            if not nyers_adatok or len(nyers_adatok) < 2:
                print("A táblázat még üres, vagy csak fejléc van benne, nincs mit letölteni.")
                return False
                
            fejlec = nyers_adatok[0]
            adat_sorok = nyers_adatok[1:]
            
            adatTabla = pd.DataFrame(adat_sorok, columns=fejlec)
            adatTabla.to_csv(mentes_fajlnev, index=False, sep=';', encoding="utf-8-sig")
            
            print(f"Sikeres letöltés! Az emberi válaszok felülírás nélkül (nyersen) elmentve ide: {mentes_fajlnev}")
            return True
            
        except FileNotFoundError:
            print(f"HIBA: A '{hitelesito_fajl}' fájl nem található a hitelesítéshez.")
            return False
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"HIBA: A '{tablazat_neve}' nevű táblázat nem található a Google Drive-on.")
            return False
        except Exception as e:
            print(f"Hiba történt a letöltés során: {e}")
            return False

    def aiSzovegTisztitasa(self, szoveg, egyszavas_feladat):
        szoveg = str(szoveg).strip()
        if not szoveg:
            return szoveg
            
        szoveg = re.sub(r'(?i)(thinking|thought|thoughts|silently|the user wants).*?\n', '', szoveg)
        
        if not egyszavas_feladat:
            return szoveg.strip()

        sorok = szoveg.split('\n')
        vegs_valasz = ""
        for sor in reversed(sorok):
            if sor.strip():
                vegs_valasz = sor.strip()
                break
                
        if len(vegs_valasz.split()) > 3 or "thinking" in vegs_valasz.lower():
            szavak = vegs_valasz.split()
            utolso_szo = szavak[-1]
            utolso_szo = re.sub(r'[^\wÁÉÍÓÖŐÚÜŰáéíóöőúüű]', '', utolso_szo)
            return utolso_szo

        return vegs_valasz

    def aiValaszokTisztitasaCsvben(self, bemeneti_fajl="ai_nyers_valaszok.csv", kimeneti_fajl="ai_tisztitott_valaszok.csv"):
        kerdesek = self.konfig.kerdesekLekerese()
        tisztitott_sorok = []
        
        try:
            with open(bemeneti_fajl, 'r', encoding='utf-8-sig') as be_fajl:
                olvaso = csv.reader(be_fajl, delimiter=';')
                for sor_index, sor in enumerate(olvaso):
                    if not sor:
                        continue
                    uj_sor = []
                    for oszlop_index, cella in enumerate(sor):
                        if sor_index == 0 or oszlop_index < 2:
                            uj_sor.append(cella)
                        else:
                            kerdes_adat = kerdesek[oszlop_index - 2]
                            egyszavas = kerdes_adat.get("egyszavas", True)
                            uj_sor.append(self.aiSzovegTisztitasa(cella, egyszavas))
                    tisztitott_sorok.append(uj_sor)
        except FileNotFoundError:
            print(f"HIBA: A '{bemeneti_fajl}' nem található a tisztításhoz!")
            return

        with open(kimeneti_fajl, 'w', encoding='utf-8-sig', newline='') as ki_fajl:
            iro = csv.writer(ki_fajl, delimiter=';')
            iro.writerows(tisztitott_sorok)
            
        print(f"Kész! Az AI válaszok megtisztítva és elmentve ide: '{kimeneti_fajl}'.")

    def adatokLapitasaTxtbe(self, csv_fajl="emberi_nyers_valaszok.csv", txt_fajl="lapitott_adatok.txt"):
        try:
            with open(csv_fajl, 'r', encoding='utf-8-sig') as f:
                sorok = list(csv.reader(f, delimiter=';'))
            if len(sorok) < 2:
                print("A CSV fájl üres, nincs mit lapítani.")
                return
                
            fejlec = sorok[0]
            
            with open(txt_fajl, 'w', encoding='utf-8') as f:
                f.write("Te egy szigorú és precíz adatfeldolgozó algoritmus vagy. Keresd meg a szövegben az <OSZLOP_X> és </OSZLOP_X> tag-eket. Ezek között magyar nyelvű, |#| jelekkel elválasztott adatokat találsz.\n\n")
                f.write("A FELADATOD: Alkalmazd az alábbi tisztítási szabályokat a tag-eken belüli adatokra, majd add vissza az eredményt PONTOSAN az eredeti formátumban.\n\n")
                f.write("TISZTÍTÁSI SZABÁLYOK:\n")
                f.write("1. Javítsd a helyesírási hibákat.\n")
                f.write("2. Töröld az összes emojit.\n")
                f.write("3. Töröld az értelmetlen random karakterláncokat (pl. 'asdfg', 'aaaa') és a felesleges rövidítéseket.\n")
                f.write("4. Ha a cella eredetileg üres volt, VAGY a tisztítás (pl. szemét törlése) miatt kiürül, HAGYD ÜRESEN, DE AZ ELVÁLASZTÓ JELT (|#|) KÖTELEZŐ MEGTARTANI!\n")
                f.write("5. KRITIKUS SZABÁLY: SZIGORÚAN tilos megváltoztatni a |#| jelek számát! Az adatok struktúrája nem sérülhet.\n\n")
                f.write("KIMENETI KÖVETELMÉNYEK:\n")
                f.write("- KIZÁRÓLAG az <OSZLOP_X> tag-eket és a közte lévő tisztított adatokat adhatod vissza.\n")
                f.write("- TILOS bármilyen bevezető szöveget, magyarázatot, üdvözlést vagy záró gondolatot írni.\n")
                f.write("- TILOS markdown formázást (pl. ``` vagy félkövér betű) használni.\n\n")
                f.write("FELDOLGOZANDÓ ADATOK:\n\n")
                
                for i in range(1, len(fejlec)):
                    oszlop_adatok = [sor[i].strip() for sor in sorok[1:]]
                    lapitott_szoveg = self.elvalaszto.join(oszlop_adatok)
                    f.write(f"<OSZLOP_{i}>\n{lapitott_szoveg}\n</OSZLOP_{i}>\n\n")

            print(f"Siker! A lapított adatok és a fő prompt egyetlen másolható blokkban kimentve ide: {txt_fajl}")
            
        except FileNotFoundError:
            print(f"HIBA: A '{csv_fajl}' nem található! Előbb le kell tölteni az adatokat.")
        except Exception as e:
            print(f"Hiba a lapításnál: {e}")

    def adatokVisszaallitasaTxtbol(self, txt_fajl="lapitott_adatok.txt", csv_fajl="emberi_javitott_valaszok.csv", eredeti_csv="emberi_nyers_valaszok.csv"):
        if not os.path.exists(txt_fajl):
            print(f"HIBA: A '{txt_fajl}' nem található!")
            return

        try:
            with open(eredeti_csv, 'r', encoding='utf-8-sig') as f:
                emerald_sorok = list(csv.reader(f, delimiter=';'))
            
            fejlec = emerald_sorok[0]
            eredeti_valaszok_szama = len(emerald_sorok) - 1

            with open(txt_fajl, 'r', encoding='utf-8') as f:
                txt_tartalom = f.read()

            uj_oszlopok = []
            
            uj_oszlopok.append([sor[0] for sor in emerald_sorok])

            for i in range(1, len(fejlec)):
                kezdo_tag = f"<OSZLOP_{i}>"
                zaro_tag = f"</OSZLOP_{i}>"
                
                kezdo_idx = txt_tartalom.find(kezdo_tag)
                zaro_idx = txt_tartalom.find(zaro_tag)

                if kezdo_idx != -1 and zaro_idx != -1:
                    adat_szoveg = txt_tartalom[kezdo_idx + len(kezdo_tag):zaro_idx].strip()
                    
                    adat_szoveg = adat_szoveg.replace('```', '').replace('**', '')
                    
                    javitott_elemek = [elem.strip() for elem in adat_szoveg.split(self.elvalaszto)]

                    if len(javitott_elemek) == eredeti_valaszok_szama:
                        uj_oszlopok.append([fejlec[i]] + javitott_elemek)
                    else:
                        print(f"VIGYÁZAT: A(z) {i}. oszlop szerkezete elcsúszott az AI javítás során! "
                              f"(Eredeti méret: {eredeti_valaszok_szama}, AI méret: {len(javitott_elemek)}). "
                              f"Ezt az oszlopot nem írjuk felül, az eredeti, nyers adatokat tartjuk meg.")
                        uj_oszlopok.append([sor[i] for sor in emerald_sorok])
                else:
                    print(f"VIGYÁZAT: A(z) {i}. oszlop tag-je (<OSZLOP_{i}>) hiányzik a TXT-ből! Eredeti adat megtartva.")
                    uj_oszlopok.append([sor[i] for sor in emerald_sorok])

            vegleges_sorok = []
            for sor_idx in range(len(emerald_sorok)):
                aktualis_sor = [uj_oszlopok[oszlop_idx][sor_idx] for oszlop_idx in range(len(fejlec))]
                vegleges_sorok.append(aktualis_sor)

            with open(csv_fajl, 'w', encoding='utf-8-sig', newline='') as f:
                iro = csv.writer(f, delimiter=';')
                iro.writerows(vegleges_sorok)
                
            print(f"\nSikeres visszaállítás! Az ellenőrzött adatok elmentve ide: {csv_fajl}")

        except Exception as e:
            print(f"Hiba a visszaállítás során: {e}")

    def reszEredmenyMenteseCsvbe(self, adatok_listaja, kimeneti_fajlnev):
        try:
            with open(kimeneti_fajlnev, 'w', encoding='utf-8-sig', newline='') as fajl:
                iro = csv.writer(fajl, delimiter=';')
                iro.writerows(adatok_listaja)
            print(f"Részeredmény kimentve: {kimeneti_fajlnev}")
        except Exception as e:
            print(f"HIBA a CSV mentésekor ({kimeneti_fajlnev}): {e}")