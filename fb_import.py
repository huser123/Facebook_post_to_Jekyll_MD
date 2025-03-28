#!/usr/bin/env python3
import os
import sys
import requests
import datetime
import yaml
import argparse
from urllib.parse import urlparse

class FacebookPostImporter:
   def __init__(self, token, page_id, output_dir="FB_MD", post_count=5, debug=False):
       """
       Inicializálja az importálót
       
       :param token: Facebook API token (Page Access Token)
       :param page_id: Facebook oldal azonosítója
       :param output_dir: Kimeneti mappa
       :param post_count: Importálandó bejegyzések száma
       :param debug: Debug mód bekapcsolása részletes kimenethez
       """
       self.token = token
       self.page_id = page_id
       self.output_dir = output_dir
       self.post_count = post_count
       self.debug = debug
       
       # Mappák létrehozása, ha még nem léteznek
       self.fb_post_dir = os.path.join(output_dir, "_c-sk-facebook")
       os.makedirs(self.fb_post_dir, exist_ok=True)
       
       if self.debug:
           print("\n=== DEBUG MÓD BEKAPCSOLVA ===")
           print(f"Token: {token[:15]}...{token[-15:]}")
           print(f"Oldal ID: {page_id}")
           print(f"Output mappa: {output_dir}")
           print(f"Bejegyzések száma: {post_count}")
           print("============================\n")
   
   def verify_token_type(self):
       """Ellenőrzi, hogy a token Page Access Token-e vagy User Token"""
       print("Token típus ellenőrzése...")
       try:
           # Ellenőrizzük, hogy a tokennel hozzáférünk-e az oldalhoz
           url = f"https://graph.facebook.com/v22.0/{self.page_id}"
           params = {
               "access_token": self.token,
               "fields": "name"
           }
           
           response = requests.get(url, params=params)
           response.raise_for_status()
           data = response.json()
           
           if "name" in data:
               print(f"Sikeres kapcsolódás a következő oldalhoz: {data['name']}")
               return True
               
       except requests.exceptions.RequestException as e:
           print(f"Hiba a token ellenőrzésekor: {e}")
           if hasattr(e, 'response') and e.response:
               try:
                   error_data = e.response.json()
                   if "error" in error_data:
                       error_msg = error_data["error"].get("message", "")
                       if "missing permissions" in error_msg or "does not exist" in error_msg:
                           print("\nA megadott token valószínűleg nem Page Access Token, vagy nem rendelkezik")
                           print("megfelelő jogosultságokkal az oldal eléréséhez.")
               except:
                   pass
           
           print("\nSzeretnéd folytatni a problémás tokennel? (i/n)")
           choice = input().lower()
           if choice != 'i' and choice != 'igen':
               print("Program megszakítva.")
               sys.exit(1)
           
           print("Folytatás a problémás tokennel (ez valószínűleg nem fog működni)...")
       
   def fetch_facebook_posts(self):
       """Lekéri a Facebook bejegyzéseket"""
       print(f"Facebook bejegyzések lekérése ({self.post_count} db)...")
       
       # Először ellenőrizzük, hogy a token valóban Page Access Token-e
       self.verify_token_type()
       
       # API verzió v22.0 használata
       url = f"https://graph.facebook.com/v22.0/{self.page_id}/posts"
       params = {
           "access_token": self.token,
           "fields": "id,message,created_time,full_picture,images,attachments{media_type,url,media,title,type,subattachments{media_type,url,description,title,type,media}},permalink_url",
           "limit": self.post_count
       }
       
       try:
           response = requests.get(url, params=params)
           response.raise_for_status()
           data = response.json()
           
           if "data" not in data:
               print(f"Hibás API válasz: {data}")
               return []
               
           print(f"{len(data['data'])} bejegyzés sikeresen letöltve.")
           return data["data"]
           
       except requests.exceptions.RequestException as e:
           print(f"Hiba a Facebook API kérés során: {e}")
           return []

   def normalize_scontent_url(self, url):
       """Facebook scontent URL normalizálása a duplikációk elkerülése érdekében"""
       if not url or "scontent" not in url:
           return url
       
       # Alapvető URL szabályozás: a ? jelig tartó részt elmentjük
       # Ez tartalmazza a fájlnevet és az elérési utat, de nem a paramétereket
       base_url = url.split('?')[0] if '?' in url else url
       
       # Ha a fájlnév különböző méretre utal (pl. p720x720), azt megtartjuk
       # és a kérdőjel utáni első paraméterig tartó részt is
       if '?' in url:
           query_params = url.split('?')[1]
           first_param = query_params.split('&')[0] if '&' in query_params else query_params
           
           # Ha méret paraméter, hozzáadjuk az alap URL-hez
           if "dst-jpg_p" in first_param or "dst-png_p" in first_param:
               base_url = f"{base_url}?{first_param}"
       
       # Ellenőrizzük, hogy tartalmaz-e azonosító értéket, ami segít megkülönböztetni a képeket
       # például: 486702524_984377663785708_3263183359998342760_n.jpg
       parts = base_url.split('/')
       if len(parts) > 0:
           filename = parts[-1]
           if '_' in filename and ('n.jpg' in filename or 'n.png' in filename):
               # Már elég specifikus, visszaadjuk
               return base_url
       
       return base_url

   def is_image_url(self, url):
       """Ellenőrzi, hogy egy URL képre mutat-e"""
       if not url:
           return False
           
       url_lower = url.lower()
       
       # Ha Facebook link, de nem kép, kiszűrjük
       if "facebook.com/photo.php" in url_lower or "facebook.com/" in url_lower and "/posts/" in url_lower:
           return False
           
       # Ha scontent-et tartalmaz (Facebook CDN kép), elfogadjuk
       if "scontent" in url_lower and not url.startswith("https://www.facebook.com"):
           return True
           
       # Ha ismert képkiterjesztést tartalmaz
       if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
           return True
           
       # Ha a végén van képkiterjesztés
       parsed = urlparse(url)
       path = parsed.path.lower()
       if path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
           return True
               
       return False

   def get_all_images_from_post(self, post):
       """Összegyűjti az összes képet egy bejegyzésből"""
       images = []
       
       # Ha van fő kép a bejegyzésben
       if "full_picture" in post and post["full_picture"]:
           images.append(post["full_picture"])
       
       # Ha vannak csatolmányok
       if "attachments" in post and "data" in post["attachments"]:
           for attachment in post["attachments"]["data"]:
               # Média típus ellenőrzése
               media_type = attachment.get("media_type", "")
               
               # Kép típusú csatolmány
               if media_type == "photo":
                   # Különböző lehetséges képattribútumok ellenőrzése
                   if "url" in attachment:
                       images.append(attachment["url"])
                   
                   # Media objektum ellenőrzése
                   if "media" in attachment:
                       media = attachment.get("media", {})
                       if isinstance(media, dict) and "image" in media:
                           image = media.get("image", {})
                           if isinstance(image, dict) and "src" in image:
                               images.append(image["src"])
               
               # Album típusú csatolmány
               if media_type == "album":
                   # Külön API hívás az albumhoz tartozó képek lekéréséhez
                   if "url" in attachment:
                       images.append(attachment["url"])
               
               # Alcsatolmányok ellenőrzése
               if "subattachments" in attachment and "data" in attachment["subattachments"]:
                   for subattachment in attachment["subattachments"]["data"]:
                       sub_media_type = subattachment.get("media_type", "")
                       
                       # Kép típusú alcsatolmány
                       if sub_media_type == "photo":
                           if "url" in subattachment:
                               images.append(subattachment["url"])
                           
                           # Media objektum ellenőrzése
                           if "media" in subattachment:
                               media = subattachment.get("media", {})
                               if isinstance(media, dict) and "image" in media:
                                   image = media.get("image", {})
                                   if isinstance(image, dict) and "src" in image:
                                       images.append(image["src"])
       
       # Ha a bejegyzésnek van ID-ja, próbáljunk további képeket lekérni közvetlenül
       if "id" in post:
           try:
               url = f"https://graph.facebook.com/v22.0/{post['id']}/attachments"
               params = {
                   "access_token": self.token,
                   "fields": "media_type,url,media,subattachments{media_type,url,media}"
               }
               
               response = requests.get(url, params=params)
               response.raise_for_status()
               data = response.json()
               
               if "data" in data:
                   for attachment in data["data"]:
                       media_type = attachment.get("media_type", "")
                       
                       if media_type == "photo":
                           if "url" in attachment:
                               images.append(attachment["url"])
                           
                           if "media" in attachment:
                               media = attachment.get("media", {})
                               if isinstance(media, dict) and "image" in media:
                                   image = media.get("image", {})
                                   if isinstance(image, dict) and "src" in image:
                                       images.append(image["src"])
                       
                       # Alcsatolmányok ellenőrzése
                       if "subattachments" in attachment and "data" in attachment["subattachments"]:
                           for subattachment in attachment["subattachments"]["data"]:
                               sub_media_type = subattachment.get("media_type", "")
                               
                               if sub_media_type == "photo":
                                   if "url" in subattachment:
                                       images.append(subattachment["url"])
                                   
                                   if "media" in subattachment:
                                       media = subattachment.get("media", {})
                                       if isinstance(media, dict) and "image" in media:
                                           image = media.get("image", {})
                                           if isinstance(image, dict) and "src" in image:
                                               images.append(image["src"])
           except Exception as e:
               print(f"Hiba a további képek lekérésekor: {e}")
       
       # Szűrjük a képeket, hogy csak a valós képeket tartsuk meg
       filtered_images = []
       normalized_urls = {}  # Szótár a normalizált URL -> eredeti URL párokhoz

       for img in images:
           if img and self.is_image_url(img):
               # Ha scontent URL, normalizáljuk a duplikációk kiszűréséhez
               if "scontent" in img:
                   normalized_url = self.normalize_scontent_url(img)
                   if normalized_url not in normalized_urls:
                       normalized_urls[normalized_url] = img
               else:
                   # Nem scontent URL-eket közvetlenül adjuk hozzá
                   if img not in normalized_urls.values():
                       normalized_urls[img] = img
       
       # A szótár értékeit használjuk - ez tartalmazza az egyedi képeket
       unique_images = list(normalized_urls.values())
       
       print(f"Képek száma összesen: {len(unique_images)}")
       if unique_images and self.debug:
           print(f"Első kép: {unique_images[0]}")
           
       return unique_images
       
   def format_date(self, date_str):
       """Formázza a dátumot olvasható formára"""
       date_obj = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
       return date_obj.strftime("%Y.%m.%d %H:%M")
       
   def create_jekyll_post(self, post):
       """Létrehoz egy Jekyll bejegyzést egy Facebook bejegyzésből"""
       created_time = datetime.datetime.fromisoformat(post.get("created_time").replace("Z", "+00:00"))
       date_str = created_time.strftime("%Y-%m-%d")
       time_str = created_time.strftime("%H-%M")
       
       # Létrehozzuk a címet
       title = f"Príspevok / Bejegyzés - {created_time.strftime('%Y.%m.%d')}"
       
       # Létrehozzuk a fájlnevet
       filename = f"{date_str}-{time_str}-prispevok.md"
       file_path = os.path.join(self.fb_post_dir, filename)
       
       # Az összes kép összegyűjtése
       all_images = self.get_all_images_from_post(post)
       
       # Beállítjuk a borítóképet
       cover_image = "/assets/images/bejegyzes-alap.jpg"
       gallery_images = all_images.copy()
       
       if gallery_images:
           print(f"Bejegyzés képeinek száma: {len(gallery_images)}")
           
           cover_image = gallery_images[0]
           
           # Első képet nem mutatjuk újra a galériában, ha van elég kép
           if len(gallery_images) > 1:
               gallery_images = gallery_images[1:]
               print(f"Borítókép: {cover_image}")
               print(f"Galéria képek száma: {len(gallery_images)}")
       
       # Létrehozzuk a front matter-t
       front_matter = {
           "layout": "fb-post",
           "title": title,
           "date": created_time.strftime("%Y-%m-%d %H:%M:%S"),
           "categories": ["facebook"],
           "image": cover_image,
           "fb_url": post.get("permalink_url", ""),
           "display_date": self.format_date(post.get("created_time"))
       }
       
       if gallery_images:
           front_matter["gallery"] = gallery_images
       
       # A bejegyzés tartalmának formázása
       message = post.get("message", "")
       
       # Az üres bejegyzés kezelése
       if not message:
           message = "(Tento príspevok neobsahuje text, iba obrázky alebo iné médiá. / Ez a bejegyzés nem tartalmaz szöveget, csak képeket vagy más médiát.)"
       
       # A tartalom összeállítása
       content = f"""---
{yaml.dump(front_matter, allow_unicode=True, sort_keys=False, default_flow_style=False)}---

{message}

<div class="fb-post-info">
 <p><i class="fab fa-facebook"></i> <a href="{post.get('permalink_url', '')}" target="_blank">Zobraziť na Facebooku / Megtekintés a Facebookon</a></p>
</div>
"""
       
       # A fájl mentése
       with open(file_path, 'w', encoding='utf-8') as f:
           f.write(content)
           
       return filename
               
   def run(self):
       """Futtatja az importálást"""
       # Facebook bejegyzések lekérése
       posts = self.fetch_facebook_posts()
       
       if not posts:
           print("Nem sikerült bejegyzéseket letölteni.")
           return False
       
       # Bejegyzések létrehozása
       for post in posts:
           filename = self.create_jekyll_post(post)
           print(f"Bejegyzés létrehozva: {filename}")
       
       print("\nSiker! Facebook bejegyzések importálva.")
       print(f"Bejegyzések: {self.fb_post_dir}")
       return True


def main():
   """Főprogram"""
   parser = argparse.ArgumentParser(description="Facebook bejegyzések importálása Jekyll oldalakhoz")
   parser.add_argument("-t", "--token", default="EAATyHi6i9p8BO4VDlgvmUkCpC7XRv2M6tUpSZA1ydopNPAMjVz3obUDClN7AnmVOn7F1e01q1nnTDM60qbZAQqovkBKsw2vPmH90AmbhgIOJcr8S8MY5y4wFhqdPz4ySGQdOpwrLZALONaQxai2miDhM0lmTDMZD", 
                       help="Facebook API token (Page Access Token)")
   parser.add_argument("-p", "--page", default="265760324323651", help="Facebook oldal azonosítója")
   parser.add_argument("-o", "--output", default="FB_MD", help="Kimeneti mappa")
   parser.add_argument("-n", "--number", type=int, help="Importálandó bejegyzések száma")
   parser.add_argument("-d", "--debug", action="store_true", help="Részletes debug információk")
   
   args = parser.parse_args()
   
   # Ha a bejegyzések száma nincs megadva paraméterkent, interaktívan kérjük be
   post_count = args.number
   if post_count is None:
       try:
           print("\n== Facebook Bejegyzés Importáló ==\n")
           print("Ez a program letölti a kiválasztott Facebook oldal legutóbbi bejegyzéseit")
           print("és Jekyll bejegyzésekké alakítja azokat.\n")
           
           while True:
               try:
                   post_count = int(input("Hány bejegyzést szeretnél letölteni? [5]: ") or "5")
                   if post_count <= 0:
                       print("A bejegyzések számának pozitívnak kell lennie.")
                       continue
                   break
               except ValueError:
                   print("Kérlek, adj meg egy érvényes számot.")
       except KeyboardInterrupt:
           print("\nProgram megszakítva.")
           return False
   
   importer = FacebookPostImporter(
       token=args.token,
       page_id=args.page,
       output_dir=args.output,
       post_count=post_count,
       debug=args.debug
   )
   
   return importer.run()

if __name__ == "__main__":
   main()