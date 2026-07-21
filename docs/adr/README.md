# docs/adr/ — Architecture Decision Records

> **Purpose:** Büyük mimari/ürün kararlarının detaylı, kalıcı kayıtları. Kararların
> özet listesi ve Faz 0 kararlarının tam kayıtları [DECISIONS.md](../../DECISIONS.md)
> dosyasındadır; implementation fazından itibaren yeni büyük kararlar burada birer ADR
> dosyası olarak tutulur ve DECISIONS.md'ye tek satır özet eklenir.

## Ne zaman ADR yazılır? *(bu kuralın tek sahibi bu dosyadır)*

> Diğer dosyalar (CLAUDE.md, AGENTS.md, DECISIONS.md) bu kuralı **tekrar etmez**, buraya
> link verir. Daha önce üç dosyada üç farklı formül vardı; tek tanım burasıdır.

**Yazılır:** geri dönmesi pahalı kararlar — stack seçimi, veri saklama modeli, servis
sınırları, taxonomy standardı, önemli üçüncü taraf bağımlılıkları, harici AI sağlayıcısı
kullanımı.

**Yazılmaz:** küçük implementasyon tercihleri, kolayca geri alınabilir seçimler.

**Confirmed bir kararı değiştiren her karar** ADR gerektirir; eski karar `Superseded`
işaretlenir.

**Sınır durumu kuralı:** Tereddütte kalırsan [DECISIONS.md](../../DECISIONS.md) kaydı
yeterlidir; kullanıcı isterse sonradan ADR'ye yükseltilir. "Yönü değiştiren ama kolayca
geri alınabilir" kararlar DECISIONS.md'de kalır.

## Süreç

1. [ADR_TEMPLATE.md](ADR_TEMPLATE.md) kopyalanır → `ADR-NNN-kisa-baslik.md`
   (NNN = sıradaki numara).
2. Status `Proposed` ile yazılır; kullanıcı onayıyla `Accepted` olur.
3. DECISIONS.md'ye özet satırı eklenir (D-numarası ↔ ADR-numarası eşlenir).
4. Kabul edilen ADR değiştirilmez; fikir değişirse yeni ADR yazılır ve eskisi
   `Superseded by ADR-XXX` işaretlenir.

## Index

| ADR | Başlık | Status |
|---|---|---|
| — | _Henüz ADR yok. İlk beklenen: stack seçimi (T-012, D-001'i kapatır)._ | — |
