import os
import json
import time
from dotenv import load_dotenv
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

def create_llama_index_from_json(json_file):
    print("\nشروع ساخت ایندکس از فایل JSON...")
    start_time = time.time()
    documents = []

    # Load JSON data
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    for i, p in enumerate(data, 1):
        try:
            # Fixed the nested quotes issue by using double quotes outside, single quotes inside
            specs_text = ', '.join([f"{spec.get('keyFa', '')}={spec.get('valueFa', '')}" for spec in p.get('specifications', [])])
            
            content = (
                f"نام محصول: {p.get('title', '')}\n"
                f"نام محصول (انگلیسی): {p.get('titleEn', '')}\n"
                f"شناسه محصول (ID): {p.get('_id', {}).get('$oid', '')}\n"
                f"SKU: {p.get('productItems', [{}])[0].get('sku', '')}\n"
                f"وضعیت: {p.get('status', '')}\n"
                f"توضیحات کوتاه: {p.get('title', '')}\n"
                f"توضیحات کامل: {p.get('description', '')}\n"
                f"قیمت: {p.get('productItems', [{}])[0].get('price', '')}\n"
                f"در تخفیف: {p.get('productItems', [{}])[0].get('discount', 0) > 0}\n"
                f"موجودی: {p.get('productItems', [{}])[0].get('qty', 'نامشخص')}\n"
                f"تصاویر: {', '.join(p.get('images', []))}\n"
                f"دسته‌بندی‌ها: {', '.join([c.get('$oid', '') for c in p.get('category', [])])}\n"
                f"ویژگی‌ها: {specs_text}\n"
                f"تاریخ ایجاد: {p.get('createdAt', {}).get('$date', '')}\n"
                f"تاریخ آخرین تغییر: {p.get('updatedAt', {}).get('$date', '')}\n"
            )
            documents.append(Document(text=content))
            print(f"محصول {i}/{len(data)} پردازش شد: {p.get('title', 'بدون نام')} (ID: {p.get('_id', {}).get('$oid', 'نامشخص')})")
        except Exception as e:
            print(f"خطا در پردازش محصول {i}: {e}")

    print(f"\nتعداد اسناد ساخته‌شده: {len(documents)}")
    print("در حال ساخت ایندکس VectorStore...")

    try:
        # تنظیم LLM و Embedding با تأخیر
        llm = OpenAI(model="gpt-3.5-turbo", temperature=0.0)
        embed_model = OpenAIEmbedding(
            model="text-embedding-ada-002",
            embed_batch_size=10,
            additional_kwargs={"timeout": 60}
        )

        # تنظیمات سراسری
        Settings.llm = llm
        Settings.embed_model = embed_model

        # ساخت ایندکس با دسته‌بندی کوچک‌تر و تأخیر
        index = VectorStoreIndex.from_documents(
            documents=documents,
            show_progress=True
        )
        print("ایندکس با موفقیت ساخته شد.")
    except Exception as e:
        print(f"خطا در ساخت ایندکس: {e}")
        return None

    end_time = time.time()
    print(f"زمان صرف‌شده برای ساخت ایندکس: {end_time - start_time:.2f} ثانیه")
    return index

def main():
    json_file_path = "/Users/najmeh/Desktop/chatbot/chiline-main.products.json"  # مسیر فایل JSON خود را اینجا قرار دهید

    print("شروع برنامه...")
    print(f"مسیر فایل JSON: {json_file_path}")
    print("-" * 50)

    # ساخت ایندکس
    index = create_llama_index_from_json(json_file_path)
    if index is None:
        print("ساخت ایندکس ناموفق بود.")
        return

    print("\nدر حال ذخیره ایندکس...")
    try:
        index.storage_context.persist(persist_dir="my_product_index")
        print("ایندکس با موفقیت در مسیر 'my_product_index' ذخیره شد.")
    except Exception as e:
        print(f"خطا در ذخیره ایندکس: {e}")

    # تست پرس‌وجو
    print("\nتست پرس‌وجو از ایندکس...")
    try:
        query_engine = index.as_query_engine()
        response = query_engine.query("محصولاتی که در تخفیف هستند را معرفی کن.")
        print("پاسخ به سؤالم:")
        print(response)
    except Exception as e:
        print(f"خطا در پرس‌وجو: {e}")

    print("-" * 50)
    print("برنامه با موفقیت به پایان رسید.")

if __name__ == "__main__":
    main()