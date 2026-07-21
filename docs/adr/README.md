# docs/adr/ — Architecture Decision Records

> **Purpose:** Büyük mimari/ürün kararlarının detaylı, kalıcı kayıtları. Kararların
> özet listesi ve Faz 0 kararlarının tam kayıtları [DECISIONS.md](../../DECISIONS.md)
> dosyasındadır; implementation fazından itibaren yeni büyük kararlar burada birer ADR
> dosyası olarak tutulur ve DECISIONS.md'ye tek satır özet eklenir.

## Ne zaman ADR yazılır?

- Geri dönmesi pahalı kararlar: stack seçimi, veri saklama modeli, servis sınırları,
  taxonomy standardı, önemli üçüncü taraf bağımlılıkları.
- Bir Confirmed decision'ı değiştiren her karar (eski karar `Superseded` işaretlenir).
- Yazılmaz: küçük implementasyon tercihleri, kolayca geri alınabilir seçimler.

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
