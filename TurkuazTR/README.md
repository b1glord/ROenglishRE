<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/README.md
📌 Amac: ROenglishRE Turkce ceviri ve client entegrasyon modelini dokumante eder
📌 Docs - Markdown
Version: 1.2.0
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
