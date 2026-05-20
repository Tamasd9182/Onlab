from google import genai
from google.genai import types
from openai import OpenAI
import time
import os
import csv
import base64
import PIL.Image
import concurrent.futures

class MestersagesIntelligenciaKezelo:
    def __init__(self, konfig_kezelo, adat_kezelo):
        self.konfig = konfig_kezelo
        self.adat = adat_kezelo
        
        gemini_kulcs = self.konfig.apiKulcsLekerese("gemini")
        self.gemini_client = genai.Client(api_key=gemini_kulcs) if gemini_kulcs else None

        openai_kulcs = self.konfig.apiKulcsLekerese("openai")
        self.openai_client = OpenAI(api_key=openai_kulcs) if openai_kulcs else None

    def _kepBase64Kodolasa(self, kep_eleresi_ut):
        with open(kep_eleresi_ut, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _normalizaltTemp(self, temp_szoveg):
        try:
            t_tiszta = str(temp_szoveg).strip().replace(',', '.')
            t_float = float(t_tiszta)
            return str(round(t_float, 1)).replace('.', ',')
        except:
            return str(temp_szoveg).strip()

    def _marLetezoValaszokBeolvasasa(self, fajlnev):
        kesz_adatok = set()
        if not os.path.exists(fajlnev):
            return kesz_adatok

        try:
            with open(fajlnev, 'r', encoding='utf-8-sig') as f:
                olvaso = csv.reader(f, delimiter=';')
                fejlec = next(olvaso, None)
                if not fejlec:
                    return kesz_adatok
                
                kerdes_oszlopok = [i for i, col in enumerate(fejlec) if col.startswith("Kerdes_")]
                
                for sor in olvaso:
                    if not sor or len(sor) < 2:
                        continue
                    m_nev = sor[0].strip()
                    temp = self._normalizaltTemp(sor[1])
                    
                    for o_idx in kerdes_oszlopok:
                        if o_idx < len(sor) and sor[o_idx].strip() and sor[o_idx].strip() != "HIBA" and not sor[o_idx].startswith("API_HIBA"):
                            k_szam = fejlec[o_idx].replace("Kerdes_", "")
                            kesz_adatok.add(f"{m_nev}|{temp}|{k_szam}")
        except Exception as e:
            print(f"[Figyelem] Nem sikerült beolvasni a korábbi mentéseket: {e}")
        
        return kesz_adatok

    def valaszokGeneralasaEsMentese(self, kimeneti_fajlnev="ai_nyers_valaszok.csv"):
        if not self.gemini_client and not self.openai_client:
            print("[HIBA] Egyik AI kliens sincs beállítva. Ellenőrizd az API kulcsokat!")
            return

        print("\n" + "="*40)
        print("   AI VÁLASZOK GENERÁLÁSA INDUL ")
        print("="*40)
        
        ai_beallitasok = self.konfig.ertekLekerese("ai_beallitasok")
        modellek_listaja = ai_beallitasok.get("modellek", [])
        homerseklet_kezdo = float(ai_beallitasok.get("homerseklet_kezdo", 0.0))
        homerseklet_max = float(ai_beallitasok.get("homerseklet_max", 2.0))
        homerseklet_lepes = float(ai_beallitasok.get("homerseklet_lepes", 0.5))
        kerdesek_listaja = self.konfig.kerdesekLekerese()
        
        if not modellek_listaja or not kerdesek_listaja:
            print("Hiba: Nincsenek definiálva modellek vagy kérdések.")
            return

        fejlec = ["Modell_Neve", "Homerseklet"]
        for kerdes in kerdesek_listaja:
            fejlec.append(f"Kerdes_{kerdes['sorszam']}")

        fajl_uj = not os.path.exists(kimeneti_fajlnev)
        mar_kesz_halmaz = self._marLetezoValaszokBeolvasasa(kimeneti_fajlnev)
        if mar_kesz_halmaz:
            print(f"[Rendszer] {len(mar_kesz_halmaz)} korábbi sikeres részválasz feltérképezve.")

        if fajl_uj:
            with open(kimeneti_fajlnev, 'w', encoding='utf-8-sig', newline='') as f:
                csv.writer(f, delimiter=';').writerow(fejlec)

        osszes_fazis = len(modellek_listaja) * int(((homerseklet_max - homerseklet_kezdo) / homerseklet_lepes) + 1)
        jelenlegi_fazis = 0

        for modell_nev in modellek_listaja:
            is_openai = "gpt" in modell_nev.lower()
            
            if (is_openai and not self.openai_client) or (not is_openai and not self.gemini_client):
                continue

            hivatalos_modell_nev = modell_nev
            if not is_openai and not hivatalos_modell_nev.startswith("models/"):
                hivatalos_modell_nev = f"models/{hivatalos_modell_nev}"

            aktualis_homerseklet = homerseklet_kezdo
            while aktualis_homerseklet <= homerseklet_max:
                jelenlegi_fazis += 1
                
                magyar_homerseklet_szoveg = self._normalizaltTemp(aktualis_homerseklet)
                
                hianyzo_kerdesek = []
                for kerdes in kerdesek_listaja:
                    kulcs = f"{modell_nev}|{magyar_homerseklet_szoveg}|{kerdes['sorszam']}"
                    if kulcs not in mar_kesz_halmaz:
                        hianyzo_kerdesek.append(kerdes)

                    if not hianyzo_kerdesek:
                        aktualis_homerseklet += homerseklet_lepes
                        aktualis_homerseklet = round(aktualis_homerseklet, 1)
                        continue

                print(f"\n[{jelenlegi_fazis}/{osszes_fazis}] Fázis indítása: {modell_nev} (Temp: {magyar_homerseklet_szoveg})")
                print(f"   -> Új/Hiányzó kérdések száma ebben a fázisban: {len(hianyzo_kerdesek)} / {len(kerdesek_listaja)}")

                fajl_tartalom = []
                sor_index = -1
                
                with open(kimeneti_fajlnev, 'r', encoding='utf-8-sig') as f:
                    olvaso = csv.reader(f, delimiter=';')
                    fajl_tartalom = list(olvaso)

                for idx, sor in enumerate(fajl_tartalom):
                    if sor and sor[0] == modell_nev and self._normalizaltTemp(sor[1]) == magyar_homerseklet_szoveg:
                        sor_index = idx
                        break

                if sor_index == -1:
                    uj_sor = [modell_nev, magyar_homerseklet_szoveg] + [""] * len(kerdesek_listaja)
                    fajl_tartalom.append(uj_sor)
                    sor_index = len(fajl_tartalom) - 1

                for kerdes in hianyzo_kerdesek:
                    q_sorszam = kerdes["sorszam"]
                    prompt_szoveg = kerdes.get("prompt", "")
                    kep_eleresi_ut = kerdes.get("kep_eleresi_ut", "")
                    tisztitott_valasz = "HIBA"
                    
                    print(f"      -> {q_sorszam}. kérdés küldése... ", end="", flush=True)

                    def api_lekerdezes():
                        if is_openai:
                            uzenetek = [{"role": "user", "content": [{"type": "text", "text": prompt_szoveg}]}]
                            if kep_eleresi_ut and os.path.exists(kep_eleresi_ut):
                                base64_kep = self._kepBase64Kodolasa(kep_eleresi_ut)
                                mime_type = "image/jpeg" if kep_eleresi_ut.lower().endswith(".jpg") else "image/png"
                                uzenetek[0]["content"].append({
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime_type};base64,{base64_kep}"}
                                })
                            valasz = self.openai_client.chat.completions.create(
                                model=hivatalos_modell_nev,
                                messages=uzenetek,
                                temperature=aktualis_homerseklet
                            )
                            return valasz.choices[0].message.content.replace('\n', ' ').strip()
                        else:
                            bemeneti_tartalom = [prompt_szoveg]
                            if kep_eleresi_ut and os.path.exists(kep_eleresi_ut):
                                megnyitott_kep = PIL.Image.open(kep_eleresi_ut)
                                bemeneti_tartalom.append(megnyitott_kep)

                            valasz = self.gemini_client.models.generate_content(
                                model=hivatalos_modell_nev,
                                contents=bemeneti_tartalom,
                                config=types.GenerateContentConfig(temperature=aktualis_homerseklet)
                            )
                            return valasz.text.replace('\n', ' ').strip()
                    
                    try:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            jovo = executor.submit(api_lekerdezes)
                            tisztitott_valasz = jovo.result(timeout=600.0) 
                        
                        print("OK")
                        time.sleep(3.5)
                        
                    except concurrent.futures.TimeoutError:
                        print("IDŐTÚLLÉPÉS (10 PERC)!")
                        tisztitott_valasz = "API_HIBA: Timeout (10 perc)"
                        time.sleep(2.0)
                    except Exception as e:
                        print(f"HIBA!")
                        print(f"         [Ok]: {e}")
                        tisztitott_valasz = f"API_HIBA: {str(e)[:30]}"
                        time.sleep(5.0)

                    fajl_tartalom[sor_index][q_sorszam + 1] = tisztitott_valasz

                    with open(kimeneti_fajlnev, 'w', encoding='utf-8-sig', newline='') as f:
                        csv.writer(f, delimiter=';').writerows(fajl_tartalom)

                aktualis_homerseklet += homerseklet_lepes
                aktualis_homerseklet = round(aktualis_homerseklet, 1)
                
        print("\n========================================")
        print("   AI GENERÁLÁS SIKERESEN BEFEJEZŐDÖTT!")
        print("========================================")