# Modül Kayıtları

Her uygulanan Python paketinde `MODULE.md` zorunludur.

Bir kayıt aşağıdaki sorulara cevap verir:

1. Input nereden geldi?
2. Modül inputu nasıl doğruladı?
3. Hangi algoritmayı uyguladı?
4. Output nedir?
5. Output hangi modüllere dağıtıldı?
6. Hata veya timeout durumunda ne oldu?
7. Hangi testler doğruluyor?

`python tools/validate_project.py` eksik kayıtları CI hatası hâline getirir.
