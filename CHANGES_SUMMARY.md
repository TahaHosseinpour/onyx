# خلاصه تغییرات پروژه Onyx - حذف وابستگی به GPU + پیکربندی Metis AI

## تغییرات انجام شده

### 1. تغییر مدل Embedding به OpenAI (از طریق Metis AI)
**فایل**: `backend/onyx/configs/model_configs.py`

```python
# قبل:
DEFAULT_DOCUMENT_ENCODER_MODEL = "nomic-ai/nomic-embed-text-v1"
DOC_EMBEDDING_DIM = 768

# بعد:
DEFAULT_DOCUMENT_ENCODER_MODEL = "openai/text-embedding-3-small"
DOC_EMBEDDING_DIM = 1536
```

**دلیل**: مدل nomic به GPU نیاز داشت، حالا از API OpenAI استفاده می‌شود.

---

### 2. غیرفعال‌سازی Model Server ها
**فایل**: `deployment/docker_compose/docker-compose.yml`

#### تغییرات:
- سرویس‌های `inference_model_server` و `indexing_model_server` کامنت شدند
- وابستگی به model server ها از سرویس‌های `api_server` و `background` حذف شد
- متغیر `DISABLE_MODEL_SERVER=True` به environment اضافه شد

**قبل**:
```yaml
depends_on:
  - inference_model_server
  - indexing_model_server
environment:
  - MODEL_SERVER_HOST=inference_model_server
```

**بعد**:
```yaml
depends_on: []  # بدون model server
environment:
  - DISABLE_MODEL_SERVER=True
```

---

### 3. فایل Environment جدید
**فایل جدید**: `deployment/docker_compose/.env`

این فایل شامل تنظیمات زیر است:
- `DISABLE_MODEL_SERVER=true` - غیرفعال کردن model server محلی
- `DOCUMENT_ENCODER_MODEL=openai/text-embedding-3-small` - استفاده از OpenAI
- `DOC_EMBEDDING_DIM=1536` - ابعاد embedding جدید
- `OPENAI_API_KEY=your-key-here` - کلید API (باید توسط کاربر تنظیم شود)

**نکته مهم**: باید کلید OpenAI را در این فایل قرار دهید:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

---

### 4. مستندات Deployment
**فایل جدید**: `deployment/docker_compose/DEPLOYMENT_GUIDE.md`

این فایل شامل:
- راهنمای کامل نصب و راه‌اندازی
- نحوه تنظیم authentication (Basic, OAuth, OIDC, SAML)
- گزینه‌های مختلف embedding providers
- چک‌لیست production deployment
- راهنمای troubleshooting

---

## مزایای تغییرات

### ✅ حذف نیاز به GPU
- دیگر نیازی به NVIDIA GPU نیست
- می‌توان روی هر سرور معمولی اجرا کرد
- هزینه سخت‌افزاری کاهش یافت

### ✅ ساده‌تر شدن دیپلوی
- تعداد سرویس‌ها از 10 به 8 کاهش یافت
- مصرف RAM کمتر (حداقل 4GB کافی است)
- نیاز به nvidia-docker-toolkit حذف شد

### ✅ مقیاس‌پذیری بهتر
- با استفاده از API های ابری، محدودیت GPU نداریم
- می‌توان به راحتی scale کرد

---

## معایب و هزینه‌ها

### ⚠️ هزینه API
- OpenAI embedding: ~$0.02 به ازای هر 1 میلیون توکن
- برای پروژه‌های بزرگ، هزینه می‌تواند بالا رود

### ⚠️ تأخیر شبکه (Latency)
- قبلاً: 10-50ms (GPU محلی)
- حالا: 100-500ms (API خارجی)
- برای کاربران ایرانی با توجه به محدودیت‌های شبکه، ممکن است کندتر باشد

### ⚠️ وابستگی به اینترنت
- نیاز به اتصال دائمی به اینترنت برای embedding
- در صورت قطع اتصال، indexing کار نمی‌کند

---

## نحوه استفاده

### 1. نصب و راه‌اندازی سریع

```bash
cd deployment/docker_compose

# 1. ویرایش فایل .env و اضافه کردن API key
nano .env
# OPENAI_API_KEY=sk-your-key-here

# 2. اجرای docker compose
docker compose up -d

# 3. مشاهده لاگ‌ها
docker compose logs -f
```

### 2. دسترسی به برنامه
- وب: http://localhost:3000
- API: http://localhost:8080

### 3. تنظیمات LLM
پس از ورود، به بخش Admin → Settings بروید و:
- LLM Provider را انتخاب کنید (OpenAI, Anthropic, etc.)
- API Key را وارد کنید
- Model را انتخاب کنید (gpt-4, claude-3, etc.)

---

## گزینه‌های جایگزین برای کاهش هزینه

### استفاده از Cohere (ارزان‌تر)
```bash
DOCUMENT_ENCODER_MODEL=cohere/embed-english-v3.0
DOC_EMBEDDING_DIM=1024
COHERE_API_KEY=your-cohere-key
```

### استفاده از Voyage AI
```bash
DOCUMENT_ENCODER_MODEL=voyage/voyage-large-2-instruct
DOC_EMBEDDING_DIM=1024
VOYAGE_API_KEY=your-voyage-key
```

### بازگشت به مدل محلی (در صورت نیاز)
اگر بعداً بخواهید به مدل GPU برگردید:
1. در `docker-compose.yml` کامنت model server ها را بردارید
2. `DISABLE_MODEL_SERVER=true` را حذف کنید
3. `DOCUMENT_ENCODER_MODEL=nomic-ai/nomic-embed-text-v1` تنظیم کنید

---

## تست کردن

### بررسی سرویس‌ها
```bash
docker compose ps
```

باید 8 سرویس running باشد:
- api_server
- background
- web_server
- nginx
- relational_db (postgres)
- index (vespa)
- cache (redis)
- minio

### بررسی لاگ‌ها
```bash
# API server
docker compose logs api_server | grep -i error

# Background worker
docker compose logs background | grep -i error
```

### تست API
```bash
curl http://localhost:8080/health
```

باید پاسخ `{"status": "ok"}` یا مشابه آن را دریافت کنید.

---

## نکات مهم

### 🔐 امنیت
برای production حتماً:
- `AUTH_TYPE` را فعال کنید (نه `disabled`)
- پسوردهای قوی برای database و minio تنظیم کنید
- SSL/TLS فعال کنید
- `ENCRYPTION_KEY_SECRET` تنظیم کنید

### 📊 پایش
- لاگ‌ها در volume های docker ذخیره می‌شوند
- می‌توانید از Sentry برای error tracking استفاده کنید
- برای monitoring production، Prometheus + Grafana توصیه می‌شود

### 🔄 بروزرسانی
```bash
# دریافت آخرین نسخه
docker compose pull

# اعمال تغییرات
docker compose up -d
```

### 💾 پشتیبان‌گیری
```bash
# Database
docker compose exec relational_db pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql

# MinIO (فایل‌ها)
docker compose exec minio mc mirror /data/onyx-file-store-bucket ./backup/minio/
```

---

## مشکلات رایج و راه‌حل

### خطا: "OpenAI API key not found"
**راه‌حل**: API key را در `.env` تنظیم کنید و سرویس‌ها را restart کنید

### خطا: "Cannot connect to model server"
**راه‌حل**: مطمئن شوید `DISABLE_MODEL_SERVER=true` در `.env` وجود دارد

### خطا: "Embedding dimension mismatch"
**راه‌حل**: اگر قبلاً از nomic استفاده می‌کردید، باید Vespa index را rebuild کنید

### سرعت پایین embedding
**راه‌حل**:
1. از VPN با سرعت بالا استفاده کنید (برای کاربران ایران)
2. یا از Cohere که server های نزدیک‌تر دارد
3. یا batch size را افزایش دهید: `EMBEDDING_BATCH_SIZE=512`

---

## پشتیبانی

برای سوالات و مشکلات:
- GitHub Issues: https://github.com/onyx-dot-app/onyx/issues
- Discord: https://discord.gg/onyx
- Documentation: https://docs.onyx.app

---

**تاریخ تغییرات**: 2025-11-03
**نسخه**: بدون GPU (Cloud API Mode)
