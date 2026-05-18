import pandas as pd
from deep_translator import GoogleTranslator
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import huspacy
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

class NyelviElemzo:
    def __init__(self):
        self.fordito_modell = GoogleTranslator(source='hu', target='en')
        self.sentence_transformer_modell = None
        self.erzelem_modell = None
        self.huspacy_modell = None
        
        self.brysbaert_szotar = {}
        self.brysbaert_betoltve = False

    def transformerBetoltese(self):
        if self.sentence_transformer_modell is None:
            print("[Rendszer] SentenceTransformer (Távolságmérés) betöltése...")
            self.sentence_transformer_modell = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

    def erzelemModellBetoltese(self):
        if self.erzelem_modell is None:
            print("[Rendszer] GoEmotions modell (Érzelemelemzés) betöltése...")
            self.erzelem_modell = pipeline("text-classification", model="monologg/bert-base-cased-goemotions-original", top_k=None)

    def huspacyBetoltese(self):
        if self.huspacy_modell is None:
            print("[Rendszer] Huspacy modell (Szófajelemzés) betöltése...")
            try:
                self.huspacy_modell = huspacy.load()
            except Exception as e:
                print(f"[HIBA] Huspacy betöltési hiba! Terminál parancs: 'python -m huspacy download hu_core_news_lg'. Bővebben: {e}")

    def brysbaertBetoltese(self):
        if not self.brysbaert_betoltve:
            print("[Rendszer] Brysbaert Excel tábla (Konkrétságmérés) betöltése...")
            try:
                df = pd.read_excel('Concreteness_ratings_Brysbaert.xlsx')
                for index, sor in df.iterrows():
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

    def magyarrolAngolraForditas(self, magyar_szoveg):
        try:
            return self.fordito_modell.translate(magyar_szoveg)
        except Exception as e:
            print(f"Fordítási hiba: {e}")
            return ""

    def ketSzoHasonlosaga(self, szo1, szo2):
        if not szo1 or not szo2 or szo1 == "HIBA":
            return 0.0

        self.transformerBetoltese()
        
        try:
            vektor1 = self.sentence_transformer_modell.encode([szo1])
            vektor2 = self.sentence_transformer_modell.encode([szo2])
            
            hasonlosag_matrix = cosine_similarity(vektor1, vektor2)
            pontszam = hasonlosag_matrix[0][0]
            return float(pontszam)
        except Exception as e:
            print(f"Hiba a távolságmérésnél: {e}")
            return 0.0

    def erzelemElemzes(self, magyar_mondat):
        if not magyar_mondat or magyar_mondat == "HIBA":
            return "nincs_adat"

        self.erzelemModellBetoltese()
        angol_forditas = self.magyarrolAngolraForditas(magyar_mondat)
        
        ERZELEM_MAGYARUL = {
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

        try:
            eredmenyek = self.erzelem_modell(angol_forditas)[0]
            legjobb_pontszam = 0.0
            legjobb_erzelem_cimke = "neutral"
            
            for eredmeny in eredmenyek:
                if eredmeny['score'] > legjobb_pontszam:
                    legjobb_pontszam = eredmeny['score']
                    legjobb_erzelem_cimke = eredmeny['label']
            
            magyar_cimke = ERZELEM_MAGYARUL.get(legjobb_erzelem_cimke, legjobb_erzelem_cimke)
            return f"{magyar_cimke} ({round(legjobb_pontszam * 100, 1)}%)"
            
        except Exception as e:
            print(f"Hiba az érzelemelemzésnél: {e}")
            return "hiba"

    def szofajElemzes(self, magyar_mondat):
        if not magyar_mondat or magyar_mondat == "HIBA":
            return "0 ige, 0 fn, 0 mn"
            
        self.huspacyBetoltese()
        
        ige, fonev, melleknev = 0, 0, 0
        
        try:
            doc = self.huspacy_modell(magyar_mondat)
            for token in doc:
                if token.pos_ == "VERB":
                    ige += 1
                elif token.pos_ == "NOUN":
                    fonev += 1
                elif token.pos_ == "ADJ":
                    melleknev += 1
                    
            return f"{ige} ige, {fonev} fn, {melleknev} mn"
        except Exception as e:
            print(f"Hiba a szófajelemzésnél: {e}")
            return "hiba"

    def konkretsagiTeszt(self, magyar_mondat):
        if not magyar_mondat or magyar_mondat == "HIBA":
            return 0.0

        self.brysbaertBetoltese()
        if not self.brysbaert_betoltve:
            return 0.0
            
        angol_szoveg = self.magyarrolAngolraForditas(magyar_mondat).lower()
        szavak = angol_szoveg.replace('.', '').replace(',', '').replace('?', '').split()
        
        sulyozott_pontok = 0.0
        sulyok_osszege = 0.0
        stop_szavak = {"a", "an", "the", "and", "but", "or", "because", "is", "am", "are", "was", "were", "to", "of", "in", "it", "i", "you", "he", "she"}
        
        try:
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
                return round(sulyozott_pontok / sulyok_osszege, 2)
            else:
                return 0.0
        except Exception as e:
            print(f"Hiba a konkrétság tesztnél: {e}")
            return 0.0