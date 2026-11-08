# PROJECT: Independent Instagram AI Automation SaaS

Sen senior Python Backend Architect va Full-Stack Engineer sifatida ishlaysan.

Biz mustaqil Instagram AI Automation SaaS platformasini mutlaqo noldan yaratamiz. Loyiha kelajakda ko‘plab mijozlar va kompaniyalarga xizmat ko‘rsatadigan tijoriy mahsulot bo‘lishi kerak.

## 1. Asosiy maqsad

Foydalanuvchilar o‘z Instagram Professional (Business/Creator) akkauntlarini ulaydi va quyidagi imkoniyatlardan foydalanadi:

- Instagram Direct avtomatlashtirish.
- Kommentariyaga kalit so‘z orqali avtomatik javob.
- AI yordamchi.
- Lead va mijozlarni yig‘ish.
- CRM.
- Avtomatlashtirish Flow Builder.
- Statistika va analitika.
- Keyinchalik pullik tariflar va SaaS obunalari.

Platforma ChatPlace kabi xizmatlarga muqobil bo‘lishi kerak. Tashqi chatbot platformalariga qaram bo‘lmaymiz. Instagram bilan integratsiya Meta rasmiy API orqali amalga oshiriladi.

## 2. Texnologiyalar

Backend:
- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 Async
- Alembic
- Pydantic
- Redis
- Background Workers

Frontend:
- React
- TypeScript
- Vite

AI:
- OpenRouter API
- Turli AI modellarini tanlash imkoniyati.

Infrastructure:
- Docker
- Docker Compose
- Environment variables
- Structured logging

## 3. Arxitektura

Modular Monolith arxitekturasidan foydalan.

Backend qatlamlari qat'iy ajratilsin:

instagram_ai_saas/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── logging.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── tenant.py
│   │   ├── instagram.py
│   │   ├── conversation.py
│   │   ├── lead.py
│   │   ├── automation.py
│   │   └── subscription.py
│   │
│   ├── schemas/
│   │   ├── instagram.py
│   │   ├── message.py
│   │   ├── lead.py
│   │   └── automation.py
│   │
│   ├── api/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── instagram.py
│   │   │   ├── webhooks.py
│   │   │   ├── inbox.py
│   │   │   ├── automations.py
│   │   │   ├── leads.py
│   │   │   └── analytics.py
│   │   │
│   │   └── dependencies.py
│   │
│   ├── repositories/
│   │   ├── user_repo.py
│   │   ├── tenant_repo.py
│   │   ├── instagram_repo.py
│   │   ├── message_repo.py
│   │   ├── lead_repo.py
│   │   └── automation_repo.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── instagram_service.py
│   │   ├── messaging_service.py
│   │   ├── comment_service.py
│   │   ├── automation_service.py
│   │   ├── lead_service.py
│   │   ├── ai_service.py
│   │   └── entitlement_service.py
│   │
│   ├── integrations/
│   │   ├── meta/
│   │   │   ├── client.py
│   │   │   ├── oauth.py
│   │   │   ├── webhooks.py
│   │   │   └── messaging.py
│   │   │
│   │   └── ai/
│   │       └── openrouter.py
│   │
│   ├── workers/
│   │   ├── tasks.py
│   │   └── dispatcher.py
│   │
│   └── security/
│       ├── encryption.py
│       ├── permissions.py
│       └── tenant_context.py
│
├── migrations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── e2e/
│
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
└── docker-compose.yml

Biznes logika router ichida yozilmasin.
SQL so‘rovlar service ichida yozilmasin.
Repository ma'lumotlar bazasi bilan ishlasin.
Service biznes logikani boshqarsin.
Router HTTP so‘rovlarini qabul qilib, service'ga uzatsin.

Har bir modul mustaqil va kengaytirish mumkin bo‘ladigan qilib yozilsin.

## 4. Multi-Tenant SaaS

Platforma bir nechta mijoz va kompaniyalarga bir vaqtda xizmat qiladi.

Har bir mijozning:
- Instagram akkauntlari;
- kontaktlari;
- suhbatlari;
- avtomatlashtirishlari;
- AI sozlamalari;
- statistikasi;
- obunalari

boshqa mijozlardan qat'iy ajratilsin.

Tenant identifikatori frontend yuborgan qiymatga ishonib olinmasin. U autentifikatsiya va foydalanuvchi membership ma'lumotlari orqali aniqlansin.

## 5. Meta Instagram integratsiyasi

Faqat Meta rasmiy API va ruxsat etilgan imkoniyatlardan foydalan.

Instagram Login, OAuth, Webhooks, Direct Messages va Comments integratsiyasi alohida modul bo‘lsin.

Meta API permissionlari, token muddati, messaging window, comment private reply va App Review talablari rasmiy hujjatlar asosida tekshirilsin.

Meta cheklovlarini chetlab o‘tishga urinma.

## 6. Xavfsizlik

- Access tokenlar shifrlangan holda saqlansin.
- OAuth state tekshirilsin.
- Webhook imzosi tekshirilsin.
- Webhook eventlari takroriy kelishiga qarshi idempotency bo‘lsin.
- Tenantlararo ma'lumotlar sizib chiqmasin.
- Maxfiy ma'lumotlar loglarga yozilmasin.
- API rate limit va permission nazorati bo‘lsin.

## 7. Ishlash qoidalari

1. Kod professional, type-hinted va PEP8 standartlariga mos bo‘lsin.
2. Keraksiz murakkablik va ortiqcha abstraksiyalar kiritilmasin.
3. Har bir modul test qilinadigan bo‘lsin.
4. Har bir muhim bosqichda Git commit qilinsin.
5. `.env` Git'ga qo‘shilmasin.
6. `.env.example` tayyorlansin.
7. README va texnik hujjatlar yuritilsin.
8. Mavjud talablar bilan kelishilmagan yangi funksiyalar qo‘shilmasin.
9. Ishlamaydigan mock funksiyalarni tayyor mahsulot sifatida ko‘rsatma.
10. Har bir bajarilgan vazifani test natijalari bilan tasdiqla.

## 8. Hozirgi topshiriq

Hozircha hech qanday kod yozma.

Loyihaning to‘liq texnik arxitekturasini ishlab chiq:

- Backend papkalar tuzilishi.
- Frontend papkalar tuzilishi.
- PostgreSQL ma'lumotlar bazasi jadvallari.
- Jadvallar o‘rtasidagi bog‘lanishlar.
- Multi-tenant ma'lumotlar izolyatsiyasi.
- Meta Instagram integratsiyasi.
- AI integratsiyasi.
- Redis va background worker vazifalari.
- API endpointlar ro‘yxati.
- Xavfsizlik mexanizmlari.
- Test strategiyasi.
- Deployment va backup rejasi.
- Bosqichma-bosqich ishlab chiqish yo‘l xaritasi.

Har bir qaroringni texnik jihatdan asosla. Xavfli yoki Meta tomonidan tasdiqlanmagan imkoniyatlarni alohida belgilab ber.

Yakunida birinchi ishlab chiqish bosqichi uchun aniq vazifalar ro‘yxatini chiqar.

**MUHIM: Bu bosqichda faqat tahlil va loyiha hujjatlari. Kod yozish va fayllarni o‘zgartirishga ruxsat yo‘q.**