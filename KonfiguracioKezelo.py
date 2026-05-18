import json

class KonfiguracioKezelo:
    """
    Ez az osztály felel a konfigurációs (JSON) fájl beolvasásáért és kezeléséért.
    A többi osztály rajta keresztül fér hozzá a beállításokhoz.
    """
    def __init__(self, fajlnev='konfiguracio.json'):
        self.fajlnev = fajlnev
        self.beallitasok = {}
        self.konfiguracioBetoltese()

    def konfiguracioBetoltese(self):
        """Betölti a JSON fájlt egy memóriában tárolt szótárba."""
        try:
            with open(self.fajlnev, 'r', encoding='utf-8') as fajl:
                self.beallitasok = json.load(fajl)
            print("Konfiguráció sikeresen betöltve!")
        except FileNotFoundError:
            print(f"\n[KRITIKUS HIBA] A '{self.fajlnev}' nem található!")
            print("Kérlek, győződj meg róla, hogy a fájl abban a mappában van, ahonnan a Main.py-t indítod.")
            self.beallitasok = {}
        except json.JSONDecodeError as e:
            print(f"\n[KRITIKUS HIBA] A '{self.fajlnev}' fájl formátuma hibás (Pl. hiányzó vessző vagy idézőjel)!")
            print(f"Részletek: {e}")
            self.beallitasok = {}

    def ertekLekerese(self, fokulcs, alkulcs=None):
        """
        Visszaad egy értéket a konfigurációból. 
        Példák a használatra:
        ertekLekerese("ai_beallitasok") -> Visszaadja az egész beállítás blokkot
        ertekLekerese("api_kulcsok", "gemini") -> Visszaadja konkrétan az API kulcsot
        """
        if fokulcs in self.beallitasok:
            if alkulcs:
                return self.beallitasok[fokulcs].get(alkulcs)
            return self.beallitasok[fokulcs]
        
        print(f"[FIGYELMEZTETÉS] A(z) '{fokulcs}' kulcs nem található a konfigurációban.")
        return None

    def kerdesekLekerese(self):
        """Visszaadja a kérdések teljes listáját a JSON-ből."""
        kerdesek = self.beallitasok.get("kerdesek", [])
        if not kerdesek:
            print("[FIGYELMEZTETÉS] Nincsenek definiált kérdések a konfigurációban!")
        return kerdesek

    def apiKulcsLekerese(self, modell_csalad="gemini"):
        """Kényelmi függvény az API kulcs gyors lekérésére."""
        return self.ertekLekerese("api_kulcsok", modell_csalad)