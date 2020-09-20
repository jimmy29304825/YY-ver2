import pymysql
import cv2
import numpy as np
import paramiko
from imutils.perspective import four_point_transform
from skimage.filters import threshold_local
import imutils
import datetime
import pandas as pd

class callDB():
    def __init__(self, ip, port, user, password, da_name):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.da_name = da_name
        
        
    def connect_DB(self):
        db = pymysql.connect(host=self.ip,
                             port=self.port,
                             user=self.user,
                             password=self.password,
                             db=self.da_name)
        cursor = db.cursor()
        return db, cursor
    
    
    def get_productionID(self, date):
        try:
            db, cursor = self.connect_DB()
            sql="select schedule_id, concat(demands_id, crop_id) as series_id from crop_schedule where sowing_date = %s;"
            cursor.execute(sql, (date,))
            data = cursor.fetchall()
            print(data)
            res = []
            for i in data:
                res.append({'label':'[' + i[1] + '] ' + i[0] , 'value': i[0]})
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return res
    
    
    def get_productionID_info(self, schedule_id):
        try:
            db, cursor = self.connect_DB()
            sql='''
                select 
                c.name -- 種植品種
                , d.name -- 種法
                , a.sowing_date -- 播種日
                , b.name -- 目標客戶
                , a.require_date -- 預計出貨日
                from crop_schedule a
                inner join customer b on a.cust_id = b.cust_id
                inner join crop_name c on a.crop_id = c.crop_id
                inner join demands d on a.demands_id = d.demands_id
                where schedule_id = %s;
                '''
            cursor.execute(sql, (schedule_id,))
            data = cursor.fetchone()
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return data
    
    def get_view_photo(self, image_id):
        try:
            db, cursor = self.connect_DB()
            sql='''
                select * from raspi_image where image_id = %s;
                '''
            cursor.execute(sql, (image_id, ))
            data = cursor.fetchone()
            frame = data[1]
            piece = data[3]
            nparr = np.frombuffer(frame, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            previewSize = (int(round(frame.shape[1]/15, 0)), int(round(frame.shape[0]/15, 0)))
            previewImage = cv2.resize(frame, previewSize)
        except IndexError:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return previewImage
    
    def get_use_photo(self):
        try:
            db, cursor = self.connect_DB()
            sql='''
                SELECT * FROM yyostech_2.raspi_image order by 3 desc limit 1;
                '''
            cursor.execute(sql)
            data = cursor.fetchone()
            imageid = data[0]
            frame = data[1]
            piece = data[3]
            nparr = np.frombuffer(frame, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return image, imageid, piece
    
    def get_summary(self, schedule_id):
        try:
            db, cursor = self.connect_DB()
            sql='''
                select a.process_id, a.schedule_id, a.image_id, c.piece, a.germination_cnt, 
                concat(b.cust_id, b.demands_id, b.crop_id, b.supplier_id) as series_id
                from yyostech_2.process a
                inner join yyostech_2.crop_schedule b on a.schedule_id = b.schedule_id
                inner join yyostech_2.raspi_image c on a.image_id = c.image_id
                where a.schedule_id=%s
                ''' 
            cursor.execute(sql, (schedule_id, ))
            result = cursor.fetchall()
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return result
    
    def save_germination_record(self, process_record, result_list):
        # process_record = (ProcessNumber, ProductionSerialNumber, PhotoNumber, Slices, GerminationNumber)
        # result_list = ger.result_list
        db, cursor = self.connect_DB()
        try:
            sql_pr='''
            insert into yyostech_2.process (process_id, schedule_id, image_id, piece, germination_cnt)
            values (%s, %s, %s, %s, %s)
            '''
            cursor.execute(sql_pr, process_record)
            print('process ok')
            sql_sp='''
            insert into yyostech_2.sponge (process_id, crop_percentage, is_germinate, position_x, position_y, sp_image)
            values (%s, %s, %s, %s, %s, %s)
            '''
            for i in result_list:
                img = i[4]
                is_success, im_buf_arr = cv2.imencode(".jpg", img)
                byte_im = im_buf_arr.tobytes()
                cursor.execute(sql_sp, (process_record[0], float(i[2]), i[3], i[0], i[1], byte_im))
            print('sponge ok')

            result = db.commit()
        except :
            print('error')
            result = db.rollback()
        finally:
            cursor.close()
            db.close()
        return result
    
    def get_parameter(self, schedule_id):
        db, cursor = self.connect_DB()
        try:
            sql = '''
                SELECT concat(a.demands_id, a.crop_id, a.supplier_id) as series_id, 
                a.schedule_id, b.identify_value, b.thresholds, 
                b.nursery_rate, b.thinning_rate, b.cultivation_rate, a.sowing_date
                FROM yyostech_2.crop_schedule a
                inner join yyostech_2.crop_parameters b on a.demands_id = b.demands_id and a.crop_id = b.crop_id and a.supplier_id = b.supplier_id
                where schedule_id = %s
                order by b.build_datetime desc
                limit 1;
                '''
            cursor.execute(sql, (schedule_id, ))
            data = cursor.fetchone()
#             print(data)
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return data
    
    def get_last_schedule(self):
        db, cursor = self.connect_DB()
        try:
            sql = '''select schedule_id from yyostech_2.crop_schedule order by schedule_id desc limit 1'''
            cursor.execute(sql)
            schedule_id = cursor.fetchone()
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
        return schedule_id
    
    def update_schedule(self, df_use):
        db, cursor = self.connect_DB()
        try:
            sql='''
                insert into yyostech_2.crop_schedule (schedule_id, cust_id, demands_id, crop_id, supplier_id, sowing_date, require_date) 
                    value (%s, %s, %s, %s, %s, %s, %s)
                '''
            for i in range(len(df_use)):
                print(df_use.iloc[i]['生產序號'])

                schedule_id = df_use.iloc[i]['生產序號']
                cust_id = df_use.iloc[i]['編號'][0]
                demands_id = df_use.iloc[i]['編號'][1]
                crop_id = df_use.iloc[i]['編號'][2:5]
                supplier_id = df_use.iloc[i]['編號'][5]
                sowing_date = str(df_use.iloc[i]['播種日期'])
                require_date = str(df_use.iloc[i]['交貨日'])
                try:
                    cursor.execute(
                        sql, 
                        (
                            schedule_id,
                            cust_id,
                            demands_id,
                            crop_id,
                            supplier_id,
                            sowing_date,
                            require_date
                        )
                    )
                except:
                    # 排除沒有在參數表的資料
                    continue
            db.commit()
            print('==========================')
            print('done')
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
            
            
    def save_artificial_judgment(self, sponge_id, judge_result):
        db, cursor = self.connect_DB()
        create_datetime = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        try:
            sql='''
                insert into yyostech_2.artificial_judgment (sponge_id, create_datetime, judge_result) 
                    value (%s, %s, %s)
                '''
            cursor.execute(sql,(sponge_id, create_datetime, judge_result))
            db.commit()
            print('==========================')
            print('done')
        except:
            print('error')
            db.rollback()
        finally:
            cursor.close()
            db.close()
            
    def get_lastday(self, seriesID, date):
        db, cursor = self.connect_DB()
        try:
            sql='''
                SELECT sum(a.germination_cnt) as germination_cnt, sum(b.piece) as piece 
                FROM yyostech_2.process a
                inner join yyostech_2.raspi_image b on a.image_id = b.image_id
                where schedule_id in (select schedule_id
                                        from yyostech_2.crop_schedule
                                        where concat(demands_id, crop_id, supplier_id) = %s
                                        and sowing_date = %s)

                '''
            cursor.execute(sql,(seriesID, date))
            data = cursor.fetchone() 
        finally:
            cursor.close()
            db.close()
        return data
    
    
    def get_single_sponge(self, series):
        db, cursor = self.connect_DB()
        check_list = []
        result_table = None
        try:
            sql='''
                select 
                a.sponge_id, 
                a.sp_image, 
                concat(c.demands_id, c.crop_id) as series, 
                a.crop_percentage, 
                abs(
                    a.crop_percentage - (select identify_value 
                                            from crop_parameters 
                                            where concat(demands_id, crop_id) = %s)
                ) as distance
                from sponge a
                inner join process b on a.process_id = b.process_id
                inner join crop_schedule c on b.schedule_id = c.schedule_id
                left join artificial_judgment d on a.sponge_id = d.sponge_id
                where 1 = 1
                and concat(c.demands_id, c.crop_id) = %s
                and d.sponge_id is null
                order by 5
                limit 8;
                '''
            cursor.execute(sql, (series, series))
            result = cursor.fetchall()
            
            sql='''
                select 
                concat(b.demands_id, b.crop_id) as series
                , sum(a.germination_cnt) as identify_cnt
                , c.judge_cnt
                from process a
                inner join crop_schedule b on a.schedule_id = b.schedule_id
                left join (
                    select 
                    concat(b.demands_id, crop_id) as series
                    , count(d.judge_id) as judge_cnt
                    from process a
                    inner join crop_schedule b on a.schedule_id = b.schedule_id
                    inner join sponge c on a.process_id = c.process_id
                    left join artificial_judgment d on c.sponge_id = d.sponge_id
                    group by concat(b.demands_id, crop_id)
                        ) c on concat(b.demands_id, b.crop_id) = c.series
                group by concat(b.demands_id, crop_id);
                '''
            cursor.execute(sql)
            result_table = cursor.fetchall()
            
            for i in result:
                nparr = np.frombuffer(i[1], np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                check_list.append([i[0], frame, i[2], i[3], i[4]])
        except:
            print('error')
        finally:
            cursor.close()
            db.close()
            return check_list, result_table

    def get_dashboard_data(self, start, end):
        db, cursor = self.connect_DB()
        try:
            sql='''
                select 
                a.schedule_id as `生產序號`
                , concat(demands_id, a.crop_id, supplier_id) as `作物編號`
                , sowing_date as `播種日期`
                , require_date as `出貨日期`
                , b.`name` as `品種名稱`
                , d.`name` as `客戶名稱`
                , sum(f.piece) * 96 as `播種數量`
                , (sum(c.germination_cnt)+(case when add_ger_cnt is not null then add_ger_cnt else 0 end)) as `發芽數量`
                , (sum(c.germination_cnt)+(case when add_ger_cnt is not null then add_ger_cnt else 0 end)) / (sum(c.piece) * 96) as `發芽率`
                from crop_schedule a
                inner join crop_name b on b.crop_id = a.crop_id
                inner join process c on a.schedule_id = c.schedule_id
                inner join customer d on d.cust_id = a.cust_id
                left join (
	                select 
	                c.schedule_id
	                , sum(a.judge_result) as add_ger_cnt
	                from artificial_judgment a
	                inner join sponge b on a.sponge_id = b.sponge_id
	                inner join process c on b.process_id = c.process_id
	                group by  c.schedule_id
                ) e on e.schedule_id = a.schedule_id
                inner join raspi_image f on c.image_id = f.image_id
                where a.sowing_date >= %s and a.sowing_date <= %s
                group by a.schedule_id
                , concat(demands_id, a.crop_id, supplier_id)
                , sowing_date
                , require_date
                , b.`name`
                order by a.schedule_id;
                '''
            cursor.execute(sql,(start, end))
            data = cursor.fetchall() 
            
        except:
            print('error')
        finally:
            cursor.close()
            db.close()
            return data
        
    def get_views(self, datetimes, schedule_id):
        db, cursor = self.connect_DB()
        try:
            if datetimes == '':
                sql=f'''
                    SELECT a.process_id, b.piece, a.germination_cnt, a.image_id, b.image, b.create_datetime
                    FROM yyostech_2.process a
                    inner join yyostech_2.raspi_image b on a.image_id = b.image_id
                    where schedule_id = '{schedule_id}'
                    order by b.image, b.create_datetime
                    limit 1;
                    '''
                cursor.execute(sql)
            else:
                sql=f'''
                    SELECT a.process_id, b.piece, a.germination_cnt, a.image_id, b.image, b.create_datetime
                    FROM yyostech_2.process a
                    inner join yyostech_2.raspi_image b on a.image_id = b.image_id
                    where schedule_id = '{schedule_id}'
                    and b.create_datetime < '{datetimes}'
                    order by b.image, b.create_datetime
                    limit 1;
                    '''
                cursor.execute(sql)
            data = cursor.fetchone() 
            if data != None:
                datetimes = str(data[5])
                nparr = np.frombuffer(data[4], np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                frame = cv2.resize(frame, (960, int((960/frame.shape[1])*frame.shape[0])), interpolation=cv2.INTER_CUBIC)
                data_list = [data[0], data[1], data[2], data[3], str(data[5])]
            else:
                frame = None
                data_list = None
                print('empty')
            
        except:
            print('error')
        finally:
            cursor.close()
            db.close()
            return frame, data_list
    
class par():
    def __init__(self, ip, port, username, password):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        
    def connect_raspi(self, photo_id, piece):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip,self.port,self.username, self.password)  # 網路連線設定
        stdin, stdout, stderr = ssh.exec_command("python3 /home/pi/Desktop/test.py %s %s" % (photo_id, piece))  # 呼叫執行檔並傳送參數
        paramiko_result = stdout.readlines()  # 回傳產出結果
        print(paramiko_result, photo_id, piece)
        ssh.close()
        return paramiko_result
    
    
class germination():
    def __init__(self, series_id, germination_percent, pieces):
        self.series_id = series_id
        self.germination_percent = germination_percent
        self.result_list = []  #預設結果儲存物件
        self.pieces = pieces
        self.dict_pieces = {
            '4':[range(0,8), range(0,12)],
            '3':[range(0,8), range(12,24)],
            '2':[range(8,16), range(0,12)],
            '1':[range(8,16), range(12,24)],
        }
        
    def convert_image(self, image):  # 取出海綿的範圍，回傳照片與預覽圖(含點線)
        img_preview = image.copy()  # 複製影像
        paper = cv2.GaussianBlur(image, (5, 5), 0)  # 糊化 消除雜訊
        ret, thresh_gray = cv2.threshold(
            cv2.cvtColor(paper, cv2.COLOR_BGR2GRAY),  # 轉換灰階
            100, 255, cv2.THRESH_BINARY  # 二元化
        )
        # contours, hier = cv2.findContours(thresh_gray, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)  #　尋找邊界，cv2.RETR_EXTERNAL不找被框住的範圍內（但不知道為什麼還是會抓．．．）
        _, contours, hier = cv2.findContours(thresh_gray, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)  #　尋找邊界，cv2.RETR_EXTERNAL不找被框住的範圍內（但不知道為什麼還是會抓．．．）
        for c in contours:
            rect = cv2.minAreaRect(c)  # 找中心點
            box = cv2.boxPoints(rect)  # 找四頂點
            box = np.int0(box)  # 資料型態轉換
            x = []  # x軸
            y = []  # y軸
            for i in range(0, 4):
                x.append(box[i][0])  # 抓四頂點的X
                y.append(box[i][1])  # 抓四頂點的Y
            if (max(x)-min(x)) > 2000 and (max(y)-min(y)) > 1000:  # 圖形符合整塊海綿的大小才取用
                global tar
                tar = box
                cv2.drawContours(image, [np.int0(tar)], 0, (0, 255, 0),5)  # 畫出邊界(可以不用)
                M = cv2.moments(c)  # 計算動差函數
                cX = int(M["m10"] / M["m00"])  # 尋找中心點Ｘ軸
                cY = int(M["m01"] / M["m00"])  # 尋找中心點Ｙ軸
                cv2.circle(img_preview, (cX, cY), 10, (1, 227, 254), 50)  # 標示出中心點位置
                sumxy = []
                for i in c:
                    sumxy.append(i[0][0]+i[0][1])
                rb = tuple(c[sumxy.index(max(sumxy))][0].tolist())
                tl = tuple(c[sumxy.index(min(sumxy))][0].tolist())
                divxy = []
                for i in c:
                    divxy.append(i[0][0]-i[0][1])
                rt = tuple(c[divxy.index(max(divxy))][0].tolist())
                lb = tuple(c[divxy.index(min(divxy))][0].tolist()) 
                cv2.circle(img_preview, rb, 20, (255, 0, 0), 5)
                cv2.circle(img_preview, tl, 20, (255, 0, 0), 5)
                cv2.circle(img_preview, rt, 20, (255, 0, 0), 5)
                cv2.circle(img_preview, lb, 20, (255, 0, 0), 5)
                break
        point = [rb, tl, rt, lb]
        rect = four_point_transform(image, np.array(point))  #用目標四頂點拉伸圖片
        image_convert = cv2.resize(rect,(100*24, 100*16))  # 調整影像大小
        return image_convert, img_preview
    
    def binary(self, image_convert):  # 圖像二元化
        kernel_size = (9, 9)  # 高斯模糊矩陣大小
        sigma = 6  # 高斯模糊標準差參數(0=自動)
        thresholds = 120
        grayImage = cv2.cvtColor(image_convert, cv2.COLOR_BGR2GRAY)  # gray(0-255) 圖像轉換灰階
        GaussianImage = cv2.GaussianBlur(grayImage, kernel_size, sigma)  # GaussianBlur  圖校進行模糊化(高斯)
        block_size = 79
        local_thresh1 = threshold_local(GaussianImage, block_size, offset=20, method='gaussian')
        binary_local1 = GaussianImage > local_thresh1
        return binary_local1
    
    def caculate(self, binary_image, convert_image):
        # 計算發芽率
        plus = 100  # 長寬設定 100 * 100
        germination_sum = 0
        for i in range(self.pieces):
            for x in self.dict_pieces[str(i+1)][0]:
                    for y in self.dict_pieces[str(i+1)][1]:
                        top, left = x*plus, y*plus
                        slice_img = convert_image[top:top+plus, left:left+plus]
                        slice_img_binary = binary_image[top:top+plus, left:left+plus]
                        caculateImg = slice_img_binary[10:90, 10:90]  # 邊緣10%不計算發芽率
                        slice_percent =  round(sum(sum(caculateImg == 0))/64, 2)  # 計算黑色比例(作物占比)
                        if slice_percent > self.germination_percent:
                            is_germination = 1
                            germination_sum += 1
                        else:
                            is_germination = 0
                        self.result_list.append([x, y, slice_percent, is_germination, slice_img])
        germination_rate = round((germination_sum / (96*self.pieces))*100, 2)
        return germination_rate, germination_sum
    
    def identify(self, image):
        convert_image, convert_image_preview = self.convert_image(image)
        binary_image = self.binary(convert_image)
        caculate = self.caculate(binary_image, convert_image)
        return caculate