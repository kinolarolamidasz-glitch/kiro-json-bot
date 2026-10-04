# Kiro JSON Bot — Interface Guide

## User menu

### 🛒 JSON sotish
- Tariflar chiqadi.
- User tarifni tanlaydi.
- JSON matn yoki `.json` hujjat yuboradi.
- JSON sintaksisi va duplicate keys tekshiriladi.
- Buyurtma admin panelga tushadi.
- Admin processing/approve/reject qiladi.
- Approve qilinganda summa user balansiga qo‘shiladi.
- Reject qilinganda sabab yuboriladi.

### 📝 JSON tayyorlash
- Xizmat narxi chiqadi.
- `JSON tayyorlash uchun kerakli ma’lumotlarni yuboring.` deyiladi.
- User faqat matnli ma’lumot yuboradi.
- Xizmat narxi balansdan atomik yechiladi.
- Buyurtma admin'ga user ismi, username, ID, vaqt va yuborgan ma'lumot bilan keladi.
- Admin `📤 JSON yuborish` ni bosib `.json` fayl yuboradi.
- Fayl userga yuborilgandan keyingina buyurtma `completed` bo‘ladi.
- Admin rad etsa pul balansga qaytariladi.

### 💰 Balansim
- Joriy balans
- JSON sotuvlaridan tushgan daromad
- Kutilayotgan withdrawal

### ➕ Balans to‘ldirish
- Summani kiritish.
- Admin qo‘shgan faol kartani tanlash.
- Karta rekvizitlari ko‘rsatiladi.
- To‘lovni amalga oshirib tasdiqlovchi ma'lumot yuboriladi (matn/rasm/hujjat).
- Admin tasdiqlasa balansga bir marta tushadi.
- Admin rad etsa balans o‘zgarmaydi.

### 💸 Pul chiqarish
- Summani kiritish.
- Payment method tanlash.
- Saqlangan karta yoki yangi karta/telefon.
- Withdrawal pending -> processing -> paid/rejected.
- Reject bo‘lsa summa balansga qaytariladi.

### 📦 Sotuvlarim
- JSON market buyurtmalari tarixi.

### 📜 Tarix
- Balansdagi barcha tranzaksiyalar.

### 👤 Kabinet
- User ID, ism, username, balans va ro‘yxatdan o‘tgan sana.

### 💳 Kartalarim
- Karta qo‘shish.
- Saqlangan kartani ko‘rish.
- O‘chirish.
- Withdrawal vaqtida saqlangan kartani tanlash.

### ❓ Yordam
- Admin sozlagan yordam matni.

## Admin panel

### 📊 Dashboard
Userlar, JSON buyurtmalar, withdrawals, balans xizmatlari va umumiy ko‘rsatkichlar.

### 📥 JSON Market
Pending/processing JSON buyurtmalar:
- PROCESSING
- TASDIQLASH
- RAD ETISH
- JSON yuklash
- O‘CHIRISH

### 📝 JSON xizmat
- Xizmat narxini o‘zgartirish.
- Kutilayotgan JSON tayyorlash buyurtmalarini ko‘rish.
- `📤 JSON yuborish`.
- `❌ RAD + REFUND`.

### 💎 Tariflar
JSON sotish tariflarini qo‘shish, narxini o‘zgartirish, yoqish/o‘chirish va o‘chirish.

### 💳 To‘lov usullari
Withdrawal uchun Click/Payme/Paynet/Uzum va boshqa usullarni qo‘shish, rekvizit/izohini o‘zgartirish, yoqish/o‘chirish.

### 💸 Pul chiqarish
Withdrawallarni ko‘rish va processing/paid/reject qilish.

### 💰 Balans to‘ldirish
Kutilayotgan topuplarni ko‘rish va approve/reject qilish.

### 💳 Balans kartalari
Balans to‘ldirish uchun foydalanuvchilarga ko‘rsatiladigan kartalarni admin boshqaradi:
- karta qo‘shish
- nomi
- 16–19 xonali raqam
- izoh
- ON/OFF
- o‘chirish

### 👥 Foydalanuvchilar
Userlar, ID, username, balans va blok holati.

### 💰 Balanslar
User balanslari.

### 📜 Tranzaksiyalar
So‘nggi balans harakatlari.

### 🔐 Majburiy obuna
- Kanal/guruh qo‘shish.
- Botning administrator ekanini tekshirish.
- Bir nechta kanal/guruh.
- Har birini ON/OFF.
- O‘chirish.
- Global ON/OFF.
- User `🔄 Obunani tekshirish` orqali qayta tekshiradi.

### 📣 Hammaga xabar
Matn, rasm, video yoki hujjatni barcha userlarga tarqatadi va yuborilgan/yuborilmagan sonini chiqaradi.

### ⚙️ Sozlamalar
Minimum withdrawal, yordam matni, official channel va payment channel kabi sozlamalar.

### 🗄 Backup
SQLite bazaning backup nusxasini beradi.

## Security / reliability notes
- `.env` GitHub/ZIP ichiga kiritilmagan.
- BOT_TOKEN faqat Railway Variables yoki lokal `.env`da bo‘lishi kerak.
- Balansga pul tushirish faqat admin approve qilganda amalga oshadi.
- Topup/withdrawal/order approve/reject amallari bir martalik status transition bilan himoyalangan.
- JSON xizmatida pul fayl userga muvaffaqiyatli yuborilgandan keyin `completed` qilinadi.
- JSON xizmatini rad etishda summa avtomatik refund qilinadi.
