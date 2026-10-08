<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/TEST-RELEASE.md
📌 Amac: Turkce localization test surumu kabul kriterlerini, bilinen aciklari ve client smoke-test planini tanimlar
📌 Docs - Markdown
Version: 1.4.0
Aciklama: v1.114.0 sonrasinda opsiyonel client denemesi ve otomatik localization kabul kurallarini tanimlar
Bagimli Oldugu Katman: View
-->

# TurkuazTR 2026.10.08-test.4

Bu belge test paketi ile final localization release asamalarini ayirir. 2022 client uzerinde manuel deneme opsiyoneldir; yapilmadiysa uyumluluk dogrulandi denilemez.

## Release kapsami

- Kaynak dal: `translation/tr`
- Upstream referansi: `upstream/latest`
- Paket profilleri: `english`, `hybrid`, `full_tr`, `bilingual`
- Paketleme araci: `TurkuazTR/tools/build-test-package.py`
- CI: `.github/workflows/turkuaz-test-release.yml`
- Client payload: `SystemEN/`, `data/` ve varsa `tipoftheday.txt`
- Paket disi: build-report JSON dosyalari ve ceviri gelistirme metadata dosyalari

## Otomatik kabul gate'leri

- Upstream sync: `translation/tr`, `upstream/latest` dalindan geri kalmamalidir.
- Skill ad/aciklama pending: gercek ceviri adayi 0 olmalidir.
- Quest display pending: 0 olmalidir.
- Pet temiz ceviri pending: 0 olmalidir; bozuk kaynaklar source-recovery icinde izole kalmalidir.
- Python syntax, overlay build, quest byte yapisi ve itemInfo builder testleri PASS olmalidir.
- Test ZIP'i bozuk olmamali ve zorunlu client dosyalarini tasimalidir.
- ZIP icine `*-build-report.json` dosyalari sizmamalidir.
- Her paket icin SHA-256 ve JSON build raporu uretilmelidir.

## Bilinen test-surumu siniri

`itemInfo.lua` serbest lore migration'i devam etmektedir. Yeni v1.111.0 generated snapshot 9685 benzersiz / 9685 occurrence seviyesindedir. Canli degerin kaynagi `TurkuazTR/iteminfo-lore.pending.json` dosyasidir. Anlami guvenli olmayan metinler Turkcelestirilmez; Ingilizce fallback olarak korunur. Bu durum test surumunu engellemez, ancak final localization release gate'i olarak kabul edilmez.

## v1.111.0 yeni test candidate

- Test adayi: `2026.10.08-test.4`.
- Exact ceviri: ana 2984 + final 10021 = 13005.
- Lore pending: 9685 benzersiz / 9685 occurrence.
- Paketleme: 4/4 PASS (english, hybrid, full_tr, bilingual); ZIP/SHA-256/JSON artifact olusturuldu.
- Paketleme CI: https://github.com/b1glord/ROenglishRE/actions/runs/37822207048
- Genel validation CI: https://github.com/b1glord/ROenglishRE/actions/runs/37822206893 (PASS).
- Paket kaynak commit: `561275ac24b9cc958aed2a6c85d7aa3204704e96`.
- CI her profil icin SHA-256 sidecar kontrolunu ve dosya yuklemesini tamamlamistir; manuel artifact indirme/karsilastirma ve gercek client testi ayrica yapilmalidir.
- Onceki test.3 paketleri bu adayin yerine kullanilmaz.
- 2022 client smoke-test opsiyoneldir. Gerceklestirilmediyse bu durum release kaydinda acikca belirtilir; gecilmis test olarak gosterilmez.

## Onceki v1.110.0 test candidate

- Test adayi: `2026.10.08-test.3`.
- Exact ceviri: ana 2984 + final 9722 = 12706.
- Lore pending: 9984 benzersiz / 9984 occurrence.
- Paketleme durumu: English, Hybrid, Full TR, Bilingual 4/4 PASS; ZIP, SHA-256 ve JSON artifact kontrolu tamam.
- GitHub Actions: https://github.com/b1glord/ROenglishRE/actions/runs/37818112171
- Paket kaynak commit: `216681c67c082fcab8cdd0304403890126e086fc`
- Durum: otomatik paketleme tamam; 2022 client uzerinde manuel smoke-test bekleniyor.
- Gercek 2022 client smoke testi ayrica yapilmalidir.

## Onceki v1.109.0 test candidate

- Test adayi: `2026.10.08-test.2`.
- Exact ceviri: ana 2984 + final 9433 = 12417.
- Lore pending: 10273 benzersiz / 10273 occurrence.
- Durum: 2026.10.08-test.2 icin dort profil ZIP ve SHA-256 kontrolu PASS. Manuel 2022 client smoke-test bekleniyor.
- GitHub Actions: https://github.com/b1glord/ROenglishRE/actions/runs/37810891735
- Paket kaynak commit: `7fde262def42a0efa667d87462a7b05f0cf5197c`
- English, Hybrid, Full TR ve Bilingual paketleri artifact olarak uretildi; 14 gun saklanir.
- Onceki test ZIP'leri v1.109.0 kaynagini temsil etmez.

## Onceki test paketleme sonucu

- CI: https://github.com/b1glord/ROenglishRE/actions/runs/37786392323
- Kaynak commit: `1b16849db63cbe96f1183dc25470c6b71feae3df`
- `english`, `hybrid`, `full_tr`, `bilingual`: 4/4 paketleme PASS.
- ZIP ve SHA-256 sidecar dogrulamasi PASS.
- Her paket icin ZIP, SHA-256 ve JSON build raporu artifact olarak uretildi.
- GitHub Actions artifact saklama suresi 14 gundur.
- Durum: otomatik paketleme tamam, gercek 2022 client smoke-test bekliyor.

## Opsiyonel manuel client smoke test

Manuel oyun ici deneme, bu localization gelistirme akisini engellemez. Otomatik dogrulama, ZIP yapisi, SHA-256, Lua yapisi, korumali tag ve pending raporlari zorunludur. Yeni bir kaynak veya ceviri hatasi bulunursa sessizce yok sayilmaz: config tabanli kural, exact ceviri veya source-recovery kaydi ile izlenir; generated ciktisi yeniden uretilir.

1. Mevcut client localization dosyalarini yedekle.
2. Once `english` kontrol paketini uygula ve client acilisini dogrula.
3. `full_tr` paketini uygula; login, karakter secimi ve harita yuklemesini test et.
4. Skill penceresi, quest penceresi, Navi, achievements, item tooltip, pet konusmalari ve kitaplari ac.
5. Renk kodu, NAVI/ITEM tag'i, satir kirilmasi ve Lua hatasi olup olmadigini kontrol et.
6. En az bir item tooltip'i, bir skill, bir quest, bir pet konusmasi ve bir kitap icin English/Full TR karsilastirmasi yap.
7. Bu deneme yapilirsa raporunu ekle; yapilmazsa `client_smoke_test: not_run` olarak acikla. Oyun icinde PASS varsayma.

## PR ve merge politikasi

Test paketi `translation/tr` dalindan uretilir. Varsayilan `master` dalina test amaciyla toplu merge yapilmaz. Final release karari, gercek pending/quality backlog'u, upstream uyumu, otomatik CI ve artifact butunlugu kapilarina gore verilir. Manuel client smoke-test zorunlu degildir; yapilmadiysa uyumluluk durumu acikca `not_verified` kalir.
