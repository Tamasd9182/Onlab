import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import re
import warnings

warnings.filterwarnings("ignore")

class IsmetlodesElemzo:
    def __init__(self, konfig_json="konfiguracio.json", ai_csv="ai_tisztitott_valaszok.csv", ember_csv="emberi_javitott_valaszok.csv"):
        self.konfig_json = konfig_json
        self.ai_csv = ai_csv
        self.ember_csv = ember_csv
        
        self.stop_szavak = {
            "a", "az", "egy", "és", "s", "meg", "vagy", "de", "azonban", "bár", "ha", "hogy", "mert", 
            "mivel", "amíg", "akkor", "ott", "itt", "is", "mint", "ez", "ami", "aki", "egyik", "másik", 
            "nem", "igen", "csak", "nagyon", "pedig", "hanem", "illetve", "ezért", "így", "úgy", "tehát", 
            "valamint", "olyan", "ilyen", "valami", "már", "még", "egyébként", "is", "volna", "lett", "van",
            "volt", "lesz", "vannak", "voltak", "lesznek", "kell", "lehet"
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

    def _ismetlodes_szazalek(self, szoveg):
        if pd.isna(szoveg) or str(szoveg).strip() in ["", "HIBA"]:
            return np.nan
            
        tisztitott = str(szoveg).strip().lower()
        if not tisztitott:
            return np.nan

        tisztitott = re.sub(r'[^\w\s]', '', tisztitott)
        szavak = tisztitott.split()
        
        valid_szavak = [szo for szo in szavak if szo not in self.stop_szavak and len(szo) > 1]
        
        osszes_valid = len(valid_szavak)
        if osszes_valid <= 1:
            return 0.0
            
        egyedi_szavak_szama = len(set(valid_szavak))
        ismetlodesek_szama = osszes_valid - egyedi_szavak_szama
        
        return (ismetlodesek_szama / osszes_valid) * 100

    def interaktiv_menu(self):
        print("\n" + "="*50)
        print("  CÉLZOTT DIAGRAM KÉSZÍTŐ - SZÓISMÉTLÉS MÉRŐ ")
        print("="*50)

        valasztott_teszt = "ismetlodes"

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

        print("\n[Rendszer] Szóismétlések (lexikális diverzitás) számítása...")
        
        ai_eredmenyek = []
        ember_ismetlodes_pontok = []
        
        for kerdes in kivalasztott_kerdesek:
            k_sorszam = kerdes['sorszam']
            k_oszlop_ai = f"Kerdes_{k_sorszam}"
            
            if k_sorszam < len(self.ember_df.columns):
                ember_oszlop_nev = self.ember_df.columns[k_sorszam]
                for valasz in self.ember_df[ember_oszlop_nev]:
                    pont = self._ismetlodes_szazalek(valasz)
                    if not np.isnan(pont):
                        ember_ismetlodes_pontok.append(pont)
            
            if k_oszlop_ai in self.ai_df.columns:
                szurt_ai_df = self.ai_df[self.ai_df['Modell_Neve'].isin(szurt_modellek)]
                for _, sor in szurt_ai_df.iterrows():
                    m_nev = sor['Modell_Neve']
                    t_ertek = str(sor['Homerseklet']).replace('.', ',')
                    
                    pont = self._ismetlodes_szazalek(sor[k_oszlop_ai])
                    if not np.isnan(pont):
                        ai_eredmenyek.append({
                            "Modell": m_nev,
                            "Temperature": t_ertek,
                            "Ismetlodes": pont
                        })

        df_ai = pd.DataFrame(ai_eredmenyek)
        globalis_ember_ismetlodes_atlag = np.mean(ember_ismetlodes_pontok) if ember_ismetlodes_pontok else np.nan

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
                self._plot_aggregated(df_ai, 'Temperature', 'Ismetlodes', 
                                      "Átlagos Szóismétlés Aránya (Temperature szerint)",
                                      referencia_vonal=globalis_ember_ismetlodes_atlag, ref_nev="Emberi Átlag")
            elif csop == '2':
                self._plot_aggregated(df_ai, 'Modell', 'Ismetlodes', 
                                      "Átlagos Szóismétlés Aránya (AI Modell szerint)",
                                      referencia_vonal=globalis_ember_ismetlodes_atlag, ref_nev="Emberi Átlag")

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
            
        ax = sns.barplot(data=agg_df, x=group_col, y=value_col, palette="rocket")
        
        if not np.isnan(referencia_vonal):
            plt.axhline(y=referencia_vonal, color='red', linestyle='--', linewidth=2, label=f"{ref_nev} ({referencia_vonal:.2f}%)")
            plt.legend(fontsize=12)

        plt.title(title, fontsize=16, pad=15)
        plt.ylabel("Átlagos Szóismétlés Aránya (%)", fontsize=12)
        plt.xlabel("Hőmérséklet (Temperature)" if group_col == 'Temperature' else "Mesterséges Intelligencia Modellek", fontsize=12)
        
        plt.ylim(0, max(agg_df[value_col].max() * 1.2, 5.0))
        
        for container in ax.containers:
            ax.bar_label(container, fmt='%.2f%%', padding=3)

        if group_col == 'Modell':
            plt.xticks(rotation=45, ha='right')
            
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    elemzo = IsmetlodesElemzo()
    elemzo.interaktiv_menu()