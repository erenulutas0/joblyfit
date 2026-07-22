"""İlan metninde arama.

**Neden sunucuda:** korpustaki açıklamalar toplam 30 MB. Arayüzün diğer
filtreleri istemcide anında çalışıyor ve öyle kalmalı, ama tam metin araması
için 30 MB'ı tarayıcıya göndermek anlamsız. Sunucu ilan kimliklerini döner
(birkaç yüz KB), istemci kendi filtrelerini onun üzerine uygular.

**Neden gerekli:** arama şimdiye kadar yalnızca başlık, işveren, şehir ve şart
önizlemesine bakıyordu. "forklift", "SAP", "kaynakçı" gibi sözlükte olmayan
ama ilan metninde geçen terimler hiç bulunamıyordu — kullanıcı aradığı işin
var olduğunu bilmeden "sonuç yok" görüyordu.

**Operatörler:** iş arayanlar aramayı daraltmak ister; bu yüzden sadece
kelime yığını değil, üç operatör desteklenir:

* ``muhasebe uzman``  → ikisi de geçmeli (VE mantığı)
* ``"ön muhasebe"``   → tam öbek
* ``-stajyer``        → bu kelime geçmemeli

Dışlama özellikle işe yarıyor: "mühendis -satış" ya da "-stajyer" tek
başına yüzlerce alakasız ilanı eler.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .pipeline import fold

#: Aramada taranan metnin üst sınırı (karakter). İlanların kuyruğu genelde
#: hukuki metin ve eşit fırsat beyanı; oraya kadar aramak hem yavaş hem de
#: alakasız eşleşme üretir.
_MAX_SCAN = 8000


@dataclass(frozen=True, slots=True)
class Query:
    terms: tuple[str, ...]      # hepsi geçmeli
    phrases: tuple[str, ...]    # tam öbek olarak geçmeli
    excluded: tuple[str, ...]   # hiçbiri geçmemeli

    @property
    def is_empty(self) -> bool:
        return not (self.terms or self.phrases or self.excluded)


_PHRASE = re.compile(r'"([^"]+)"')


def parse(raw: str) -> Query:
    """Arama dizesini operatörlerine ayırır."""
    if not raw:
        return Query((), (), ())

    text = fold(raw)
    phrases = tuple(p.strip() for p in _PHRASE.findall(text) if p.strip())
    text = _PHRASE.sub(" ", text)

    terms: list[str] = []
    excluded: list[str] = []
    for word in text.split():
        if word.startswith("-") and len(word) > 1:
            excluded.append(word[1:])
        elif word:
            terms.append(word)
    return Query(tuple(terms), phrases, tuple(excluded))


def haystack(posting) -> str:
    """Bir ilanın aranabilir metni.

    Başlık ve işveren **iki kez** yazılır. Sıralama yapmıyoruz, ama bir terim
    yalnızca uzun açıklamanın içinde geçtiğinde de başlıkta geçtiğinde de
    eşleşme sayılması gerekir; bu yüzden ikisi de aynı torbaya girer.
    """
    job = posting.job
    parts = (
        job.title, job.employer, job.city, job.occupation_id,
        (posting.job_text or "")[:_MAX_SCAN],
    )
    return fold(" ".join(p for p in parts if p))


def matches(hay: str, q: Query) -> bool:
    """Torbanın sorguyu karşılayıp karşılamadığı.

    Dışlama **önce** bakılır: eleme, dahil etmeden ucuzdur ve kullanıcı
    "-stajyer" yazdıysa niyeti nettir.
    """
    if any(x in hay for x in q.excluded):
        return False
    if not all(p in hay for p in q.phrases):
        return False
    return all(t in hay for t in q.terms)
