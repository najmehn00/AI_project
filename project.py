# import json
# with open("/Users/najmeh/Desktop/chatbot/chiline-main.products.json","r") as file:
#     data = json.load(file)


# print(json.dumps(data,indent=2))
# descriptions = [product['description'] for product in data['products']]

import json

# Load JSON data
with open("/Users/najmeh/Desktop/chatbot/chiline-main.products.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Extract product information
for p in data:
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
        f"ویژگی‌ها: {', '.join([f'{spec['keyFa']}={spec['valueFa']}' for spec in p.get('specifications', [])])}\n"
        f"تاریخ ایجاد: {p.get('createdAt', {}).get('$date', '')}\n"
        f"تاریخ آخرین تغییر: {p.get('updatedAt', {}).get('$date', '')}\n"
    )
    print(content)
