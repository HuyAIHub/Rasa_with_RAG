import pandas as pd
import csv,re
from difflib import get_close_matches
from ChatBot_Extract_Intent.config_app.config import get_config

config_app = get_config()
path = config_app['parameter']['data_private']
df = pd.read_excel(path)
df = df.fillna(0)

with open('./ChatBot_Extract_Intent/data/product_final_204_oke.xlsx - Sheet1.csv', 'r') as file:
    reader = csv.DictReader(file)
    data = list(reader)

def parse_price_range(value):
    pattern = r"(?P<prefix>\b(dưới|trên|từ|đến|khoảng)\s*)?(?P<number>\d+(?:,\d+))\s(?P<unit>triệu|nghìn|tr|k)?\b"

    min_price = 0
    max_price = float('inf')

    for match in re.finditer(pattern, value, re.IGNORECASE):
        prefix = match.group('prefix') or ''
        number = float(match.group('number').replace(',', ''))
        unit = match.group('unit') or ''

        if unit.lower() in ['triệu','tr']:
            number *= 1000000
        elif unit.lower() in ['nghìn','k']:
            number *= 1000

        if prefix.lower().strip() == 'dưới':
            max_price = min(max_price, number)
        elif prefix.lower().strip() == 'trên':
            min_price = min(max_price, number)
        elif prefix.lower().strip() == 'từ':
            min_price = min(max_price, number)
        elif prefix.lower().strip() == 'đến':
            max_price = max(min_price, number)
        else:  # Trường hợp không có từ khóa
            min_price = number * 0.9
            max_price = number * 1.1

    if min_price == float('inf'):
        min_price = 0
    print('min_price, max_price:',min_price, max_price)
    return min_price, max_price


# Hàm xử lý yêu cầu
def process_command(demands, list_product):
    lst_mua = ['mua','quan tâm','tìm','thích','bán']
    lst_so_luong = ['số lượng','bao nhiêu']
    print("info:",demands)
    
    if (demands['demand'].lower() in lst_mua) and len(demands['value']) >= 1:
        return handle_buy(demands)
    elif (demands['demand'].lower() in lst_mua) and len(demands['value']) == 0:
        return handle_interest(demands)
    elif demands['demand'].lower() in lst_so_luong:
        return handle_count(demands)
    # elif demands['demand'].lower() == 'công suất':
    #     return handle_power(demands)
    elif demands['demand'].lower() == 'giá': # x
        return handle_price(demands)
    elif demands['demand'].lower() == 'bảo hành' or demands['demand'].lower() == 'thời gian sử dụng trung bình' or demands['demand'].lower() == 'tốt hơn':
        return handle_tskt(demands, list_product)
    else:
        return "Xin lỗi, tôi không hiểu yêu cầu của bạn."

# Các hàm xử lý cụ thể
def handle_buy(demands):
    # Xử lý yêu cầu
    matching_products = []
    for product in data:
        product_name = product['PRODUCT_NAME'].lower()
        group_name = product['GROUP_PRODUCT_NAME'].lower()
        specifications = re.sub(r'[^a-zA-Z0-9]', '', product['SPECIFICATION_BACKUP'].lower())
        if any(obj.lower() in group_name for obj in demands["object"]) and re.sub(r'[^a-zA-Z0-9]', '', demands["value"].lower()) in specifications:
            matching_products.append(product)

    # Trả kết quả vào một chuỗi
    result_string = ""
    if matching_products:
        result_string += f"{demands['demand'].capitalize()} {', '.join(demands['object'])} từ {demands['value'].title()} tìm thấy:\n"
        for product in matching_products:
            result_string += f"- {product['PRODUCT_NAME']} - Giá: {product['RAW_PRICE']} VNĐ\n"
            result_string += f"  Thông số kỹ thuật: {product['SPECIFICATION_BACKUP']}\n"
    else:
        # Tìm các giá trị gần đúng với "value" trong cột SPECIFICATIONS_BACKUP
        value_possibilities = set(re.sub(r'[^a-zA-Z0-9]', '', product['SPECIFICATION_BACKUP'].lower()) for product in data)
        close_matches = get_close_matches(re.sub(r'[^a-zA-Z0-9]', '', demands["value"].lower()), value_possibilities)
        
        if close_matches:
            result_string += f"Không tìm thấy {' '.join(demands['object'])} từ {demands['value'].title()} trong dữ liệu.\n"
            result_string += f"Có thể bạn muốn tìm kiếm:\n"
            for match in close_matches:
                result_string += f"- {' '.join(demands['object'])} {match.title()}\n"
        else:
            # result_string += f"Không tìm thấy {' '.join(demands['object'])} từ {demands['value'].title()} trong dữ liệu."
            result_string = handle_price(demands)
    return result_string

def handle_interest(demands):
    # Xử lý yêu cầu quan tâm đến sản phẩm với giá trị cụ thể
    found_products = {}
    for product in data:
        product_name = product['PRODUCT_NAME'].lower()
        group_name = product['GROUP_PRODUCT_NAME'].lower()
        for keyword in demands['object']:
            if f" {keyword} " in f" {product_name} " or f" {keyword} " in f" {group_name} ":
                if keyword not in found_products:
                    found_products[keyword] = []
                found_products[keyword].append(product)

    # Tạo chuỗi kết quả tìm kiếm
    result_string = ""
    for keyword in demands['object']:
        if keyword in found_products:
            result_string += f"Sản phẩm '{keyword}' tìm thấy:\n"
            if found_products[keyword]:
                for product in found_products[keyword][:3]:  # In ra 3 sản phẩm đầu tiên
                    result_string += f"- {product['PRODUCT_NAME']} - Giá: {product['RAW_PRICE']}\n"
                    specifications = product['SPECIFICATION_BACKUP'].split('\n')
                    result_string += "  Thông số kỹ thuật:\n"
                    for spec in specifications[:5]:  # In ra 5 dòng đầu tiên của thông số kỹ thuật
                        result_string += f"    {spec}\n"
            else:
                result_string += f"- Rất tiếc, không có thông tin sản phẩm {keyword} nào trong dữ liệu của tôi.\n"
        else:
            result_string += f"Không tìm thấy sản phẩm '{keyword}'.\n"

    return result_string

def handle_sale(demands):
    # Xử lý yêu cầu về sản phẩm bán chạy
    pass

def handle_count(demands):
    # Xử lý yêu cầu về số lượng sản phẩm
    matching_products = []
    for product in data:
        group_name = product['GROUP_PRODUCT_NAME'].lower()
        if any(demands["object"][0].lower() in group_name for obj in demands["object"]):
            if demands["value"]:
                specifications = re.sub(r'[^a-zA-Z0-9]', '', product['SPECIFICATION_BACKUP'].lower())
                if re.sub(r'[^a-zA-Z0-9]', '', demands["value"].lower()) in specifications:
                    matching_products.append(product)
            else:
                matching_products.append(product)


    # Trả kết quả vào một chuỗi
    result_string = ""
    if matching_products:
        result_string += f"Số lượng {', '.join(demands['object'])} {demands['value']}: {len(matching_products)} sản phẩm\n"
    else:
        # Tìm các giá trị gần đúng với "value" trong cột SPECIFICATION_BACKUP
        value_possibilities = set(re.sub(r'[^a-zA-Z0-9]', '', product['SPECIFICATION_BACKUP'].lower()) for product in data)
        close_matches = get_close_matches(re.sub(r'[^a-zA-Z0-9]', '', demands["value"].lower()), value_possibilities)

        if close_matches:
            result_string += f"Không tìm thấy {' '.join(demands['object'])} {demands['value']} trong dữ liệu.\n"
            result_string += f"Có thể bạn muốn tìm kiếm:\n"
            for match in close_matches:
                result_string += f"- {' '.join(demands['object'])} {match.title()}\n"
        else:
            result_string += f"Không tìm thấy {' '.join(demands['object'])} {demands['value']} trong dữ liệu."

    return result_string

def handle_power(demands):
    # Xử lý yêu cầu về công suất của sản phẩm
    pass
def parse_price_range(value):
    pattern = r"(?P<prefix>\b(dưới|trên|từ|đến|khoảng)\s*)?(?P<number>\d+(?:,\d+)*)\s*(?P<unit>triệu|nghìn|tr|k)?\b"

    min_price = 0
    max_price = float('inf')
    for match in re.finditer(pattern, value, re.IGNORECASE):
        prefix = match.group('prefix') or ''
        number = float(match.group('number').replace(',', ''))
        unit = match.group('unit') or ''

        if unit.lower() in ['triệu','tr']:
            number *= 1000000
        elif unit.lower() in ['nghìn','k']:
            number *= 1000

        if prefix.lower().strip() == 'dưới':
            max_price = min(max_price, number)
        elif prefix.lower().strip() == 'trên':
            min_price = min(max_price, number)
        elif prefix.lower().strip() == 'từ':
            min_price = min(max_price, number)
        elif prefix.lower().strip() == 'đến':
            max_price = max(min_price, number)
        else:  # Trường hợp không có từ khóa
            min_price = number * 0.9
            max_price = number * 1.1

    if min_price == float('inf'):
        min_price = 0
    print('min_price, max_price:',min_price, max_price)
    return min_price, max_price

def handle_price(demands):
    # Xử lý yêu cầu về giá của sản phẩm
        # Xử lý yêu cầu
    matching_products = []
    # if demands["demand"] == "giá":
    for product in data:
        group_name = product['GROUP_PRODUCT_NAME'].lower()
        if any(obj.lower() in group_name for obj in demands["object"]):
            raw_price_str = re.sub(r'[^0-9,]', '', product['RAW_PRICE'])
            raw_price = float(raw_price_str.replace(',', ''))
            min_price, max_price = parse_price_range(demands["value"].lower())
            if min_price <= raw_price <= max_price:
                matching_products.append(product)
    # else:
    #     return "Câu hỏi không liên quan đến giá sản phẩm."

    # Trả kết quả vào một chuỗi
    result_string = ""
    if matching_products:
        result_string += f"{demands['object'][0].title()} {demands['value']} tìm thấy:\n"
        for product in matching_products:
            result_string += f"- {product['PRODUCT_NAME']} - Giá: {product['RAW_PRICE']} VNĐ\n"
    else:
        result_string += f"Không tìm thấy {demands['object'][0]} {demands['value']} trong dữ liệu."

    return result_string

def handle_type(demands):
    # Xử lý yêu cầu về loại sản phẩm phổ biến
    pass

def handle_warranty(demands):
    # Xử lý yêu cầu về thời gian bảo hành
    pass

def handle_average_usage(demands):
    # Xử lý yêu cầu về thời gian sử dụng trung bình
    pass

def handle_tskt(demands, list_product):
    # Xử lý yêu cầu sản phẩm
    for product in list_product:
        if len(product) > 0:
            print(product)
            return "Tôi cần tên cụ thể của  " + product[0][-3] + " mà bạn đang quan tâm."

def take_db(demands):
    '''
    0: If dont have object return type 0
    1: return product
    2: return product for bot
    3: callback
    '''
    # If dont have object return type 0
    if demands['object'] == "":
        return [0]

    list_product = []
    for name_product in demands['object']:
        product = []
        check_group = True

        # Find product by name
        for index, row in df.iterrows():
            if name_product.lower() not in row['GROUP_PRODUCT_NAME'].lower() and name_product.lower() in row['PRODUCT_NAME'].lower():
                list_product.append([[row['LINK_SP'], row['GROUP_PRODUCT_NAME'], row['SPECIFICATION_BACKUP'],
                                     row['PRODUCT_NAME'], row['RAW_PRICE'], row['QUANTITY_SOLD']]])
                check_group = False
                break
        if not check_group:
            continue

        # Find product by group name
        for index, row in df.iterrows():
            if name_product.lower() in row['GROUP_PRODUCT_NAME'].lower():
                product.append([row['LINK_SP'], row['GROUP_PRODUCT_NAME'], row['SPECIFICATION_BACKUP'],
                                     row['PRODUCT_NAME'], row['RAW_PRICE'], row['QUANTITY_SOLD']])
        # If cant find any product return type 3
        if len(product) == 0:
            return [3, name_product]
        list_product.append(product)

    # sort product from highest price to lowest
    def key_sort(s):
        return s[5]
    for i in range(0,len(list_product)):
        list_product[i] = sorted(list_product[i], key = key_sort, reverse=True)
    
    if demands['demand'] == "":
        if demands['value'] == "":
            result = []
            for product in list_product:
                for j in range(0,min(3,len(product))):
                    result.append([product[j][0], product[j][1], product[j][2]])
            return [1, result]
        else:
            type = 2 # Type 2: SPECIFICATION_BACKUP
            list_type = [
                [4, 'trieu', 'nghin'], # Type 4: RAW_PRICE
                [5, 'ban chay nhat', 'nhieu luot mua', 'pho bien nhat'] # Type 5: QUANTITY_SOLD
            ]
            # Find type of demand
            for i in list_type:
                for j in range(1,len(i)):
                    if j[i] in demands['value']:
                        type = j[0]
            result = []
            if type == 4:
                min_price, max_price = parse_price_range(demands['value'])
            count = 0
            for product in list_product:
                for j in range(0,len(product)):
                    if type ==4 and product[j][type] >= min_price and product[j][type] <= max_price:
                        result.append([product[j][0], product[j][1], product[j][type]])
                        count += 1
                    else:
                        result.append([product[j][0], product[j][1], product[j][type]])
                        count += 1
                    if count >= 3:
                        break

            return [1, result]
    else:
        if demands['value'] == "":
            return process_command(demands, list_product)
        else:
            # srearch db
            return
        
demands = {
            "command":"Quạt sưởi không khí AIO Smart bảo hành trong bao lâu?",
            "demand":"bảo hành",
            "object":["Quạt sưởi không khí AIO Smart"],
            "value":"",
        }

print(take_db(demands))