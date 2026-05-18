import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from deep_translator import GoogleTranslator
import warnings

warnings.filterwarnings("ignore")

class KonkretsagElemzo:
    def __init__(self, konfig_json="konfiguracio.json", ai_csv="ai_tisztitott_valaszok.csv", ember_csv="emberi_javitott_valaszok.csv"):
        self.konfig_json = konfig_json
        self.ai_csv = ai_csv
        self.ember_csv = ember_csv
        
        self.fordito = GoogleTranslator(source='hu', target='en')
        
        self.brysbaert_szotar = {}
        self.brysbaert_betoltve = False
        self._brysbaertBetoltese()
        
        self.kerdesek = self._load_konfig()
        self.ai_df = self._load_csv(self.ai_csv)
        self.ember_df = self._load_csv(self.ember_csv)
        
        sns.set_theme(style="whitegrid")

    def _load_konfig(self):
        if os.path.exists(self.konfig_json):
            with open(self.konfig_json, 'r', encoding='utf-8') as f:
                return json.load(f).get("kerdesek", [])
        return []

    def _load_csv(self, path):
        if os.path.exists(path):
            return pd.read_csv(path, sep=';', encoding='utf-8-sig')
        return pd.DataFrame()

    def _brysbaertBetoltese(self):
        if not self.brysbaert_betoltve:
            print("[Rendszer] Brysbaert Excel tábla (Konkrétságmérés) betöltése...")
            try:
                df = pd.read_excel('Concreteness_ratings_Brysbaert.xlsx')
                for _, sor in df.iterrows():
                    szo = str(sor['Word']).lower()
                    self.brysbaert_szotar[szo] = {
                        "pont": float(sor['Conc.M']),
                        "szoras": float(sor['Conc.SD']),
                        "ismerteSzazalek": float(sor['Percent_known'])
                    }
                self.brysbaert_betoltve = True
            except FileNotFoundError:
                print("[HIBA] A 'Concreteness_ratings_Brysbaert.xlsx' fájl nem található!")
            except Exception as e:
                print(f"[HIBA] Hiba az Excel betöltésekor: {e}")

    def _elso_valid_szo_kinyerese(self, hivoszo, valasz_szoveg):
        if pd.isna(valasz_szoveg) or str(valasz_szoveg).strip() in ["", "HIBA"]:
            return None
            
        szavak = [sz.strip(".,!?\"' ").lower() for sz in str(valasz_szoveg).split(',')]
        szavak = [sz for sz in szavak if sz]
        
        hivoszo_low = hivoszo.lower() if hivoszo else ""
        
        for szo in szavak:
            if hivoszo_low and szo == hivoszo_low:
                continue
            return szo
        return None

    def _konkretsag_szamitasa(self, magyar_szo):
        if not magyar_szo or magyar_szo == "HIBA" or not self.brysbaert_betoltve:
            return np.nan

        try:
            angol_szoveg = self.fordito.translate(magyar_szo).lower()
            szavak = angol_szoveg.replace('.', '').replace(',', '').replace('?', '').split()
            
            stop_szavak = {"a", "an", "the", "and", "but", "or", "because", "is", "am", "are", "was", "were", "to", "of", "in", "it", "i", "you", "he", "she"}
            
            sulyozott_pontok = 0.0
            sulyok_osszege = 0.0
            
            i = 0
            while i < len(szavak):
                if i < len(szavak) - 1:
                    kif = szavak[i] + " " + szavak[i+1]
                    if kif in self.brysbaert_szotar and self.brysbaert_szotar[kif]["ismerteSzazalek"] > 0.9:
                        pont = self.brysbaert_szotar[kif]["pont"]
                        suly = 1 / ((self.brysbaert_szotar[kif]["szoras"] + 0.01) ** 2)
                        sulyozott_pontok += pont * suly
                        sulyok_osszege += suly
                        i += 2
                        continue 

                szo = szavak[i]
                if szo in self.brysbaert_szotar and self.brysbaert_szotar[szo]["ismerteSzazalek"] > 0.9 and szo not in stop_szavak:
                    pont = self.brysbaert_szotar[szo]["pont"]
                    suly = 1 / ((self.brysbaert_szotar[szo]["szoras"] + 0.01) ** 2)
                    sulyozott_pontok += pont * suly
                    sulyok_osszege += suly
                i += 1
                
            if sulyok_osszege > 0:
                return sulyozott_pontok / sulyok_osszege
            else:
                return np.nan
        except Exception:
            return np.nan

    def interaktiv_menu(self):
        print("\n" + "="*50)
        print("  CÉLZOTT DIAGRAM KÉSZÍTŐ - KONKRÉTSÁGMÉRÉS  ")
        print("="*50)

        valasztott_teszt = "konkretsag"

        elerheto_kerdesek = [k for k in self.kerdesek if valasztott_teszt in k.get("futtatando_tesztek", [])]
        
        if not elerheto_kerdesek:
            print(f"Nincs olyan kérdés, amire a(z) '{valasztott_teszt}' futtatható lenne.")
            return
            
        elerheto_id_k = [str(k["sorszam"]) for k in elerheto_kerdesek]
        print(f"\nEhhez a teszthez engedélyezett kérdések (Sorszámok): {', '.join(elerheto_id_k)}")
        
        kell = input("Melyiket elemezzük? (Vesszővel elválasztva, vagy 'mind'): ").strip().lower()
        if kell == 'mind':
            kivalasztott_kerdesek = elerheto_kerdesek
        else:
            kell_lista = [x.strip() for x in kell.split(',')]
            kivalasztott_kerdesek = [k for k in elerheto_kerdesek if str(k["sorszam"]) in kell_lista]

        if not kivalasztott_kerdesek:
            print("Nem választottál érvényes kérdést.")
            return

        k_oszlopok = [f"Kerdes_{k['sorszam']}" for k in kivalasztott_kerdesek]
        elerheto_modellek = set()
        
        for k_oszlop in k_oszlopok:
            if k_oszlop in self.ai_df.columns:
                valid_df = self.ai_df[~self.ai_df[k_oszlop].isin(["", "HIBA", np.nan])]
                elerheto_modellek.update(valid_df['Modell_Neve'].dropna().unique())
        
        if not elerheto_modellek:
            print("A kiválasztott kérdésekre egyetlen AI modell sem adott érvényes választ!")
            return
            
        print("\nSikeres eredményt adó AI modellek ezeknél a kérdéseknél:")
        modellek_lista = sorted(list(elerheto_modellek))
        
        for i, m in enumerate(modellek_lista):
            print(f"[{i+1}] {m}")
        
        v_modellek = input("\nMely modelleket vonjuk be? (Sorszámok vesszővel elválasztva, vagy 'mind'): ").strip()
        
        if v_modellek.lower() == 'mind':
            szurt_modellek = modellek_lista
        else:
            kivalasztott_indexek = [int(idx.strip()) - 1 for idx in v_modellek.split(',') if idx.strip().isdigit()]
            szurt_modellek = [modellek_lista[i] for i in kivalasztott_indexek if 0 <= i < len(modellek_lista)]
            
        if not szurt_modellek:
            print("Nem választottál érvényes modellt.")
            return

        print("\n[Rendszer] Konkrétsági pontok számítása... (Fordítás folyamatban)")
        
        ai_eredmenyek = []
        ember_konkretsag_pontok = []
        
        for kerdes in kivalasztott_kerdesek:
            k_sorszam = kerdes['sorszam']
            k_oszlop_ai = f"Kerdes_{k_sorszam}"
            hivoszo = kerdes.get('hivoszo_vagy_referencia', '')
            
            if k_sorszam < len(self.ember_df.columns):
                ember_oszlop_nev = self.ember_df.columns[k_sorszam]
                for valasz in self.ember_df[ember_oszlop_nev]:
                    tisztitott_szo = self._elso_valid_szo_kinyerese(hivoszo, valasz)
                    pont = self._konkretsag_szamitasa(tisztitott_szo)
                    if not np.isnan(pont):
                        ember_konkretsag_pontok.append(pont)
            
            if k_oszlop_ai in self.ai_df.columns:
                szurt_ai_df = self.ai_df[self.ai_df['Modell_Neve'].isin(szurt_modellek)]
                for _, sor in szurt_ai_df.iterrows():
                    m_nev = sor['Modell_Neve']
                    t_ertek = str(sor['Homerseklet']).replace('.', ',')
                    tisztitott_szo = self._elso_valid_szo_kinyerese(hivoszo, sor[k_oszlop_ai])
                    
                    pont = self._konkretsag_szamitasa(tisztitott_szo)
                    if not np.isnan(pont):
                        ai_eredmenyek.append({
                            "Modell": m_nev,
                            "Temperature": t_ertek,
                            "Konkretsag": pont
                        })

        df_ai = pd.DataFrame(ai_eredmenyek)
        globalis_ember_konkretsag_atlag = np.mean(ember_konkretsag_pontok) if ember_konkretsag_pontok else np.nan

        if df_ai.empty:
            print("Hiba: Nincs ábrázolható adat!")
            return

        while True:
            print("\nCsoportosítási alapok:")
            print("[1] Temperature szerint csoportosítva")
            print("[2] AI Modell szerint csoportosítva")
            print("[0] Vissza az előző menübe")
            
            csop = input("Válassz (0-2): ").strip()
            if csop == '0': break
            
            if csop == '1':
                self._plot_aggregated(df_ai, 'Temperature', 'Konkretsag', 
                                      "Átlagos Konkrétsági Pontszámok (Temperature szerint)",
                                      referencia_vonal=globalis_ember_konkretsag_atlag, ref_nev="Emberi Átlag")
            elif csop == '2':
                self._plot_aggregated(df_ai, 'Modell', 'Konkretsag', 
                                      "Átlagos Konkrétsági Pontszámok (AI Modell szerint)",
                                      referencia_vonal=globalis_ember_konkretsag_atlag, ref_nev="Emberi Átlag")

    def _plot_aggregated(self, df, group_col, value_col, title, referencia_vonal=np.nan, ref_nev=""):
        df_clean = df.dropna(subset=[value_col])
        if df_clean.empty:
            print("\n[HIBA] Nincs elég érvényes adat a diagram kirajzolásához!")
            return

        plt.figure(figsize=(12, 6))
        
        agg_df = df_clean.groupby(group_col)[value_col].mean().reset_index()
        
        if group_col == 'Temperature':
            agg_df['sort_key'] = agg_df[group_col].str.replace(',', '.').astype(float)
            agg_df = agg_df.sort_values('sort_key').drop('sort_key', axis=1)
            
        ax = sns.barplot(data=agg_df, x=group_col, y=value_col, palette="flare")
        
        if not np.isnan(referencia_vonal):
            plt.axhline(y=referencia_vonal, color='red', linestyle='--', linewidth=2, label=f"{ref_nev} ({referencia_vonal:.2f})")
            plt.legend(fontsize=12)

        plt.title(title, fontsize=16, pad=15)
        plt.ylabel("Átlagos Konkrétsági Pont (1.0 = Absztrakt, 5.0 = Konkrét)", fontsize=12)
        plt.xlabel("Hőmérséklet (Temperature)" if group_col == 'Temperature' else "Mesterséges Intelligencia Modellek", fontsize=12)
        
        plt.ylim(1.0, 5.0)
        
        for container in ax.containers:
            ax.bar_label(container, fmt='%.3f', padding=3)

        if group_col == 'Modell':
            plt.xticks(rotation=45, ha='right')
            
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    elemzo = KonkretsagElemzo()
    elemzo.interaktiv_menu()