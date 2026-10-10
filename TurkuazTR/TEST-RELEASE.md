<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/TEST-RELEASE.md
📌 Amac: Turkce localization test surumu kabul kriterlerini, bilinen aciklari ve client smoke-test planini tanimlar
📌 Docs - Markdown
Version: 1.9.0
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


## v1.158.0 - canli itemInfo / 2022 client kabul kapisi

> Bu bolum bir test prosedurudur. **Gercek oyun ici test yapilmadi**; PASS sonucu varsayilmaz. Guvenli olmayan oyun mekanigi ve belirsiz sayisal bonus metinleri kaynak onariminda tutulur.

- Dal: `translation/tr`; yeni shard: `TurkuazTR/config/iteminfo-exact-v1158.tr.json`. Hedeflenen source-recovery: **103 -> 80**; temiz pending **0**. Gercek degerler generated `TurkuazTR/iteminfo-lore.pending.json` raporundan dogrulanir.
- Paket: `.github/workflows/turkuaz-test-release.yml` is akisinin `english`, `hybrid`, `full_tr`, `bilingual` ZIP, SHA-256 ve JSON sonucunu kullan. `source_commit` alanini yeni generated `translation/tr` commit'iyle eslestir; eski `test.4` paketini guncel paket sanma.
- Once ayri bir **2022 Ragnarok client kopyasi** olustur. 2015 RagnarokClient/Thor dosyalarini, farkli patcher'lari ve ozel GRF'leri degistirme. Aktif `SystemEN` ve `data` yukleme onceligini istemci konfigurasyonundan kontrol et.
- Windows PowerShell dogrulamasi: `Get-FileHash .\TurkuazTR-full_tr-<version>.zip -Algorithm SHA256`; dosyanin .sha256 degeriyle karsilastir. ZIP'i ayri test klasorune ac.
- `english` ile giris, karakter secimi, harita yuklemesini test et; sonra `full_tr` ve ayrica `hybrid`/`bilingual` profilleriyle tekrar et.
- Tooltip ornekleri: item ID `14601` (5 dakika, MATK/HIT/FLEE), `15398` (iki satirin anlami), `15400`, `15401`, `15402`, `15399` (stat turleri), `31854` (firinci aciklamasi), `11589` ve `6769` (yiyecek). English karsiligi, satir birlesmesi ve beceri sayilari kontrol edilmeli.
- Skill penceresi, quest/NAVI penceresi, pet diyalogu ve kitap sayfalarinda UTF-8, renk etiketleri, `<NAVI>`/`<INFO>` kodlari, metin tasmasi ve Lua yukleme hatalarina bak.
- Test kaydinda tarih, client PACKETVER, profil, yukleme dizini, item ID, beklenen/gorulen metin, ekran goruntusu, sonuc (PASS/FAIL/NOT_RUN) ve varsa hata logu bulunsun. FAIL varsa kod kaydi ac; otomatik CI PASS tek basina gercek oyun ici kabul degildir.
- Geri alma: temiz client kopyasina don veya `SystemEN` ve `data` yedegini geri yukle. Oyun ici test yoksa `client_smoke_test: not_run` ve `client_visual_acceptance: not_verified`.


## v1.159.0 - otomatik guncel test paketi provenansi

- Onceki `2026.10.08-test.4` tarihsel checkpoint'tir. Yeni TurkuazTR ceviri testleri icin guncel artifact'leri kullan.
- `turkuaz-skill-translation.yml` ceviri profillerini yeniler, degisiklik varsa `translation/tr` dalina commit'ler, sonra **ayni run icinde** dort istemci test paketini hazirlar. GitHub `GITHUB_TOKEN` bot commit'i tek basina yeni `push` paket is akisinin calismasini tetiklemedigi icin bunu ayri bot-push workflow'una birakmiyoruz.
- Paketler `english`, `hybrid`, `full_tr`, `bilingual` profilleri icin ayri ZIP + SHA-256 sidecar + JSON raporuyla artifact olarak yuklenir. Surum etiketi `test-<guncel_commit_ilk_12>` ve `source_commit` degeri generated profillerin son commit'ine ait olmalidir.
- CI dort paket icin `.sha256` checksum, ZIP bozulma kontrolu, gerekli client dosyalarini, `smoke_test: pass` ve birebir kaynak commit eslesmesini dogrular. Eksik dosya veya eski SHA hata kabul edilir.
- Manuel `turkuaz-test-release.yml` baslatilirken version alani bos birakilirsa `test-<github_sha12>` kullanilir; tarihsel test.4 etiketi otomatik yeniden uretilmez.
- ZIP'in PASS olmasi oyunda acilis, karakter secimi veya tooltip'in gorsel ve anlamsal kabul testini **kanitlamaz**. Client kabul alani test gercekten yapilana dek `NOT_RUN` / `not_verified` kalir.


## v1.160.0 - kaynak kanitli cift satir itemInfo aciklamalari

- Temporal Circlet item #19474 ve ayni metni kullanan diger Temporal Circlet'ler: Hugin ile ilgili iki Ingilizce satir **ayni anda** Turkcelestirilir; yarisi Ingilizce yarisi Turkce metin olusmamasi icin bitisik satir sozlesmesi CI'da denetlenir. Referans: https://divine-pride.net/database/item/19474/circlet-of-timerune-knight-1
- Steamed Ancient Lips item #12069: fis veya tarif isimleri tahmin edilmez, `Ancient Lips` ifadesi korunur. Bagimsiz kaynak: https://db.irowiki.org/db/item-info/12069/
- Odin guc cubbesi item #15397: aciklamanin iki kaynak satiri birlikte cevrilir.
- Toplam 3 **yeni** exact satir kaynak onarim listesinden cikarilir. Iki tamamlayici satir zaten onceki exact config dosyalarinda cevrilmistir; bunlara tekrar kayit eklenmez, mevcut Turkce ifadelerle uyum saglanir. Normal pending 0 kalir; kaynak onarim hedefi **80 -> 77**.
- Sayisal etkisi eksik metinler veya bozuk renk kodlari bu pakette tahminen duzeltilmez. Gercek Ragnarok 2022 istemcisi acilis ve gorsel tooltip kabul testi: `NOT_RUN / not_verified`.


## v1.161.0 - kaynak butunlugu triage ve korumali ceviri

- Kaynak onarimi kuyrugu **77 -> 76**: iki item (23014, 23200) icin ayni `Potion Box` / `Poison Bottle Box` listesindeki miktarlar ve item adlari aynen korunarak tek kaynak satiri Turkcelestirildi.
- CI `audit-iteminfo-recovery-context.py` dosyasinin `integrity_flags` ve `integrity_risk_counts` alanlari ile kaynak bozuk baytlarini (`invalid_source_bytes`), bos renkli yazi dizisini (`empty_color_span`), eksik yuzde degerini (`missing_percent_value`), olasi renk kodu/metin cakismasini (`suspected_color_marker_text_overlap`) ve belirtilmemis refine esigini (`missing_refine_threshold`) ayri bildirir. Bunlar **kaynak inceleme uyarilaridir**; otomatik iyilestirme veya ceviri anlamina gelmez.
- Kaynak tarafinda bozuk rune/renk/beceri ya da eksik sayisal oyun etkisi varsa `itemInfo.lua` sessizce degistirilmez, yeni sayi/skill uydurulmaz. Bu durumlar 76 adaylik kaynak kurtarma listesinde yer almaya devam eder.
- Yeni regresyon testi her iki item ID'sindeki exact satir kimligini, rakamlari, renk tag'lerini ve Lua guvenligini dogrular. Bilinen kaynak risklerinin belirlenme kurallarini da kilitler.
- Gercek 2022 client uzerinde gorsel/senaryo kabul durumu halen `client_smoke_test: not_run`, `client_visual_acceptance: not_verified`.

## v1.162.0 - Herosria Mage Hat kaynak kanitli yuzde onarimi

- Item #400338 (Herosria Mage Hat) icin kaynakta eksik olan alinmis oyuncu hasari yuzdesi, Korece esya aciklamasi ve bagimsiz esya betigi aciklamasiyla **%5** olarak dogrulandi. Bu bir tahmin degil; yalniz dogrulanmis etkide yapilan Turkce exact ceviridir.
- Ingilizce `itemInfo.lua` degistirilmez. Eski bozuk `by%.` kaynak satiri, profile ait exact mapping ile `%5` olarak gosterilir. Renk etiketleri `^FF0000` ve `^000000` korunur.
- Kanit: https://www.divine-pride.net/database/item/400338 ; https://ratemyserver.net/index.php?ird=1&item_id=400338&page=re_item_db
- Source recovery sayaci **76 -> 75**, kaynak butunlugu yuksek riskli sayac **7 -> 6** olmali. Diger alti kaynak kusuru onarilmadan ve kanitsiz deger atanilmadan kuyrukta kalir.
- Gercek 2022 client tooltip ve acilis kabul testi halen **NOT_RUN / not_verified**.

## v1.163.0 - Ramen Hat Box beceri rengi kaynak onarimi

- Item ID 13725 (Ramen Hat Box) icinde `^00990Decrease AGI^000000` seklinde bozuk kaynak renk etiketi var. Ilk D harfi hex rengin parcasiymis gibi okunuyordu. Kaynak metin aynen kalir; yalniz Turkce profilde `^009900Decrease AGI^000000` gosterilir.
- Oyun mekanigi bagimsiz item 5293 Ramen Hat aciklamasi ve `AL_DECAGI` item betigiyle dogrulandi: kullanici saldiriya ugradiginda Seviye 1 Decrease AGI otomatik etkinlesebilir. Sansa ait sayisal oran, kaynak aciklamasinda verilmedigi icin ceviriye eklenmedi.
- Kanit: https://ratemyserver.net/index.php?item_id=5293&page=item_db ; https://www.divine-pride.net/database/item/5293/ramen-hat
- Item 28342 Critical Anklet icin ikincil aciklamalar +7 verirken bazi item betiklerinde `.@r > 7` bulunuyor. Bolgesel istemci/betik eslesmesi netlesmeden rafine seviyesi **onarilmadi**.
- Item 590003 icin bos renkli bolumun hangi yetenegi ifade ettigi kesinlestirilmediginden silinmedi. Bozuk kaynak baytlarini iceren 3 aday da aynen korundu.
- Kaynak onarim kuyrugu **75 -> 74**, yuksek riskli kaynak adaylari **6 -> 5** beklenir. Normal pending 0 kalir.
- Orijinal `Translation/Renewal/SystemEN/LuaFiles514/itemInfo.lua` degistirilmez. Gercek 2022 istemcide acilis ve gorsel kabul testi NOT_RUN / not_verified.

## v1.164.0 - baglam denetimli kaynak kurtarma dilimi

- Tamamen dogrulanmis 6 farkli itemInfo kaynak metni kuyruktan cikarildi (7 kaynak gorunumu). Original `itemInfo.lua` SHA `5bc5f92edd8f08ebd57ff0991f0297bc51026058` degistirilmez.
- 13834/13835 Dungeon Teleport Scroll II kutularinin `Kiel Hyre / Thanatos / Abyss Lakes` giris satiri cevrildi. Diger iki bitisik satir onceki exact shard icinde zaten bulundugundan tekrar kaydedilmedi.
- 12725 Nosiege Runestone icin `Marsh of Abyss` ve `Mandragora Howling` beceri adlari oldugu gibi korunarak baglac cevrildi. Renk etiketi aynen kalir.
- 22614 Premium Manual satirindaki baslangic `30Increases` bozuk tekrarindan sonra yalniz bir defa `30 dakika` gosterilir. %50 EXP ve %100 drop degerleri degismez; bagimsiz item ve item script kanitlidir.
- 18190 Bolt Shooter ve 32303 Bolt Revolver icin Einbech madenindeki civi disinda muhimmat atma aciklamasinin iki satiri birlikte cevrildi. Iki farkli parcali kaynakta ayni Turkce sonuc cikartilir, mevcut oyun mekaniği sayilarina dokunulmaz.
- Bagimsiz kaynaklar: https://ratemyserver.net/index.php?item_id=22614&page=re_item_db ; https://ragnaplace.com/en/iro/item/12725/nosiege-runestone ; https://db.pservero.com/item/32303/Ein_1HGUN ; https://ratemyserver.net/index.php?item_type=5&page=re_item_db&page_num=28
- Normal pending: 0. Kaynak kurtarma: **74 -> 68**. Source-integrity risk: **5** (1 bos renkli metin, 1 eksik refine esigi, 3 bozuk bayt). Bu kayitlara dogrulanmamis sayi/skill atanmadi.
- Dort profilin CI ZIP paketleri gercek 2022 client testinin yerine gecmez. Client smoke test NOT_RUN, gorsel kabul not_verified.

## v1.165.0 - surrogateescape ham bayt kaynak onarimi

- Source `itemInfo.lua` dosyasinin ham baytlari SHA-1 Git blob sozlesmesiyle aynen korunur. `0x81` ve `0x81 0xB7` onekleri Unicode tahminiyle silinmez veya CP949 metnine donusturulmez.
- Uc gorunur aciklama sadece Turkce profilde ASCII sinirli exact byte map ile onarilir: ID 7686/7688 icin Nekorin NPC koordinatlari (64 183) ve Polin Group; ID 7688/7856 icin Guillotine Cross; ID 7686/7687 icin Rune Knight.
- Lua icindeki `\\\"Nekorin\\\"` kacis dizisi birebir korunarak anahtar olusturulur; ceviri hedefindeki `"Nekorin"` karakterleri builder tarafinda guvenli kacirilir. Ham source anahtari surrogateescape ile ASCII disi baytlarini kayipsiz temsil eder.
- Regresyon testleri byte-donusum round-trip, Lua string siniri, item ID, komsu satirlar, rakamlar, isimler, source SHA ve original English profili denetler.
- Source recovery **68 -> 65**, integrity-risk **5 -> 2** olmasi beklenir. 590003 bos renkli metin ve 28342 Bloody Muffler refinman seviyesindeki kaynak/betik uyusmazligi cozulmedi: oyun kurali uydurulmez.
- Gercek 2022 istemci smoke/tooltip kabul testi NOT_RUN / not_verified.

## v1.166.0 - 2025 eski ceviri arsivi ile kaynak karsilastirmasi

- 2025 `archive/tr-2025-10-25` dali ile guncel `translation/tr` itemInfo gorunur alanlari ayni item ID ve field uzerinden karsilastirildi.
- **26.647** ortak item ID, **100.149** eslesik gorunur alan ve **6.438** degismis gorunur alan mevcut. Eski-versiyon metninde farkli olup Turkce karakter iceren alan sayisi **0**. Bu sayi ASCII ile yazilmis Turkceyi tek basina kapsamaz.
- Acik kaynak onarimi kuyrugundaki **65** bagimsiz metnin tamami guncel itemInfo icinde bulundu. Eski arsivde **110** ayni/kaynak gibi Ingilizce metin gorunumu vardir; **1** gorunum, item ID 450252 arsivde olmadigi icin kiyaslanamaz.
- Kalan **65** metinden eski arsivde dogrudan kullanilabilecek kanitli Turkce satir sayisi **0**. Dikkatsiz toplu eski metin kopyalamak, yenilenen Ingilizce kaynak ve sayisal etkileri geriye goturebilir.
- CI `iteminfo-legacy-recovery-comparison` artefakti baglam, komsu satir, item ID, eksik eski item, sayisal ve renk tag uyumlulugunu kalici raporlar. Bu rapor bir ceviri onayi degildir.
- Kaynak onarim sayaci **65** olarak kalir; otomatik ceviri veya eski kaynak metne geri donus yapilmaz. Eksik kaynak oyun mekanigi, renk, ve refine degerleri yalniz guvenilir bagimsiz kanitla onarilir.
- Gercek Ragnarok 2022 istemcisinde full TR veya Hybrid gorsel kabul: `NOT_RUN / not_verified`.

## PR ve merge politikasi

Test paketi `translation/tr` dalindan uretilir. Varsayilan `master` dalina test amaciyla toplu merge yapilmaz. Final release karari, gercek pending/quality backlog'u, upstream uyumu, otomatik CI ve artifact butunlugu kapilarina gore verilir. Manuel client smoke-test zorunlu degildir; yapilmadiysa uyumluluk durumu acikca `not_verified` kalir.
