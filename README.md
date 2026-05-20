Készítette: Mészáros Tamás
Kurzus: Önálló laboratóriumi gyakorlat

Leírás
Ez a kutatási projekt a mesterséges és természetes intelligencia határterületét vizsgálja, különös tekintettel az asszociációs képességekre. A vizsgálat során összehasonlítjuk az emberi válaszadók és a legmodernebb nagy nyelvi modellek (LLM) kognitív mintázatait különböző szemantikai, érzelmi és morfológiai metrikák mentén.

Telepítés és konfiguráció
A program futtatásához a gyökérkönyvtárban az alábbi két fájl konfigurálása szükséges:

    1. konfiguracio.json
    Ebben a fájlban tároljuk az API-hozzáféréseket. A fájlban a "kulcs" mezőket az alábbiak szerint kell kitölteni:
    
    Gemini API: A Google AI Studio-ból származó érvényes API kulcs.
    
    OpenAI API: Az OpenAI platformról származó API kulcs.
    
    2. credentials.json
    Ez a fájl a Google Sheets API-val való kommunikációhoz szükséges hitelesítési adatokat tartalmazza. Ezt a fájlt a Google Cloud Console-ból töltheted le egy Service Account létrehozását követően.
    
    Tartalma: A fájl a szolgáltatási fiók hitelesítő adatait tartalmazza (többek között: client_email, private_key, project_id), amelyek lehetővé teszik a program számára a táblázatkezelő fájlok írását és olvasását biztonságos, jelszó nélküli szerver-szerver kapcsolaton keresztül.

Fontosabb fájlok és könyvtárak
Main.py: A teljes kutatási folyamatot vezérlő főszkript.
requirements.txt: A futtatáshoz szükséges Python-könyvtárak jegyzéke.

Eredmenyek mappa: Taratlmazza a kutatás összes generálható diagramját egyéni kiértékelés céljából.
Program szerkezet mappa: Taratlmazza a program menüszerkezetét.
