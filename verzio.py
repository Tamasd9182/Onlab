import importlib.metadata

csomagok = [
    "pandas", "numpy", "matplotlib", "seaborn", "deep-translator", 
    "transformers", "sentence-transformers", "scikit-learn", "scipy", 
    "huspacy", "openai", "google-genai", "openpyxl", "pillow"
]

print("="*45)
print("   A PROJEKTBEN HASZNÁLT CSOMAGOK VERZIÓI")
print("="*45)

for csomag in csomagok:
    try:
        verzio = importlib.metadata.version(csomag)
        print(f"{csomag:<25} : v{verzio}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{csomag:<25} : Nincs telepítve ebben a környezetben")