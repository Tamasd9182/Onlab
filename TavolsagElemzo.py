import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import warnings

warnings.filterwarnings("ignore")

class TavolsagElemzo:
    def __init__(self, konfig_json="konfiguracio.json", ai_csv="ai_tisztitott_valaszok.csv", ember_csv="emberi_javitott_valaszok.csv"):
        self.konfig_json = konfig_json
        self.ai_csv = ai_csv
        self.ember_csv = ember_csv
        
        print("[Rendszer] Nyelvi modell betöltése (ez eltarthat pár másodpercig)...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
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

    def _vektorizal_es_tavolsagot_mer(self, cel_szo, referencia_vektor):
        if not cel_szo or cel_szo == "HIBA":
            return np.nan, None
            
        try:
            tisztitott_szo = str(cel_szo).strip(".,!?\"' \n").lower()
            if not tisztitott_szo:
                return np.nan, None
                
            vektor = self.model.encode(tisztitott_szo)
            tavolsag = cosine(referencia_vektor, vektor) if referencia_vektor is not None else np.nan
            return tavolsag, vektor
        except Exception:
            return np.nan, None

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

    def interaktiv_menu(self):
        print("\n" + "="*50)
        print("  CÉLZOTT DIAGRAM KÉSZÍTŐ ÉS TÁVOLSÁGELEMZŐ  ")
        print("="*50)

        valasztott_teszt = "tavolsag"

        elerheto_kerdesek = [k for k in self.kerdesek if valasztott_teszt in k.get("futtatando_tesztek", []) and k.get('hivoszo_vagy_referencia') != 'nincs']
        
        if not elerheto_kerdesek:
            print(f"Nincs olyan kérdés hívószóval, amire a(z) '{valasztott_teszt}' futtatható lenne.")
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

        print("\n[Rendszer] Vektorok és Távolságok számolása...")
        
        ai_eredmenyek = []
        ember_atlagok_celhoz = []
        
        for kerdes in kivalasztott_kerdesek:
            k_sorszam = kerdes['sorszam']
            k_oszlop_ai = f"Kerdes_{k_sorszam}"
            hivoszo = kerdes['hivoszo_vagy_referencia']
            hivo_vec = self.model.encode(hivoszo.lower())

            ember_vektorok = []
            ember_tavolsag_celhoz = []
            
            if k_sorszam < len(self.ember_df.columns):
                ember_oszlop_nev = self.ember_df.columns[k_sorszam]
                for valasz in self.ember_df[ember_oszlop_nev]:
                    tisztitott_szo = self._elso_valid_szo_kinyerese(hivoszo, valasz)
                    tav, vec = self._vektorizal_es_tavolsagot_mer(tisztitott_szo, hivo_vec)
                    if vec is not None:
                        ember_vektorok.append(vec)
                        ember_tavolsag_celhoz.append(tav)
            
            atlag_ember_cel_tav = np.mean(ember_tavolsag_celhoz) if ember_tavolsag_celhoz else np.nan
            atlag_ember_vektor = np.mean(ember_vektorok, axis=0) if ember_vektorok else None
            
            if not np.isnan(atlag_ember_cel_tav):
                ember_atlagok_celhoz.append(atlag_ember_cel_tav)

            if k_oszlop_ai in self.ai_df.columns:
                szurt_ai_df = self.ai_df[self.ai_df['Modell_Neve'].isin(szurt_modellek)]
                for _, sor in szurt_ai_df.iterrows():
                    m_nev = sor['Modell_Neve']
                    t_ertek = str(sor['Homerseklet']).replace('.', ',')
                    tisztitott_szo = self._elso_valid_szo_kinyerese(hivoszo, sor[k_oszlop_ai])
                    
                    tav_celhoz, vec = self._vektorizal_es_tavolsagot_mer(tisztitott_szo, hivo_vec)
                    
                    if vec is not None:
                        tav_embertol = cosine(atlag_ember_vektor, vec) if atlag_ember_vektor is not None else np.nan
                        
                        ai_eredmenyek.append({
                            "Modell": m_nev,
                            "Temperature": t_ertek,
                            "Tavolsag_Celhoz": tav_celhoz,
                            "Tavolsag_Embertol": tav_embertol
                        })

        df_ai = pd.DataFrame(ai_eredmenyek)
        globalis_ember_cel_atlag = np.mean(ember_atlagok_celhoz) if ember_atlagok_celhoz else np.nan

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
                print("\n Diagramok Temperature alapján:")
                print(" A - Távolság a célszótól (AI átlag vs Ember átlag)")
                print(" B - Távolság az AI és az Emberi válaszok között")
                
                d_valasz = input("Melyiket kéred? (A/B): ").strip().upper()
                if d_valasz == 'A':
                    self._plot_aggregated(df_ai, 'Temperature', 'Tavolsag_Celhoz', 
                                          "Átlagos távolság a célszótól (Temperature szerint)",
                                          referencia_vonal=globalis_ember_cel_atlag, ref_nev="Emberi Válaszok Átlaga")
                elif d_valasz == 'B':
                    self._plot_aggregated(df_ai, 'Temperature', 'Tavolsag_Embertol', 
                                          "AI átlagos távolsága az Emberi válaszoktól (Temperature szerint)")
            
            elif csop == '2':
                print("\n Diagramok AI Modell alapján:")
                print(" A - Távolság a célszótól (AI átlag vs Ember átlag)")
                print(" B - Távolság az AI és az Emberi válaszok között")
                
                d_valasz = input("Melyiket kéred? (A/B): ").strip().upper()
                if d_valasz == 'A':
                    self._plot_aggregated(df_ai, 'Modell', 'Tavolsag_Celhoz', 
                                          "Átlagos távolság a célszótól (AI Modell szerint)",
                                          referencia_vonal=globalis_ember_cel_atlag, ref_nev="Emberi Válaszok Átlaga")
                elif d_valasz == 'B':
                    self._plot_aggregated(df_ai, 'Modell', 'Tavolsag_Embertol', 
                                          "AI átlagos távolsága az Emberi válaszoktól (AI Modell szerint)")

    def _plot_aggregated(self, df, group_col, value_col, title, referencia_vonal=np.nan, ref_nev=""):
        df_clean = df.dropna(subset=[value_col])
        if df_clean.empty:
            print("\n[HIBA] Nincs elég érvényes adat (vagy hiányzik a humán kontroll) a diagram kirajzolásához!")
            return

        plt.figure(figsize=(12, 6))
        
        agg_df = df_clean.groupby(group_col)[value_col].mean().reset_index()
        
        if group_col == 'Temperature':
            agg_df['sort_key'] = agg_df[group_col].str.replace(',', '.').astype(float)
            agg_df = agg_df.sort_values('sort_key').drop('sort_key', axis=1)
            
        ax = sns.barplot(data=agg_df, x=group_col, y=value_col, palette="mako")
        
        if not np.isnan(referencia_vonal):
            plt.axhline(y=referencia_vonal, color='red', linestyle='--', linewidth=2, label=f"{ref_nev} ({referencia_vonal:.2f})")
            plt.legend(fontsize=12)

        plt.title(title, fontsize=16, pad=15)
        plt.ylabel("Koszinusz Távolság (0.0 = azonos, 1.0 = távoli)", fontsize=12)
        plt.xlabel("Hőmérséklet (Temperature)" if group_col == 'Temperature' else "Mesterséges Intelligencia Modellek", fontsize=12)
        
        for container in ax.containers:
            ax.bar_label(container, fmt='%.3f', padding=3)

        if group_col == 'Modell':
            plt.xticks(rotation=45, ha='right')
            
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    elemzo = TavolsagElemzo()
    elemzo.interaktiv_menu()