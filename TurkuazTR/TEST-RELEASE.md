<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/TEST-RELEASE.md
📌 Amac: Turkce localization test surumu kabul kriterlerini, bilinen aciklari ve client smoke-test planini tanimlar
📌 Docs - Markdown
Version: 1.0.0
Aciklama: 2026.10.07-test.1 paketinin repo, CI, roadmap ve oyun ici test gate'lerini tek yerde takip eder
Bagimli Oldugu Katman: View
-->

# TurkuazTR 2026.10.07-test.1

Bu surum son kullanici final release'i degildir. Amac, generated localization profillerini gercek client uzerinde guvenli sekilde test etmektir.

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

`itemInfo.lua` serbest lore migration'i devam etmektedir. Guncel generated pending 21022 benzersiz / 21695 occurrence seviyesindedir. Anlami guvenli olmayan metinler Turkcelestirilmez; Ingilizce fallback olarak korunur. Bu durum test surumunu engellemez, ancak final localization release gate'i olarak kabul edilmez.

## Manuel client smoke test

1. Mevcut client localization dosyalarini yedekle.
2. Once `english` kontrol paketini uygula ve client acilisini dogrula.
3. `full_tr` paketini uygula; login, karakter secimi ve harita yuklemesini test et.
4. Skill penceresi, quest penceresi, Navi, achievements, item tooltip, pet konusmalari ve kitaplari ac.
5. Renk kodu, NAVI/ITEM tag'i, satir kirilmasi ve Lua hatasi olup olmadigini kontrol et.
6. En az bir item tooltip'i, bir skill, bir quest, bir pet konusmasi ve bir kitap icin English/Full TR karsilastirmasi yap.
7. Kritik hata yoksa `full_tr` paketini test adayi olarak kabul et; metin kalite sorunlarini translation backlog'una ayir.

## PR ve merge politikasi

Test paketi `translation/tr` dalindan uretilir. Varsayilan `master` dalina test amaciyla toplu merge yapilmaz. Test sonucu ve upstream uyumu temizlendikten sonra merge/release stratejisi ayri gate olarak ele alinir.
