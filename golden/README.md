# Golden set — eşleşme kalitesi ölçümü (T-006b / D-062)

`_CALIBRATED` bugüne kadar **boş** kaldı ve sebebi dürüsttü: kalibre edilmiş
bir şey yoktu çünkü **hiçbir ölçüm yoktu**. Bu dizin o boşluğu kapatır.

## Neden "isabet" değil "aşırı iddia" ölçüyoruz

Bu ürünün iddiası "en isabetli eşleşmeyi bulmak" değil, **yanlış umut
vermemek**. D-005 (yüzde/olasılık yok) ve D-019 (bilmediğimize "uymuyor"
demeyiz) bunun için var.

O yüzden birincil ölçü **aşırı iddia (overclaim)**: üretilen bandın, elle
etiketlenen "en yüksek savunulabilir bant"tan yüksek olduğu vaka sayısı.
Kullanıcı "GÜÇLÜ EŞLEŞME" görüp başvurur ve boşa umutlanırsa, ürün asıl
sözünü bozmuş olur — %90 isabet bunu telafi etmez.

İkincil ölçüler (eksik iddia, tam/komşu isabet) bilgi amaçlıdır.

## Dosyalar

| Dosya | İş |
|---|---|
| `set.json` | 3 persona + 37 **donmuş** ilan anlık kopyası + elle etiket |
| `eval.py` | Ölçüm aracı: `python golden/eval.py` (veya `--json`) |
| `verify_fidelity.py` | Donmuş kopya canlı hattın bandını üretiyor mu? |
| `patch_field.py` | Donmuş vakalara yeni alan ekler — **job_id ile eşleyerek** |
| `../services/core/tests/test_golden.py` | CI korkuluğu — eşik aşılırsa kırmızı |

## ⚠ Golden set'i ASLA yeniden örneklemeyin

Örnekleme, sistemin **ürettiği banda** göre tabakalıdır. Eşleştirici
değişince örnek yeniden dizilir ve **indeks bazlı etiketler başka ilanlara
yapışır**. Bu gerçekten oldu: kıdem tavanı eklendikten sonra yeniden
örneklemede 5 vakanın etiketi yanlış ilana bağlandı ve ölçüm geçersiz bir
sonuç üretti (fark yalnızca hizalama denetimiyle görüldü).

Kural: **set bir kez donar.** Yeni bir alan gerekiyorsa `patch_field.py`
kullanılır — o, vakaları `job_id` ile eşler, sırayla değil.

## Neden donmuş anlık kopya

Korpus 6 saatte bir tazelenir ve ilanlar 45 günde düşer (D-024). Canlı korpusa
bakan bir değerlendirme her koşuda başka bir şey ölçer ve **regresyon zemini
olamaz**. Bu yüzden ilanlar (şartlarıyla birlikte) `set.json` içinde donar.

Fixture korpusu (8 ilan) bu iş için kullanılamaz: şartları **elle yazılmış**,
yani çıkarım hattını (lexicon/extract) hiç sınamaz. Buradaki 37 vaka gerçek
ilanlardan ve gerçek çıkarım çıktısından alınmıştır.

**Sadakat şart:** `verify_fidelity.py` donmuş kopyanın canlı hatla aynı bandı
ürettiğini doğrular. İlk sürümde bu denetim gerçek bir hata yakaladı:
`extraction_confidence` ve `is_legal_eligibility` alanları dondurulmuyordu,
varsayılana düşen 3 vakada bant `good` yerine `strong` çıkıyordu — ölçüm aracı
kendi uydurduğu bir gerçekliği ölçüyordu.

## Etiketleme kuralı

Her vaka için iki alan:

* `ilgili` — ilan personanın mesleğine ait mi?
* `en_yuksek_savunulabilir_bant` — dikkatli bir insan değerlendiricinin
  savunabileceği **en yüksek** bant. `null` = bantlanamaz.

Uygulanan yargılar:

1. **Kıdem doğrulanamıyorsa üst düzey rol `cond`'u geçemez.** Yıl beyanı
   olmayan bir profile "Senior/Staff" rolü için `strong` demek, doğrulanmamış
   bir iddiadır.
2. **Zorunlu (`hard`) şart bilinmiyorsa `cond`'u geçemez** — "Go 5 yıl" veya
   "Almanca" zorunluysa ve profil söylemiyorsa eşleşme şartlıdır.
3. **Meslek kayıyorsa `cond`** — "Partner Solutions Architect" bir satış
   rolüdür, devops profili için tam eşleşme değildir.
4. **Alakasız meslek → `null`** (şoföre risk yöneticiliği).

## Ölçülen zemin (2026-07-25, 37 vaka)

| Ölçü | D-062 (kıdem körü) | D-063 (kıdem tavanı) |
|---|---|---|
| **AŞIRI İDDİA** | 18 — **%48,6** | 8 — **%21,6** |
| alakasıza bant | 0 | 0 |
| eksik iddia | 0 | 1 |
| tam isabet | %51,3 | **%75,7** |
| komşu isabet (±1) | %78,4 | **%94,6** |

**Kök neden — kıdem körlüğü.** `match()` yalnızca `requirements` ve
`is_public_sector` okuyordu; ilanın `experience_level`'ı eşleşmeye **hiç
girmiyordu**. Ölçüm (14.504 ilanlık korpus):

| Profil | Bantlanan | Üst düzey role `strong`/`good` |
|---|---|---|
| Yeni mezun (yıl beyanı yok) | 1.474 | **247 (%16,8)** — 49'u `strong` |
| 9 yıllık kıdemli | 1.766 | 463 (%26,2) |

Yeni mezunun oranı gerçek kıdemliye yakındı; kıdem hesaba girseydi neredeyse
sıfır olmalıydı. Aradaki fark yalnızca beceri sayısından geliyordu.

**Düzeltme sonrası (canlı doğrulama, `level=senior` filtresiyle aynı ilanlar):**

| Profil | Bant dağılımı |
|---|---|
| Yeni mezun (yıl yok) | `cond: 40` — hiç `strong`/`good` yok, gerekçe notu var |
| 9 yıllık kıdemli | `strong: 23`, `good: 17` |

### Kalan 8 aşırı iddia (kıdemden değil)

* 4 vaka — çekirdek beceri **doğrulanmamış** (ML rolünde ML bilinmiyor)
* 2 vaka — **zorunlu** şart bilinmiyor (yüksek lisans, Almanca)
* 2 vaka — **meslek kayması** (satış/partner ve program yöneticiliği rolleri
  devops profiline "güçlü" görünüyor)

Sıradaki iyileştirmeler bunları hedefler; eşik yine aşağı çekilir.

## Sınırlar — dürüstçe

* **37 vaka küçüktür.** Yön gösterir, mutlak kalite notu vermez.
* **Etiketler proje geliştiricisi tarafından konmuştur**, gerçek kullanıcı
  yargısı değildir. Kendi kurallarımıza göre kendimizi ölçüyoruz.
* Bu yüzden asıl hedef: `/api/feedback` (D-059) ile akan **gerçek kullanıcı
  geri bildirimi** biriktikçe bu küme onunla değiştirilmeli/genişletilmeli.
* 3 persona var (şoför, yeni mezun yazılımcı, devops). Muhasebe, garson,
  hemşire gibi personalar örneklendi ama henüz etiketlenmedi.

## Eşiği güncelleme kuralı

`test_golden.py` içindeki eşik **bugünün gerçeğidir, hedef değildir**. Her
iyileştirmede **aşağı** çekilir. Yukarı çekmek ancak golden set büyüdüğünde ve
gerekçesi yazıldığında meşrudur — aksi hâlde korkuluk, kırılmayı gizleyen bir
lastik bandına dönüşür.
