# Facebook Bejegyzés Importáló

Ez a projekt a Facebook oldalak bejegyzéseinek automatikus importálását teszi lehetővé Jekyll weboldalakhoz. A program a Facebook Graph API segítségével letölti a megadott oldal legutóbbi bejegyzéseit, majd Jekyll formátumú Markdown fájlokká alakítja azokat.

## Funkciók

- Facebook oldal bejegyzéseinek letöltése
- Bejegyzésekhez tartozó képek automatikus feldolgozása
- Jekyll-kompatibilis Markdown fájlok generálása
- Kétnyelvű (magyar/szlovák) tartalom kezelése
- Duplikált képek kiszűrése

## Telepítés

Klónozd a repozitóriumot:

```bash
git clone https://github.com/huser123/Facebook_post_to_Jekyll_MD.git
cd Facebook_post_to_Jekyll_MD
```

Telepítsd a szükséges függőségeket:

```bash
pip install requests pyyaml
```

## Használat

### 1. Felhasználói token konvertálása oldal tokenné

Először a felhasználói tokent át kell alakítani oldal tokenné a következő szkript használatával:

```bash
python user_key_to_page_key.py
```

Írjuk be a felhasználói tokent a szkriptben, vagy adjuk meg futtatáskor. A program kilistázza az elérhető oldalakat, és automatikusan generálja az oldal tokent.

### 2. Bejegyzések importálása

A generált oldal tokennel és oldal azonosítóval futtathatjuk a fő importáló szkriptet:

```bash
python fb_import.py -t "OLDAL_TOKEN" -p "OLDAL_ID" -n 5
```

Paraméterek:
- `-t`, `--token`: Facebook API token (Page Access Token)
- `-p`, `--page`: Facebook oldal azonosítója
- `-o`, `--output`: Kimeneti mappa (alapértelmezett: "FB_MD")
- `-n`, `--number`: Importálandó bejegyzések száma
- `-d`, `--debug`: Részletes debug információk

Ha nem adunk meg paramétert a bejegyzések számához, a program interaktívan kéri be.

## Működési elv

1. A program ellenőrzi a megadott token érvényességét
2. Lekéri a megadott számú legutóbbi bejegyzést a Facebook oldalról
3. Kinyeri a bejegyzésekben található szöveget, képeket és metaadatokat
4. Létrehoz Jekyll-kompatibilis Markdown fájlokat a FB_MD/_c-sk-facebook mappában
5. Az első képet borítóképként állítja be, a többit galériában jeleníti meg

## Kimeneti formátum

A generált fájlok a következő formátumban készülnek:

```markdown
---
layout: fb-post
title: Príspevok / Bejegyzés - 2023.01.01
date: 2023-01-01 12:00:00
categories: [facebook]
image: https://url-to-cover-image.jpg
fb_url: https://facebook.com/post-url
display_date: 2023.01.01 12:00
gallery:
  - https://url-to-image1.jpg
  - https://url-to-image2.jpg
---

A bejegyzés szövege...

<div class="fb-post-info">
 <p><i class="fab fa-facebook"></i> <a href="https://facebook.com/post-url" target="_blank">Zobraziť na Facebooku / Megtekintés a Facebookon</a></p>
</div>
```

## Licenc

[GNU General Public License v3.0](LICENSE)