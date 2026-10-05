<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/README.md
📌 Amac: ROenglishRE Turkce ceviri ve client entegrasyon modelini dokumante eder
📌 Docs - Markdown
Version: 1.6.0
Aciklama: Upstream senkronu, Turkce calisma dali ve 2022 client cikisini birbirinden ayirir
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
- `achievements`: 1637 exact Turkce satir.
- `recommended_quests`: 252 exact Turkce satir.
- `town_info`: 2 exact Turkce satir.
- `sign_data`: 53 exact Turkce satir.
- `navi_data`: 1327 exact Turkce satir.
- `ba_frostjoke`: 100 exact ASCII Turkce satir.
- `dc_scream`: 105 exact ASCII Turkce satir.

`line-overlays.json` registry'sine yeni bir bilesen eklendiginde CI bunu dort profil icin otomatik build eder.

Satir yapisi upstream ile birebir olmayan dosyalar `file-overlays.json` registry'si ile source blob SHA kilitli whole-file overlay olarak yonetilir:

- `tipoftheday`: ASCII Turkce whole-file overlay.
- `guild_tip`: ASCII Turkce whole-file overlay.

Upstream source blob degisirse whole-file build fail olur ve ceviri yeni upstream ile tekrar gozden gecirilmeden sessizce uygulanmaz.

English profili upstream kaynagini degistirmeden kullanir. Hybrid, Full TR ve Bilingual profilleri line-overlay bilesenlerinde Turkce patch uygular. Bilingual farki su anda skill adlarinda `Turkce (English)` bicimindedir; uzun UI metinlerinde gereksiz cift dil gosterimi yapilmaz.
