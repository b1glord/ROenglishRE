<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/README.md
📌 Amac: ROenglishRE Turkce ceviri ve client entegrasyon modelini dokumante eder
📌 Docs - Markdown
Version: 2.20.0
Aciklama: Upstream senkronu, Turkce calisma dali, genisletilmis UI/harita/state icon localization ve 2022 client cikisini birbirinden ayirir
Bagimli Oldugu Katman: View
-->

# TurkuazTR

Bu fork artik upstream'in birebir kopyasi olarak degil, Turkce localization calisma alani olarak yonetilir.

- `archive/tr-2025-10-25`: eski Turkce calismanin dokunulmaz yedegi.
- `upstream/latest`: llchrisll/ROenglishRE guncel referansi.
- `translation/tr`: aktif Turkce ceviri dali.
- `client/2022-04-06`: exact 2022 client tabani.
- `integration/2022-04-06-tr`: 2022 client icin kontrollu Turkce cikis.
- `sync/upstream-2026-09`: guncel upstream ustune yeniden tasinan Turkce calisma.

Upstream dosyalari Turkce dosyalarla korlemesine ezilmez. Yeni upstream satirlari Ingilizce kalir ve sonraki ceviri turunda ele alinir.


## Durum kontrolu

Tum branch referanslari local repoda fetch edildikten sonra:

```bash
python3 Tools/turkuaz_translation_status.py
```

CI ayni kontrolu `translation/tr` dalindaki ilgili degisikliklerde otomatik calistirir. `needs-review` durumu upstream dosyasinin son senkrondan sonra degistigini ve Turkce karsiligin yeniden kontrol edilmesi gerektigini belirtir.


## Bilincli Ingilizce / ozel ad politikasi

`TurkuazTR/intentional-english.json`, clientte bilincli olarak Ingilizce kalan job/class adlarini, para birimlerini, sistem adlarini ve teknik format satirlarini exact-line olarak tutar.

Status araci `msgstringtable.txt` icin:
- Turkcelestirilmis/uyarlanmis satirlari,
- bilincli Ingilizce/teknik satirlari,
- gercek ceviri incelemesi gereken yeni satirlari

ayri ayri raporlar. Upstream'de yeni veya degismis bir satir exact listeye otomatik girmez; yeniden incelenmesi gerekir.


## Skill profilleri

Skill adlari kaynakta iki alanla birlikte tutulur:

- `name_original`: upstream/orijinal Ingilizce ad.
- `name_tr`: ASCII Turkce ad.

Skill ceviri durumu:

- `skillinfolist.tr.json`: 883 Turkce skill adi, gercek pending 0.
- `skilldescript.tr.json`: 826 Turkce skill aciklamasi, gercek ceviri adayi 0.
- Kaynakta blok olup aciklamasi bos/placeholder olan 11 skill `empty_descriptions` olarak ayri raporlanir.
- Kaynak `skilldescript.lub` icinde aciklama blogu bulunmayan 46 skill `missing_descriptions` olarak ayri raporlanir; bunlara uydurma metin eklenmez.

`TurkuazTR/localization-profiles.json` dort ayri cikis tanimlar:

- `english`: Ingilizce skill adi + orijinal Ingilizce aciklama.
- `hybrid`: Ingilizce skill adi + Turkce aciklama.
- `full_tr`: Turkce skill adi + Turkce aciklama.
- `bilingual`: `Turkce (English)` skill adi + Turkce aciklama.

Generated paketler `TurkuazTR/generated/<profile>/` altinda tutulur. Boylece ceviri verisi tek yerde saklanir; istemciye verilecek dil profili ayri secilir.


## Ortak localization overlay modeli

Canonical profil kaynagi `TurkuazTR/localization-profiles.json` dosyasidir.

Exact satir bazli ceviriler `TurkuazTR/line-overlays.json` registry'si ile yonetilir. Her overlay:

- `source_path`: upstream/latest icindeki orijinal Ingilizce kaynak.
- `patch_path`: yalnizca Turkce degisen satirlari tutan patch dosyasi.
- `profile_field`: English/Hybrid/Full TR/Bilingual profilinde hangi dil modunun uygulanacagi.
- `output_path`: generated profil agacindaki hedef dosya.

Su anda ortak line-overlay modeline tasinan bilesenler:

- `msgstringtable`: 3499 exact Turkce satir; inceleme bekleyen satir 0.
- `achievements`: 1638 exact Turkce satir; 2 ozel ad bilincli korunur, ceviri inceleme acigi 0.
- `recommended_quests`: 270 exact Turkce satir; kalan gorunen satirlar class/seviye etiketi veya ozel addir, ceviri inceleme acigi 0.
- `town_info`: 4 exact Turkce satir; kullaniciya gorunen Ingilizce acik 0.
- `sign_data`: 61 exact Turkce satir; kullaniciya gorunen Ingilizce acik 0.
- `navi_data`: 2273 exact Turkce satir; genel NPC, nesne ve harita etiketleri tamamlandi, canonical ozel adlar ve monster adlari bilincli korunur.
- `help_messages`: 79 komut yardim satiri ASCII Turkce; ceviri acigi 0.
- `titles`: 47 karakter unvani ASCII Turkce; ceviri acigi 0.
- `worldview`: 377 harita/konum etiketi Turkce; saf canonical ozel adlar bilincli korunur.
- `map_names`: 1144 harita etiketi Turkce; kalan satirlar Battle Royale/canonical ozel ad/etkinlik adlaridir.
- `ba_frostjoke`: 100 exact ASCII Turkce satir; kalan 19 satir skill/monster/joke adi olarak bilincli korunur.
- `dc_scream`: 105 exact ASCII Turkce satir; kalan 12 satir ceviri gerektirmeyen nida/ses satiridir.
- `state_icons`: 247 skill-sozlugu eslesmeli baslik + 472 guvenli tooltip aciklamasi olmak uzere 719 exact ASCII Turkce satir; kalan uzun/ozel durum aciklamalari kontrollu dilimlerle tamamlanir.

`line-overlays.json` registry'sine yeni bir bilesen eklendiginde CI bunu dort profil icin otomatik build eder.

Satir yapisi upstream ile birebir olmayan dosyalar `file-overlays.json` registry'si ile source blob SHA kilitli whole-file overlay olarak yonetilir:

- `tipoftheday`: ASCII Turkce whole-file overlay.
- `guild_tip`: ASCII Turkce whole-file overlay.

Upstream source blob degisirse whole-file build fail olur ve ceviri yeni upstream ile tekrar gozden gecirilmeden sessizce uygulanmaz.

English profili upstream kaynagini degistirmeden kullanir. Hybrid, Full TR ve Bilingual profilleri line-overlay bilesenlerinde Turkce patch uygular. Bilingual farki su anda skill adlarinda `Turkce (English)` bicimindedir; uzun UI metinlerinde gereksiz cift dil gosterimi yapilmaz.


## Quest profil modeli

`questid2display.txt` ve `OngoingQuests.lub` satir bazli generic overlay yerine record-aware byte-safe patch araclariyla yonetilir.

- Canonical Turkce patch: `TurkuazTR/questid2display.tr.json`
- Quest display apply: `Tools/apply_questid2display_translation.py`
- OngoingQuests apply: `Tools/apply_ongoingquests_translation.py`
- Ortak profil builder: `TurkuazTR/tools/build-quest-profile.py`

Profil davranisi:

- `english`: upstream quest display + upstream OngoingQuests.
- `hybrid`: Turkce quest display + Turkce OngoingQuests.
- `full_tr`: Turkce quest display + Turkce OngoingQuests.
- `bilingual`: Turkce quest display + Turkce OngoingQuests.

Bilingual profil uzun quest metinlerinde iki dili ayni anda gostermez. Iki dil birlikte yalnizca kisa skill adlarinda kullanilir. Quest patchleri kaynak byte yapisini, satir sonlarini ve OngoingQuests icindeki korumali NAVI/ITEM taglarini muhafaza eder.


## Pet konusma localization modeli

`Translation/Renewal/data/pettalktable.xml` once encoding ve kaynak kalitesine gore envanterlendi.

- Toplam 6417 metin dugumu bulundu.
- 5181 dugum / 3902 benzersiz ifade temiz ASCII Ingilizce ve dogrudan Turkce ceviri adayidir.
- 952 dugum karisik encoding/mojibake tasir; kaynak dogrulanmadan ceviriye alinmaz.
- 160 dugum agir non-ASCII kaynaktir; once kaynak dil/encoding tespiti gerekir.
- 124 dugum neutral/kisa ifade olarak ayri tutulur.
- Canonical pending envanter: `TurkuazTR/pettalktable.pending.json`.
- Guvenli pet overlay'i: 137 benzersiz ifade / 689 exact kaynak satiri ASCII Turkceye cevrildi; mojibake ve belirsiz satirlar disarida tutulur.
- Canonical Turkce patch: `TurkuazTR/pettalktable.tr.json` ve Hybrid/Full TR/Bilingual profillerine baglandi.
- Yeniden uretim araci: `TurkuazTR/tools/extract-pettalk-pending.py`.

Bozuk encoding metinleri Turkceye uydurularak sabitlenmez. Temiz Ingilizce bloklar once cevrilir; sorunlu bloklar upstream veya dogru encoding kaynagi ile karsilastirildiktan sonra ele alinir.


## Oyun ici kitap localization modeli

`Translation/Renewal/data/book/` altindaki 70 kaynak dosya incelendi.

- 46 dosya gercek lore, rehber, tarif veya oyun ici okunabilir metin olarak Turkce ceviri hedefidir.
- 24 adet `1000897.txt` - `1000920.txt` dosyasi eski Kore sunucusu bagisci/oyuncu listeleridir ve ceviri kapsaminda degildir.
- Ilk 15 kitap tamamlandi; guncel liste `TurkuazTR/books/index.json` dosyasinda tutulur.
- Kalan gercek kitap sayisi: 31.
- Ayrintili durum: `TurkuazTR/books/index.json`.
- Kitaplar `file-overlays.json` uzerinden source blob SHA kilitli whole-file overlay olarak uretilir.
- English profil orijinal kaynagi; Hybrid, Full TR ve Bilingual profilleri Turkce kitap metnini kullanir.
- `11064.txt` Korece kaynakli gercek rehberdir ve ceviri hedefidir.
- `prontera bible01.txt`, `11000.txt` ile ayni Rune-Midgarts lore metnini farkli satir duzeniyle tekrarlar; Turkce metin yeniden kullanilabilir.
