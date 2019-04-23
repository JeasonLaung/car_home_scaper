#coding=utf8
# import requests
# res = requests.get('https://car.autohome.com.cn/duibi/ashx/specComparehandler.ashx?callback=jsonpCallback&type=1&seriesid=5036&format=json&_=1555949768122').text
# print(res)

# #略去model_url和brand_url                                                                                         //这里是"List": [{
#         # "I": 86,
#         # "N": "阿尔法·罗密欧",
#         # "List": [{                                                        3825是这个
#         #     "I": 3825,              -------------------------------------------------------------------------
#         #     "N": "Giulia"                                                                                   |
#         # }, {                                                                                                |      
#         #     "I": 4196,                                                                                      |
#         #     "N": "Stelvio"                                                                                  |
#         # }, {                                                                                                |
#         #     "I": 179,                                                                                       |
#         #     "N": "ALFA 156(停售)"                                                                            |
#         # }, 
# type_url = 'https://car.autohome.com.cn/duibi/ashx/specComparehandler.ashx?callback=jsonpCallback&type=1&seriesid=3825&format=json&_=1555950142261'

# # 只爬取在售的
#                                             #车的id
# detail_url='https://www.autohome.com.cn/spec/27647'

# xpath = '//div[class="athm-carcolor__tip"]/text()'

# 安装lxml
# from lxml import etree 
# html = "<a href='//car.autohome.com.cn/photolist/spec/color/27647/5707/p1/#pvareaid=3454555' target='_blank' class='athm-carcolor__item'><div class='athm-carcolor__section'><em class='item-all' style='background:#700C2E'></em></div><div class='athm-carcolor__tip'>阿尔法红</div></a><a href='//car.autohome.com.cn/photolist/spec/color/27647/6200/p1/#pvareaid=3454555' target='_blank' class='athm-carcolor__item'><div class='athm-carcolor__section'><em class='item-all' style='background:#345693'></em></div><div class='athm-carcolor__tip'>米萨诺蓝</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#262626'></em></div><div class='athm-carcolor__tip'>火山黑</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#626163'></em></div><div class='athm-carcolor__tip'>维苏威火山灰</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#7F7E83'></em></div><div class='athm-carcolor__tip'>银石灰</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#514640'></em></div><div class='athm-carcolor__tip'>旷野棕</div></a><a href='javascript:void(0);' target='_self' class='athm-carcolor__item disabled'><div class='athm-carcolor__section'><em class='item-all' style='background:#1B3361'></em></div><div class='athm-carcolor__tip'>蒙特卡洛蓝</div></a>"
# _element = etree.HTML(html)

# # 获取颜色
# text = _element.xpath('//div[@class="athm-carcolor__tip"]/text()')

# print(text)
# 安装pymysql
# import pymysql 
# #连接数据库
# db = pymysql.connect("120.24.87.1","suibian","123456","online_test")

# #使用cursor()方法创建一个游标对象
# cursor = db.cursor(cursor=pymysql.cursors.DictCursor)

# #使用execute()方法执行SQL语句
# cursor.execute("SELECT * FROM test")

# #使用fetall()获取全部数据
# data = cursor.fetchall()

# #打印获取到的数据
# print(data)

# #关闭游标和数据库的连接
# cursor.close()
# db.close()

#运行结果
# ((1, 'frank', '123'), (2, 'rose', '321'), (3, 'jeff', '666'))

# import pymysql
# import time
# config={
#     "host":"120.24.87.1",
#     "user":"suibian",
#     "password":"123456",
#     "database":"online_test"
# }
# db = pymysql.connect(**config)
# cursor = db.cursor()
# sql = "INSERT INTO test(name,create_time) VALUES('%s',%s)" % ('jack',int(time.time()))
# print(sql)
# cursor.execute(sql)
# db.commit()  #提交数据
# cursor.close()
# db.close()

# import requests
# res = requests.get('https://www.autohome.com.cn/spec/663')
# print(res.status_code)
# print(res.status_code==404)
# with open('') as f:
# 有背景
# https://car2.autoimg.cn/cardfs/series/g26/M05/B0/29/100x100_f40_autohomecar__ChcCP1s9u5qAemANAABON_GMdvI451.png
# 无背景
# https://car2.autoimg.cn/cardfs/series/g26/M05/B0/29/autohomecar__ChcCP1s9u5qAemANAABON_GMdvI451.png
import data
import pymysql
import time
from lxml import etree
# from pypinyin import lazy_pinyin 
config={
    "host":"120.24.87.1",
    "user":"suibian",
    "password":"123456",
    "database":"online_test"
}
# 数据
db = pymysql.connect(**config)
# 数据库指针
cursor = db.cursor()
# 数据
car_list = data.data

for index in range(0,len(car_list)):
    # 车系list
    model_list = car_list[index]['List'][0]['List']
    # 品牌首字母
    letter = car_list[index]['L']
    # 品牌名称
    name = car_list[index]['N']
    # 品牌id
    id = car_list[index]['I']
    #获取图片网址
    html = requests.get('https://car.autohome.com.cn/price/brand-%s.html' % id).text
    _element = etree.HTML(html)
    # 获取颜色
    text = _element.xpath('//div[@class="carbradn-pic"]/img/@href')[0]
    # 返回图片路径
    logo = os.path.split(text)[1]
    # 保存图片
    with open('./logo/%s' % logo,'wb') as f:
        f.write(res)
    
    # sql存一次品牌
    sql = '''REPLACE INTO think_car_brand(
        id,
        name,
        letter,
        logo,
        status
    )
    VALUES(\'%s\',\'%s\',\'%s\',\'%s\',\'%s\')
    ''' % (id, name, letter, )
    # 执行Sql
    cursor.execute(sql)
    # 提交数据
    db.commit() 
    for i in range(0,len(model_list)):
        # 车系id
        _id = model_list[i]['I']
        # 车系名称
        _name = model_list[i]['N']

        print(model_list[i])

cursor.close()
db.close()