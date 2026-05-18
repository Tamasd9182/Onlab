import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from deep_translator import GoogleTranslator
from transformers import pipeline
import warnings

warnings.filterwarnings("ignore")

class ErzelemElemzo:
    def __init__(self, konfig_json="konfiguracio.json", ai_csv="ai_tisztitott_valaszok.csv", ember_csv="emberi_javitott_valaszok.csv"):
        self.konfig_json = konfig_json
        self.ai_csv = ai_csv
        self.ember_csv = ember_csv
        
        self.fordito = GoogleTranslator(source='hu', target='en')
        print("[Rendszer] GoEmotions modell betöltése...")
        self.erzelem_modell = pipeline("text-classification", model="monologg/bert-base-cased-goemotions-original", top_k=None)
        
        self.erzelem_magyarul = {
            "admiration": "csodálat", "amusement": "szórakozás", "anger": "harag", 
            "annoyance": "bosszankodás", "approval": "jóváhagyás", "caring": "törődés", 
            "confusion": "zavarodottság", "curiosity": "kíváncsiság", "desire": "vágy", 
            "disappointment": "csalódottság", "disapproval": "helytelenítés", "disgust": "undor",
            "embarrassment": "szégyen", "excitement": "izgalom", "fear": "félelem", 
            "gratitude": "hála", "grief": "gyász", "joy": "öröm", "love": "szeretet", 
            "nervousness": "idegesség", "optimism": "optimizmus", "pride": "büszkeség", 
            "realization": "felismerés", "relief": "megkönnyebbülés", "remorse": "bűntudat", 
            "sadness": "szomorúság", "surprise": "meglepetés", "neutral": "semleges"
        }
        
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

    def _dominans_erzelem(self, szoveg):
        if pd.isna(szoveg) or str(szoveg).strip() in ["", "HIBA"]:
            return None
        try:
            angol = self.fordito.translate(str(szoveg)).lower()
            eredmenyek = self.erzelem_modell(angol)[0]
            legjobb_pont = -1.0
            legjobb_cimke = "neutral"
            for e in eredmenyek:
                if e['score'] > legjobb_pont:
                    legjobb_pont = e['score']
                    legjobb_cimke = e['label']
            return self.erzelem_magyarul.get(legjobb_cimke, legjobb_cimke)
        except Exception:
            return None

    def interaktiv_menu(self):
        print("\n" + "="*50)
        print("  CÉLZOTT DIAGRAM KÉSZÍTŐ - ÉRZELEMELEMZÉS  ")
        print("="*50)
        
        valasztott_teszt = "erzelem"
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

        print("\n[Rendszer] Érzelmek elemzése folyamatban...")
        
        nyers_adatok = []
        
        for kerdes in kivalasztott_kerdesek:
            k_sorszam = kerdes['sorszam']
            k_oszlop_ai = f"Kerdes_{k_sorszam}"
            
            if k_sorszam < len(self.ember_df.columns):
                ember_oszlop_nev = self.ember_df.columns[k_sorszam]
                for valasz in self.ember_df[ember_oszlop_nev]:
                    erz = self._dominans_erzelem(valasz)
                    if erz:
                        nyers_adatok.append({
                            "Csoport_Temp": "Ember (Kontroll)",
                            "Csoport_Modell": "Ember (Kontroll)",
                            "Erzelem": erz
                        })
            
            if k_oszlop_ai in self.ai_df.columns:
                szurt_ai_df = self.ai_df[self.ai_df['Modell_Neve'].isin(szurt_modellek)]
                for _, sor in szurt_ai_df.iterrows():
                    m_nev = sor['Modell_Neve']
                    t_ertek = str(sor['Homerseklet']).replace('.', ',')
                    erz = self._dominans_erzelem(sor[k_oszlop_ai])
                    if erz:
                        nyers_adatok.append({
                            "Csoport_Temp": f"T={t_ertek}",
                            "Csoport_Modell": m_nev,
                            "Erzelem": erz
                        })

        df_nyers = pd.DataFrame(nyers_adatok)
        if df_nyers.empty:
            print("Hiba: Nincs ábrázolható adat!")
            return

        while True:
            print("\nCsoportosítási alapok:")
            print("[1] Temperature szerint csoportosítva")
            print("[2] AI Modell szerint csoportosítva")
            print("[0] Vissza az előző menübe")
            
            csop = input("Válassz (0-2): ").strip()
            if csop == '0': break
            
            if csop in ['1', '2']:
                csoport_oszlop = 'Csoport_Temp' if csop == '1' else 'Csoport_Modell'
                
                print("\nModern ábrázolási formátumok:")
                print("[A] Összehasonlító Hőtérkép")
                print("[B] Halmozott Oszlopdiagram")
                fmt = input("Válassz formátumot (A/B): ").strip().upper()
                
                df_szazalek = df_nyers.groupby([csoport_oszlop, 'Erzelem']).size().unstack(fill_value=0)
                df_szazalek = df_szazalek.div(df_szazalek.sum(axis=1), axis=0) * 100
                df_szazalek = df_szazalek.reset_index().melt(id_vars=csoport_oszlop, value_name='Szazalek')
                
                if fmt == 'A':
                    self._plot_hoterkep(df_szazalek, csoport_oszlop)
                elif fmt == 'B':
                    self._plot_halmozott_oszlop(df_szazalek, csoport_oszlop)

    def _plot_hoterkep(self, df, group_col):
        pivot_df = df.pivot_table(index='Erzelem', columns=group_col, values='Szazalek', aggfunc='mean').fillna(0)
        if group_col == 'Csoport_Temp':
            egyedi_elemek = list(pivot_df.columns)
            if "Ember (Kontroll)" in egyedi_elemek:
                egyedi_elemek.remove("Ember (Kontroll)")
                egyedi_elemek = sorted(egyedi_elemek, key=lambda x: float(x.replace('T=', '').replace(',', '.')))
                pivot_df = pivot_df[["Ember (Kontroll)"] + egyedi_elemek]
        else:
            egyedi_elemek = list(pivot_df.columns)
            if "Ember (Kontroll)" in egyedi_elemek:
                egyedi_elemek.remove("Ember (Kontroll)")
                pivot_df = pivot_df[["Ember (Kontroll)"] + sorted(egyedi_elemek)]
        
        plt.figure(figsize=(12, 9))
        sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': 'Előfordulási arány (%)'}, linewidths=.5)
        plt.title("Érzelmi profilok összehasonlító hőtérképe (%)", fontsize=14, fontweight='bold', pad=15)
        plt.xlabel("Hőmérséklet (Temperature)" if group_col == 'Csoport_Temp' else "Mesterséges Intelligencia Modellek", fontsize=11)
        plt.ylabel("Érzelmi kategóriák", fontsize=11)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def _plot_halmozott_oszlop(self, df, group_col):
        pivot_df = df.pivot_table(index=group_col, columns='Erzelem', values='Szazalek', aggfunc='mean').fillna(0)
        egyedi_elemek = list(pivot_df.index)
        if "Ember (Kontroll)" in egyedi_elemek:
            egyedi_elemek.remove("Ember (Kontroll)")
            if group_col == 'Csoport_Temp':
                egyedi_elemek = sorted(egyedi_elemek, key=lambda x: float(x.replace('T=', '').replace(',', '.')))
            pivot_df = pivot_df.reindex(["Ember (Kontroll)"] + egyedi_elemek)
        
        pivot_df.plot(kind='bar', stacked=True, figsize=(13, 7), cmap='tab20')
        plt.title("Összesített érzelmi profilok megoszlása csoportonként", fontsize=14, fontweight='bold', pad=15)
        plt.ylabel("Relatív gyakoriság (%)", fontsize=11)
        plt.xlabel("Hőmérséklet (Temperature)" if group_col == 'Csoport_Temp' else "Mesterséges Intelligencia Modellek", fontsize=11)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title="Érzelmi kategóriák", bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, ncol=1, fontsize=10)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    elemzo = ErzelemElemzo()
    elemzo.interaktiv_menu()