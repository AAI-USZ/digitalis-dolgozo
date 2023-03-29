# Digitális dolgozó

Az src mappa tartalma:
 - **NER-base.py**: Named Entity Recognition példa kód betöltéssel és kimenettel angol nyelvre- NER-base.py: Named Entity Recognition példa kód betöltéssel és kimenettel angol nyelvre
 - **NER-hu-base.py**: Named Entity Recognition példa kód betöltéssel és kimenettel magyar nyelvre  Az előretanított modellek a következő entitásokat ismerik fel:
   - O - Outside of a named entity 
   - B-MIS - Beginning of a miscellaneous entity right  after another miscellaneous entity
   - I-MIS	- Miscellaneous entity
   - B-PER	- Beginning of a person’s name right after another person’s name
   - I-PER	- Person’s name
   - B-ORG	- Beginning of an organization right after another organization
   - I-ORG	- organization
   - B-LOC	- Beginning of a location right after another location
    - I-LOC	- Location


 - **NER_results_body.txt**: az issue-k szövegtörzsére lefuttatott entity kinyerés eredménye
 - **NER_results_title.txt**: az issue-k cím szövegére lefuttatott entity kinyerés eredménye
 - **data/commits/**: GitHub API segítségével commit információk letöltése megadott kód repository-kból
 - **data/issues/**: GitHub API segítségével issue szöveg letöltése megadott kód repository-ból
 - **env/**: Docker környezethez szükséges fájlok
   - build.bat: docker konténer elkészítése (ennek futtatásához szükséges internet kapcsolat)
   - start_bash.bat: bash nyitása a konténeren belül, itt a `python NER-base.py` parancs kiadásával indíthatjuk a modellt, melynek kimenete a konténeren kívül a data mappában is megtalálható lesz.