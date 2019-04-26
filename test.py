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
btime = time.time()
max_id = 0
current_id = 0
start_time = time.time()
reconnect_time = 60
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
    global start_time
    global reconnect_time
    res0 = getSpecAll()
    db = pymysql.connect(**config)
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    for index0 in range(0,len(res0)):
        # 重连
        if time.time() - start_time > reconnect_time:
            cursor.close()
            db.close()
            start_time = time.time()
            time.sleep(1)
            db = pymysql.connect(**config)
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)

        brand = res0[index0]
        brand_id = brand['I']
        brand_name = brand['N']
        brand_logo = getLogoName(brand_id)
        brand_letter = brand['L']
        factory_arr = brand['List']
        sql = """REPLACE INTO
            think_car_brand(
                id,
                name,
                logo,
                letter,
                update_time
            )
            VALUES('%s','%s','%s', '%s')
        """ % (brand_id, brand_name,brand_logo, brand_letter, time.time())
        cursor.execute(sql)
        db.commit()

        for index1 in range(0,len(factory_arr)):
            
            factory_name = factory_arr[index1]['N']
            factory_id = factory_arr[index1]['I']
            if re.search(r'进口', factory_name) == None:
                factory_type = 0
            else:
                factory_type = 1

            series_arr = factory_arr[index1]['List']
            
            sql = """REPLACE INTO 
                think_car_factory(
                    id,
                    name,
                    type,
                    update_time
                )
                VALUES('%s','%s','%s','%s')
            """ % (factory_id,factory_name, factory_type, time.time())
            cursor.execute(sql)
            db.commit()

            for series in series_arr:
                series_id = series['I']
                series_name = series['N']
                res = re.search('停售',series_name)
                if res == None: 
                    series_status = 0
                else: 
                    series_status = 1
                    
                # spec_price = spec['P']
                sql = """REPLACE INTO 
                    think_car_series(
                        id,
                        fid,
                        name,
                        status,
                        update_time,
                        bid
                    )
                    VALUES('%s','%s','%s','%s','%s','%s')
                """ % (series_id, factory_id, series_name, series_status, time.time(),brand_id)
                cursor.execute(sql)
                db.commit()
                print('完成车系：'+series_name + str(series_id) +'插入')

            print('完成厂家：'+factory_name + str(factory_id) +'的车系插入')

        print('完成品牌：'+brand_name + str(brand_id) +'厂家处理')

    print('完成所有品牌处理')

    cursor.close()
    db.close()

    return True


def actionGetSpec():
    global start_time
    global current_id
    global max_id
    global reconnect_time
    db = pymysql.connect(**config)
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    
    # 获取最大id
    if max_id == 0:
        sql = """
            SELECT 
                id 
            FROM 
                think_car_series
            ORDER BY 
                id desc
            LIMIT 1
        """
        cursor.execute(sql)
        res = cursor.fetchall()
        max_id = res[0]['id']

    #找到最大的
    # current_id = i or current_id
    while current_id <= max_id+1:
        current_id = current_id + 1
        # 重连
        if time.time() - start_time > reconnect_time:
            cursor.close()
            db.close()
            start_time = time.time()
            time.sleep(1)
            db = pymysql.connect(**config)
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
        sql = """
            SELECT 
                id
            FROM
                think_car_series
            WHERE
                id >= '%s'
            ORDER BY
                id ASC
            LIMIT 1
        """ % (current_id)
        cursor.execute(sql)
        res = cursor.fetchall()
        if len(res) == 0:
            print('完成车型插入')
            return
        current_id = res[0]['id']
        # if len(res) == 0:
        #     continue
        # 存在id
        spec_arr = getSpec(current_id)        
        print('开始进行车系为'+str(current_id)+'的处理')
        print(spec_arr)
        if len(spec_arr) == 0:
            continue
        
        for _spec in spec_arr:
            # 不是在售车型
            if _spec['I'] != 1:
                continue
            specs = _spec['List']
            
            for spec in specs:
                spec_id = spec['I']
                spec_name = spec['N']
                spec_price = spec['P']
                sql = """
                    REPLACE INTO 
                    think_car_spec(
                        id,
                        sid,
                        name,
                        price,
                        status,
                        update_time
                    )
                    VALUES('%s','%s','%s','%s','%s','%s')
                """ % (spec_id,current_id,spec_name,spec_price,1,time.time())
                cursor.execute(sql)
                db.commit()

                print('完成车型'+spec_name+str(spec_id)+'插入')
            print('完成车系id为'+str(current_id)+'的车型插入')

    # 结束
    max_id = 0
    current_id = 0 
    print('完成所有车型插入')



# 完成重置最大值
# cid = 0
# 爬取颜色
def actionGetColor():
    global start_time
    global current_id
    global max_id
    global reconnect_time
    db = pymysql.connect(**config)
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    

    if max_id == 0:
        sql = """
            SELECT 
                id 
            FROM 
                think_car_spec
            ORDER BY 
                id desc
            LIMIT 1
        """
        cursor.execute(sql)
        res = cursor.fetchall()
        print(max_id)
        max_id = res[0]['id']

    while current_id <= max_id+1:
        # 重连
        current_id = current_id + 1
        if time.time() - start_time > reconnect_time:
            cursor.close()
            db.close()
            start_time = time.time()
            time.sleep(1)
            db = pymysql.connect(**config)
            cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
        sql = """
            SELECT 
                id,
                name
            FROM 
                think_car_spec 
            where 
                id >= %s
            order by
                id asc
            limit 1
        """ % current_id
        cursor.execute(sql)
        res = cursor.fetchall()
        if len(res) == 0:
            print('完成颜色插入')
            return
        current_id = res[0]['id']
        spec_name = res[0]['name']
        # if len(res) == 0:
        #     continue

        print('正在处理id为'+str(current_id)+'的车型颜色')
        color_arr = getColor(current_id)
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
            """ % (current_id, color_color_arr[a],color_name_arr[a], 1, int(time.time()))
            # 执行Sql
            cursor.execute(sql)
            # 提交数据
            db.commit()
            print('颜色'+color_color_arr[a]+color_name_arr[a]+'插入成功')
        print('车型'+spec_name+str(current_id)+'插入成功')
    print('颜色已经全部插入成功')
    

    
if __name__ == '__main__':
    # 1
    actionGetSeries()
    # 2
    # try:
    #     actionGetSpec()
    # except:
    #     # 异常重连
    #     print('异常重连')
    #     print('current_id',str(current_id))
    #     print('start_time',str(start_time))
    #     time.sleep(2)
    #     actionGetSpec()
    # 3
    # try:
    #     actionGetColor()
    # except:
    #     # 异常重连
    #     print('异常重连')
    #     print('current_id',str(current_id))
    #     print('start_time',str(start_time))
    #     time.sleep(2)
    #     actionGetColor()
    # print('全部完成耗时'+str(time.time()-btime))

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
