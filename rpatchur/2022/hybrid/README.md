# TurkuazTR / Ragnarok 2022 — rPatchur Hybrid test kanali

File Path: /ROenglishRE/rpatchur/2022/hybrid/README.md
Purpose: Explain isolated patch testing over HTTPS via GitHub Releases
Module: Documentation - Markdown
Version: 1.0.1
Description: Explain corrected HTML hosting for Windows WebView and native Ragnarok.exe launcher
Dependency Layer: View

Bu kanal **testtir**, canli oyuncularin eski 2015 patch listesiyle birlestirilmez.
Paketler CI'da \`TurkuazTR/generated/hybrid\` ile uretilir, source commit SHA rapora yazilir.
Paket THOR modunda client-root loose files \`use_grf_merging: false\` ile uretilir.
Hedef \`data/\`, \`SystemEN/\`, \`tipoftheday.txt\` dosyalaridir. Oyun EXE ve \`.grf\` degistirilmez.

Kurulum (Windows 10 x64):
1. 2022 client klasorunu kopyalayin; orijinali degistirmeyin.
2. Test surumunun GitHub Releases sayfasindan \`Turkuaz2022HybridTest-Launcher.zip\` dosyasini indirin.
3. ZIP icindeki \`TurkuazHybridTest.exe\` ve \`TurkuazHybridTest.yml\` dosyalarini *kopyaladiginiz client kokune* cikartin. Patcher adi ve YAML adi birebir ayni olmalidir.
4. \`TurkuazHybridTest.exe\` dosyasini calistirin, \`Guncelle\` deyin ve bittiginde tooltipleri inceleyin.
5. Oyununuzun exe adi \`Ragnar Ragnarok Online.exe\` degilse YML \`play.path\` alanini duzeltin; oyun acma islemi testin ilk asamasi icin zorunlu degildir.
6. Bir sonraki test kanal paketleri ayni release adresinde yayinlandiginda patcher uzaktaki plist dosyasini gorerek yeni THOR'u uygulayabilir.
7. \`TurkuazHybridTest.dat\` dosyasi patcher cache'idir. Eski uygulamalari zorla yeniden kurmak disinda silmeyin.

Geri alma: Orijinal istemciyi temiz kopyadan acin. Test patchlerini oyuncularin production client'ine uygulamayin.

Patch dagitimi: https://github.com/b1glord/ROenglishRE/releases/tag/rpatchur-2022-hybrid-test
RPatchur kaynagi: https://github.com/L1nkZ/rpatchur
RPatchur binary: official v0.3.0 Windows i686 release; yapimciya ait executable'i degistirmeyiz.

Bilinen sinirlar: RPatchur launcher exe self-update yapamaz. Windows ve oyunun acilmasi test edilmedi. Kodlama ve tooltipler gercek 2022 istemcide dogrulanmalidir.

## Windows WebView HTML goruntuleme duzeltmesi (v1.167.1)

Eski launcher `cdn.jsdelivr.net/gh/.../index.html` uzerinden HTML'i `text/plain` gibi gosterdigi icin tarayici kaynak kodunu ekrana basabilir. Yeni test launcher `rawcdn.githack.com/<owner>/<repo>/<commit>/rpatchur/2022/hybrid/index.html` adresini kullanir ve CI sunucunun `Content-Type: text/html` cevabini dogrular. Bu, ucuncu taraf bir test CDN'idir; daha kalici cozum ilk taraf GitHub Pages ya da HTTPS statik host olacaktir.

**Eski ZIP'i indirdiyseniz:** yalnız `TurkuazHybridTest.yml` dosyasinda `web.index_url` satirini yeni SHA-pinned rawcdn.githack.com adresiyle degistirmek yeterlidir. `TurkuazHybridTest.exe` dosyasini yeniden kurmak veya oyunu degistirmek gerekmez.

Windows 2022 ornek klasorde `Ragnarok.exe` goruldugu icin yeni default `play.path` bu isme donusturuldu. Istemcinin gercek baslaticisi farkliysa once `play.path` kontrol edilmelidir.
