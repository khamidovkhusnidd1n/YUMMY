# Yummy Telegram Bot - Funksiyalar (Feature List)

Bu hujjat loyihadagi bot va WebApp (frontend) funksiyalarini qisqa va tartibli ko'rinishda jamlaydi.

## 1) Umumiy

- Platforma: Telegram bot (aiogram) + Telegram WebApp (Yummy App).
- Tillar: Uzbek (uz), Russian (ru), English (en).
- Ma'lumotlar bazasi: SQLite (`yummy_bot.db`).
- Rollar:
  - User (oddiy foydalanuvchi)
  - Worker (buyurtmalarni qabul qilish va status yuritish)
  - Super Admin (to'liq admin panel)

## 2) Foydalanuvchi (User) funksiyalari

### 2.1 Start va til tanlash

- `/start` bosilganda til tanlash chiqadi (uz/ru/en).
- Tanlangan til DBda saqlanadi va keyingi xabarlarda ishlatiladi.

### 2.2 Asosiy menyu

- "Yummy App" tugmasi: Telegram WebApp orqali menyu va buyurtma berish.
- "Joylashuv": manzil/ish vaqti haqida ma'lumot.
- "Biz haqimizda": restoran/servis haqida ma'lumot.
- "Aloqa": telefon/aloqa ma'lumotlari.
- "Fikrlar": feedback qoldirish yoli (admin/username).
- Admin bo'lgan foydalanuvchiga qo'shimcha: "Admin Panel" tugmasi.

### 2.3 Buyurtma berish (WebApp -> Bot)

WebApp tomoni:
- Kategoriyalar bo'yicha mahsulotlarni ko'rish.
- Qidiruv (search) orqali mahsulot topish.
- Mahsulotni savatga qo'shish, miqdorni oshirish/kamaytirish.
- Savatni ko'rish va checkout (buyurtmani botga yuborish).
- Telegram WebApp MainButton va haptic feedback ishlatiladi (mos qurilmalarda).

Bot tomoni (checkoutdan keyin):
1) Telefon raqamini olish (contact request).
2) Yetkazish usuli: delivery yoki takeaway (o'zi olib ketish).
3) Manzil: geolokatsiya yuborish yoki matn ko'rinishida.
4) Promo-kod (ixtiyoriy): kiritish yoki "Skip" qilish.
5) Buyurtma summary: taomlar, usul, manzil, yakuniy summa.
6) Tasdiqlash yoki bekor qilish.
7) Tasdiqlansa:
   - Buyurtma DBga yoziladi.
   - Foydalanuvchi ma'lumoti (ism/telefon) DBga qo'shiladi/yangilanadi.
   - Worker(lar)ga buyurtma haqida xabar yuboriladi (inline tugmalar bilan).

### 2.4 Buyurtma statuslari va SMS xabarlari

- Statuslar:
  - pending (kutilmoqda)
  - accepted (qabul qilingan)
  - preparing (tayyorlanmoqda)
  - delivering (yetkazilmoqda)
  - completed (yakunlangan)
  - rejected (rad etilgan)
- Worker statusni o'zgartirganda foydalanuvchiga SMS ko'rinishidagi xabar yuboriladi.

### 2.5 Promo-kod (foydalanuvchi tomoni)

- Promo-kod kiritish imkoniyati bor.
- To'g'ri kod bo'lsa buyurtma summasiga foizli chegirma qo'llanadi.
- Noto'g'ri kod bo'lsa xabar chiqadi va qayta urinish yoki skip qilish mumkin.

## 3) Worker funksiyalari

- Yangi buyurtma kelganda bildirishnoma oladi.
- Buyurtmani:
  - Qabul qilish yoki rad etish.
  - Qabul qilingandan keyin statusni bosqichma-bosqich yangilash (preparing -> delivering -> completed).

## 4) Super Admin funksiyalari (Admin Panel)

### 4.1 Dashboard

- Bugungi va umumiy buyurtma/tushum ko'rsatkichlari.
- Statuslar bo'yicha buyurtmalar soni va faol buyurtmalar soni.
- Adminlar soni (jami, super admin, worker).

### 4.2 Buyurtmalar monitoringi

- Statuslar bo'yicha umumiy ko'rsatkichlar.
- Oxirgi 10 ta buyurtma ro'yxati (ID, summa, status, sana).

### 4.3 Statistika va analitika

- Statistika: bugungi va umumiy (completed) buyurtmalar hamda tushum.
- Analitika:
  - Eng ko'p uchragan buyurtma kombinatsiyalari (items string bo'yicha).
  - Top mijozlar (umumiy sarf bo'yicha).

### 4.4 Menu boshqaruvi (DBdagi categories/products)

- Yangi taom qo'shish:
  - Kategoriya tanlash -> nom -> narx -> rasm (matn yoli yoki minimal placeholder).
- Narxlarni tahrirlash:
  - Kategoriya tanlash -> mahsulot tanlash -> yangi narx kiritish.
- Taomni o'chirish:
  - Kategoriya tanlash -> mahsulot tanlash -> o'chirish.

Eslatma:
- Admin panel DBdagi products jadvalini o'zgartiradi.
- WebApp menyusi hozircha front-enddagi statik MENU_DATA asosida ishlashi mumkin (agar DB bilan bog'lanmagan bo'lsa).

### 4.5 Promo-kodlar boshqaruvi

- Promo qo'shish (kod + chegirma foizi).
- Promolar ro'yxati:
  - Faol/no-faol ko'rinishi.
  - Promo kodni o'chirish.

### 4.6 Mailing (ommaviy xabar)

- Super admin yozgan xabarni barcha foydalanuvchilarga yuborish.
- Yuborishdan oldin tasdiqlash.
- `copy_message` orqali yuborish (matn/rasm/video kabi kontentlar uchun qulay).

### 4.7 Excel hisobot

- Barcha buyurtmalar bo'yicha Excel fayl yaratish va yuborish (pandas orqali).

## 5) Texnik va servis funksiyalar

- Ishga tushirish rejimi:
  - Webhook (agar `RENDER_EXTERNAL_URL` mavjud bo'lsa).
  - Aks holda polling (local/dev).
- Sozlamalar:
  - `.env`: `BOT_TOKEN`, `SUPER_ADMINS`, `WORKERS`.
  - `config.py`: admin ro'yxatlarini env dan o'qiydi.
- DB servis skriptlari:
  - `reinit_db.py`: categories/products ma'lumotlarini qayta to'ldirish.
  - `migrate_menu.py`: `menu.py` dagi MENU dan DBga migratsiya.
  - `add_lang_column.py`: users jadvaliga lang ustuni qo'shish.
  - `warmup.py`: rasmlarni Telegramga yuborib `file_id` kesh qilish (media_cache).
