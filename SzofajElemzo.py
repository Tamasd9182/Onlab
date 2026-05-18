import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import huspacy
import warnings

warnings.filterwarnings("ignore")

class SzofajElemzo:
    def __init__(self, konfig_json="konfiguracio.json", ai_csv="ai_tisztitott_valaszok.csv", ember_csv="emberi_javitott_valaszok.csv"):
        self.konfig_json = konfig_json
        self.ai_csv = ai_csv
        self.ember_csv = ember_csv
        
        print("[Rendszer] Huspacy magyar nyelvi modell betöltése (ez eltarthat pár másodpercig)...")
        try:
            self.nlp = huspacy.load()
        except Exception as e:
            print(f"[Kritikus Hiba] A Huspacy modell nem tölthető be! Futtasd a terminálban: python -m huspacy download hu_core_news_lg\nRészletek: {e}")
            self.nlp = None

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

    def _szofaj_szazalekok(self, szoveg):
        if not self.nlp or pd.isna(szoveg) or str(szoveg).strip() in ["", "HIBA"]:
            return None
            
        tisztitott = str(szoveg).strip()
        if not tisztitott:
            return None

        try:
            doc = self.nlp(tisztitott)
            
            valodi_szavak = [t for t in doc if not t.is_punct and not t.is_space]
            osszes_szo = len(valodi_szavak)
            
            if osszes_szo == 0:
                return None
                
            igek = sum(1 for t in valodi_szavak if t.pos_ == "VERB")
            fonevek = sum(1 for t in valodi_szavak if t.pos_ == "NOUN")
            melleknevek = sum(1 for t in valodi_szavak if t.pos_ == "ADJ")
            
            return {
                "Ige": (igek / osszes_szo) * 100,
                "Főnév": (fonevek / osszes_szo) * 100,
                "Melléknév": (melleknevek / osszes_szo) * 100
            }
        except Exception:
            return None

    def interaktiv_menu(self):
        if not self.nlp:
            return

        print("\n" + "="*50)
        print("  CÉLZOTT DIAGRAM KÉSZÍTŐ - SZÓFAJELEMZÉS  ")
        print("="*50)

        valasztott_teszt = "szofaj_elemzes"

        elerheto_kerdesek = [k for k in self.kerdesek if valasztott_teszt in k.get("futtatando_tesztek", [])]
        
        if not elerheto_kerdesek:
            print(f"Nincs olyan kérdés, amire a(z) '{valasztott_teszt}' whitespace lenne.")
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

        print("\n[Rendszer] Szófajok elemzése folyamatban... (Ez eltarthat egy kis ideig!)")
        
        vegleges_adatok = []
        feldolgozott_elemek = 0
        
        for kerdes in kivalasztott_kerdesek:
            k_sorszam = kerdes['sorszam']
            k_oszlop_ai = f"Kerdes_{k_sorszam}"
            
            if k_sorszam < len(self.ember_df.columns):
                ember_oszlop_nev = self.ember_df.columns[k_sorszam]
                for valasz in self.ember_df[ember_oszlop_nev]:
                    szazalekok = self._szofaj_szazalekok(valasz)
                    if szazalekok:
                        for szofaj, ertek in szazalekok.items():
                            vegleges_adatok.append({
                                "Csoport_Temp": "Ember (Kontroll)",
                                "Csoport_Modell": "Ember (Kontroll)",
                                "Szofaj": szofaj,
                                "Szazalek": ertek
                            })
                        feldolgozott_elemek += 1
                        if feldolgozott_elemek % 20 == 0:
                            print(f"  -> Feldolgozva: {feldolgozott_elemek} válasz...")

            if k_oszlop_ai in self.ai_df.columns:
                szurt_ai_df = self.ai_df[self.ai_df['Modell_Neve'].isin(szurt_modellek)]
                for _, sor in szurt_ai_df.iterrows():
                    m_nev = sor['Modell_Neve']
                    t_ertek = str(sor['Homerseklet']).replace('.', ',')
                    
                    szazalekok = self._szofaj_szazalekok(sor[k_oszlop_ai])
                    if szazalekok:
                        for szofaj, ertek in szazalekok.items():
                            vegleges_adatok.append({
                                "Csoport_Temp": f"T={t_ertek}",
                                "Csoport_Modell": m_nev,
                                "Szofaj": szofaj,
                                "Szazalek": ertek
                            })
                        feldolgozott_elemek += 1
                        if feldolgozott_elemek % 20 == 0:
                            print(f"  -> Feldolgozva: {feldolgozott_elemek} válasz...")

        df_szofaj = pd.DataFrame(vegleges_adatok)
        
        if df_szofaj.empty:
            print("Hiba: Nincs ábrázolható adat!")
            return
            
        print(f"\n[Rendszer] Feldolgozás befejeződött. ({feldolgozott_elemek} válasz elemezve)")

        while True:
            print("\nCsoportosítási alapok (Mihez viszonyítsuk az Embert?):")
            print("[1] Temperature szerint csoportosítva")
            print("[2] AI Modell szerint csoportosítva")
            print("[0] Vissza az előző menübe")
            
            csop = input("Válassz (0-2): ").strip()
            if csop == '0': break
            
            csoport_oszlop = 'Csoport_Temp' if csop == '1' else 'Csoport_Modell'
            self._plot_bar_chart(df_szofaj, csoport_oszlop)

    def _plot_bar_chart(self, df, group_col):
        agg_df = df.groupby([group_col, 'Szofaj'])['Szazalek'].mean().reset_index()

        egyedi_csoportok = sorted(agg_df[group_col].unique())
        if "Ember (Kontroll)" in egyedi_csoportok:
            egyedi_csoportok.remove("Ember (Kontroll)")
            if group_col == 'Csoport_Temp':
                egyedi_csoportok = sorted(egyedi_csoportok, key=lambda x: float(x.replace('T=', '').replace(',', '.')))
            egyedi_csoportok = ["Ember (Kontroll)"] + egyedi_csoportok

        szofajok = ["Ige", "Főnév", "Melléknév"]
        szofaj_szinek = {"Ige": "Blues_d", "Főnév": "Greens_d", "Melléknév": "Oranges_d"}
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)

        for i, szofaj in enumerate(szofajok):
            ax = axes[i]
            szelet = agg_df[agg_df['Szofaj'] == szofaj]
            
            szelet['sorrend'] = pd.Categorical(szelet[group_col], categories=egyedi_csoportok, ordered=True)
            szelet = szelet.sort_values('sorrend')

            sns.barplot(data=szelet, x=group_col, y='Szazalek', ax=ax, palette=szofaj_szinek[szofaj])
            
            ax.set_title(f"{szofaj.upper()} aránya", fontsize=14, fontweight='bold')
            ax.set_ylabel("Arány a teljes szövegben (%)" if i == 0 else "")
            ax.set_xlabel("")
            
            ax.tick_params(axis='x', rotation=45, labelsize=10)

            for container in ax.containers:
                ax.bar_label(container, fmt='%.1f%%', padding=3, fontsize=9)

        max_val = agg_df['Szazalek'].max()
        axes[0].set_ylim(0, max_val * 1.15)

        fig.suptitle("Szófajok Átlagos Százalékos Aránya Csoportonként", fontsize=16, y=1.02)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    elemzo = SzofajElemzo()
    elemzo.interaktiv_menu()