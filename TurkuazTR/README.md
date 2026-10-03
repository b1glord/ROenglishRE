<!--
📄 Dosya Yolu: /ROenglishRE/TurkuazTR/README.md
📌 Amac: Turkce localization ve 2022-04-06 entegrasyon modelini aciklar
📌 Docs - Markdown
Version: 1.0.0
Aciklama: Upstream English, Turkce overlay ve exact client baseline katmanlarini ayri tutar
Bagimli Oldugu Katman: View
-->

# TurkuazTR

Bu klasor Ragnarok Online 2022-04-06 client icin Turkce localization entegrasyonunun durumunu tutar.

Katmanlar:

1. `upstream/latest` - llchrisll/ROenglishRE guncel referansi.
2. `client/2022-04-06` - exact 2022 client tabani.
3. `translation/tr` - mevcut Turkce ceviri calismasi.
4. `integration/2022-04-06-tr` - oyunda kullanilacak kontrollu birlesim.

Kurallar:

- Upstream master dogrudan 2022 client ustune kopyalanmaz.
- Exact 2022 dosya yapisi korunur.
- Base'i degismemis dosyalar tam overlay olarak uygulanabilir.
- `msgstringtable.txt` gibi siraya duyarli dosyalarda sadece 2022 tabaninda birebir bulunan Ingilizce satirlar Turkce karsiliklariyla degistirilir.
- 2022 tabaninda bulunmayan yeni upstream satirlari entegrasyona alinmaz.
- `achievements.lub` gibi 2022 tabaninda bulunmayan yapilar uyumluluk dogrulanmadan eklenmez.

Mevcut ilk entegrasyon; tipoftheday, GuildTip, Bard/Dancer metinleri ve 2022 ile eslesen msgstringtable cevirilerini icerir.
