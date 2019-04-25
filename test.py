#coding=utf8
# from pypinyin import lazy_pinyin 
# print(''.join(lazy_pinyin("abc")))
import requests
import os,sys,time
from lxml import etree
import json
import re
import pymysql
# import data

cid = 0

# 设置当前工作区域
os.chdir(os.path.split(os.path.realpath(__file__))[0])
# 获取
# # print(os.getcwd())

# 开启数据库指针
config={
    "host":"120.24.87.1",
    "user":"suibian",
    "password":"123456",
    "database":"online_test",
    "charset":'utf8'
}
# 数据
# db = pymysql.connect(**config)
# # 数据库指针
# cursor = db.cursor()


# 获取logo名称并保存
def getLogoName(brand_id):
    res = requests.get('https://car.autohome.com.cn/price/brand-%s.html' % brand_id)
    print('https://car.autohome.com.cn/price/brand-%s.html' % brand_id)
    if res.status_code != 404:
        html = res.text
        _element = etree.HTML(html)
        if _element == None:
            return ''
        # try:
        path = _element.xpath('//div[@class="carbradn-pic"]/img/@src')
        if len(path) <= 0:
            return ''
        path = path[0]
        # except ZeroDivisionError:
        #     return ''
        # path = '//car2.autoimg.cn/cardfs/series/g26/M05/B0/29/100x100_f40_autohomecar__ChcCP1s9u5qAemANAABON_GMdvI451.png'
        logo_path = 'http:'+os.path.split(path)[0]
        # 保存额图片名
        logo_name = os.path.split(path)[1].split('autohomecar__')[1]
        # 无底色图片路径
        real_path = logo_path + '/' + logo_name
        # 图片二进制
        content = requests.get(real_path).content
        # 保存图片
        with open('./static/logo/'+logo_name,'wb') as f:
            f.write(content)
        return logo_name
        # print(logo_name)
        # print(logo_path)
    else:
        return ''
# print(getLogoName(3))

# 获取颜色 @return数组
def getColor(spec_id):
    detail_url='https://www.autohome.com.cn/spec/%s' % spec_id
    html = requests.get(detail_url).text
    _element = etree.HTML(html)
    res = [0,0]
    res[0] = _element.xpath('//div[@class="pic-color"]//div[@class="athm-carcolor__tip"]/text()')
    res[1] = []
    tmp = _element.xpath('//div[@class="pic-color"]//em[@class="item-all"]/@style')
     # res = list(set(res))
    for item in tmp:
        print(item)
        matchObj = re.compile(r'\#.{6}').findall(item)
        res[1].append(matchObj[0])
    
    return res

# getColor()

def getSpec(series_id):
    s_url = 'https://car.autohome.com.cn/duibi/ashx/specComparehandler.ashx?callback=jsonpCallback&type=1&seriesid=%s&format=json' % series_id
    line = requests.get(s_url).text
    # print(line)
    # print(line)
    matchObj = re.compile( r'jsonpCallback\((\{.*?\})\)').findall(line)

    if len(matchObj) != 0:
        return json.loads(matchObj[0])['List']
    else:
        return []
# getSpec(179)

def getSpecAll():
    s_url = 'https://car.autohome.com.cn/javascript/NewSpecCompare.js?20131010'
    line = requests.get(s_url).text
    matchObj = re.compile( r'var listCompare\$100= (.*?);').findall(line)
    # print(string)
    return json.loads(matchObj[0])
    
# print(getSpecAll())
# 车系

def actionGetSeries():
    res = getSpecAll()
    db = pymysql.connect(**config)
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    for index0 in range(0,len(res)):
        brand = res[index0]
        brand_id = brand['I']
        brand_name = brand['N']
        brand_letter = brand['L']
        factory_arr = brand['List']
        sql = """REPLACE INTO
            think_car_brand(
                id,
                name,
                letter,
                update_time
            )
            VALUES('%s','%s','%s', '%s')
        """ % (brand_id, brand_name, brand_letter, time.time())
        cursor.execute(sql)
        db.commit()

        for index1 in range(0,len(factory_arr)):
            
            factory_name = factory_arr[index1]['N']
            factory_id = factory_arr[index1]['I']
            if re.search(r'进口', factory_name) == None:
                factory_type = 0
            else:
                factory_type = 1

            spec_arr = factory_arr[index1]['List']
            
            sql = """REPLACE INTO 
                think_car_factory(
                    id,
                    name,
                    update_time
                )
                VALUES('%s','%s','%s')
            """ % (factory_id, factory_name, time.time())
            cursor.execute(sql)
            db.commit()

            for index2 in spec_arr:
                

    # 完成重置最大值
    cid = 0
# 爬取颜色
def actionGetColor(i=0):
    max_len = 0
    db = pymysql.connect(**config)
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    if max_len == 0:
        sql = """SELECT 
                id 
            FROM think_car_spec
            WHERE id < 10000000
            ORDER BY id desc
            LIMIT 1
        """
        cursor.execute(sql)
        res = cursor.fetchall()
        max_id = res['id']

    # 到达多少次查询后自动断开
    connect_time = 60
    start_time = time.time()
    while i < max_id:
        if db == None:
            db = pymysql.connect(**config)
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
        i = i + 1
        sql = 'SELECT id FROM think_car_spec where id = %s' % i
        cursor.execute(sql)
        res = cursor.fetchall()
        if len(res) == 0:
            continue

        print('正在处理id为'+str(i)+'的车型颜色')
        color_arr = getColor(i)
        color_name_arr = color_arr[0]
        color_color_arr = color_arr[1]
        
        for a in range(0,len(color_name_arr)):
            print('插入颜色' + color_name_arr[a])
            sql = """INSERT INTO think_car_color(
                sid,
                hex,
                color,
                status,
                update_time) 
                VALUES('%s','%s','%s','%s','%s')
            """ % (i, color_color_arr[a],color_name_arr[a], 1, int(time.time()))
            # 执行Sql
            cursor.execute(sql)
            # 提交数据
            db.commit()

        if  time.time() -  start_time > connect_time:
            
            start_time = time.time()
            # 重新重连
            cursor.close()
            db.close()
            db = None

            print('开始重连...')
            time.sleep(1)
    

# while i < 6000:
#     # if i % connect_times == 0:
#     #     db = pymysql.connect(**config)
#     #     cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
#     if db == None:
#         db = pymysql.connect(**config)
#         cursor = db.cursor(cursor=pymysql.cursors.DictCursor)

#     i = i + 1    
#     sql = 'SELECT id FROM think_car_series where id = %s' % i
#     cursor.execute(sql)
#     res = cursor.fetchall()
#     if len(res) != 0:
#         spec_list = getSpec(res[0]['id'])
#         # print(spec_list)
#         # sys.exit(0)
#         for x in spec_list:
#             # 在售车型
#             if x['I'] == 1:
#                 mark_spec = x['List']
#                 # 遍历车系的所有车型
#                 for y in mark_spec:
#                     print('正在处理id为'+str(i)+'的车系')
#                     _id = y['I']
#                     _name = y['N']
#                     _price = y['P']
#                     sql = """REPLACE INTO think_car_spec(
#                         id,
#                         sid,
#                         name,
#                         price,
#                         status,
#                         update_time) 
#                         VALUES('%s','%s','%s','%s','%s','%s')
#                     """ % (_id, i,_name, _price, 1, int(time.time()))
#                     # 执行Sql
#                     cursor.execute(sql)
#                     # 提交数据
#                     db.commit()

#                     # 颜色断点
#                     if _id < 37269:
#                         continue

#                     color_arr = getColor(_id)
#                     color_name_arr = color_arr[0]
#                     color_color_arr = color_arr[1]
#                     # print(color_arr)
#                     for a in range(len(color_name_arr)):
#                         print('正在处理id为'+str(_id)+'的车型颜色')
#                         sql = """INSERT INTO think_car_color(
#                             sid,
#                             hex,
#                             color,
#                             status,
#                             update_time) 
#                             VALUES('%s','%s','%s','%s','%s')
#                         """ % (_id, color_color_arr[a],color_name_arr[a], 1, int(time.time()))
#                         # 执行Sql
#                         cursor.execute(sql)
#                         # 提交数据
#                         db.commit()

#     if i % connect_times == 0:
#         cursor.close()
#         db.close()
#         db = None

# 爬取车系数据
# car_list = getSpecAll()


# for index in range(0,len(car_list)):
#     # 车系list
#     model_list = car_list[index]['List'][0]['List']
#     # 品牌首字母
#     letter = car_list[index]['L']
#     # 品牌名称
#     name = car_list[index]['N']
#     # 品牌id
#     id = car_list[index]['I']
    


    # logo = getLogoName(id)
    # # sql存一次品牌
    # sql = """REPLACE INTO think_car_brand(
    #     id,
    #     name,
    #     letter,
    #     logo,
    #     status,
    #     update_time) 
    #     VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
    # """ % (id, name, letter, logo, 1, int(time.time()))
    # # 执行Sql
    # cursor.execute(sql)
    # # 提交数据
    # db.commit() 

    # for i in range(0,len(model_list)):
    #     db = pymysql.connect(**config)
    #     # 车系id
    #     _id = model_list[i]['I']
    #     # 车系名称
    #     _name = model_list[i]['N']
    #     # 如果是停售车跳过
    #     if len(re.compile(pattern='停售').findall(_name)) > 0:
    #         continue
    #     # 否则保存数据库
        
        
    #     # 存储车系sql语句
    #     # sql = """REPLACE INTO think_car_series(
    #     #     id,
    #     #     bid,
    #     #     name,
    #     #     status,
    #     #     update_time) 
    #     #     VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
    #     # """ % (_id, id, _name, 1, int(time.time()))
    #     # # 执行Sql
    #     # cursor.execute(sql)
    #     # # 提交数据
    #     # db.commit() 
    #     # cursor.close()
    #     # 获取车型
    #     with open('1.log','a+') as f:
    #         f.write('已加载到车系id'+str(_id)+'\n\r')
    #     spec = getSpec(_id)

        # for x in range(0,len(spec)):
        #     cursor = db.cursor()
        #     print(spec[x])
        #     __id = spec[x]['I']
        #     __name = spec[x]['N']
        #     price = spec[x]['P']
        #     # 存储车系sql语句
        #     sql = """REPLACE INTO think_car_spec(
        #         id,
        #         sid,
        #         name,
        #         price,
        #         status,
        #         update_time) 
        #         VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
        #     """ % (__id, _id, _name, price, 1, int(time.time()))
        #     # 执行Sql
        #     cursor.execute(sql)
        #     # 提交数据
        #     db.commit() 
        #     cursor.close()
        # db.close()

# db.close()



# 重新获取后request



# res = requests.get(logo_path).content
# with open('./logo/ChsEnFy9lNmAewAlAAA05w4zj8Q592.jpg','wb') as f:
    # f.write(res)
# print(os.path.split('https://img2.autoimg.cn/admdfs/g26/M07/46/D1/ChsEnFy9lNmAewAlAAA05w4zj8Q592.jpg')[1])
# from lxml import etree 
# import requests
# html = "<a href='//car.autohome.com.cn/photolist/spec/color/27647/5707/p1/#pvareaid=3454555' target='_blank' class='athm-carcolor__item'><div class='athm-carcolor__section'><em class='item-all' style='background:#700C2E'></em></div><div class='athm-carcolor__tip'>阿尔法红</div></a><a href='//car.autohome.com.cn/photolist/spec/color/27647/6200/p1/#pvareaid=3454555' target='_blank' class='athm-carcolor__item'><div class='athm-carcolor__section'><em class='item-all' style='background:#345693'></em></div><div class='athm-carcolor__tip'>米萨诺蓝</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#262626'></em></div><div class='athm-carcolor__tip'>火山黑</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#626163'></em></div><div class='athm-carcolor__tip'>维苏威火山灰</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#7F7E83'></em></div><div class='athm-carcolor__tip'>银石灰</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#514640'></em></div><div class='athm-carcolor__tip'>旷野棕</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#1B3361'></em></div><div class='athm-carcolor__tip'>蒙特卡洛蓝</div></a>"
# _element = etree.HTML(html)
# # text = _element.xpath('//a/@href')
# text = requests.get('//car.autohome.com.cn/photolist/spec/color/27647/5707/p1/#pvareaid=3454555').text
# print(text)
