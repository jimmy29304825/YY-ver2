import pymysql
import cv2
import numpy as np
import paramiko
from datetime import datetime
from imutils.perspective import four_point_transform
from scipy.stats import gaussian_kde
import imutils

class connect():
    def __init__(self, ip, port, username, password, database):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        
    def connect_DB(self):
        db = pymysql.connect(host=self.ip,
                             port=self.port,
                             user=self.username,
                             password=self.password,
                             db=self.database)
        cursor = db.cursor()
        return db, cursor
    
    def user_follow(self, line_id, user_name, right_id):
        try:
            db, cursor = self.connect_DB()
            sql_insert_blob_query = """select `line_id` from user_profile where `line_id` = %s"""
            insert_blob_tuple1 = (line_id, )
            cursor.execute(sql_insert_blob_query, insert_blob_tuple1)
            data = cursor.fetchone()
            if data == None:
                # user_profile
                sql_insert_blob_query = """INSERT INTO user_profile (`line_id`, `user_name`, `right_id`) VALUES (%s, %s, %s)"""
                insert_blob_tuple2 = (line_id, user_name, right_id)
                cursor.execute(sql_insert_blob_query, insert_blob_tuple2)
                # 確認執行上述指令
                result = db.commit()
            else:
                result = 'user exist'
        finally:
            # 關閉資料庫連線
                db.close()
        return result


    def get_menu_id(self, line_id):
        try:
            db, cursor = self.connect_DB()
            # user_profile
            sql_insert_blob_query = """select b.menu_id from user_profile a inner join user_right b on a.right_id = b.right_id and a.line_id = %s"""
            insert_blob_tuple = (line_id, )
            cursor.execute(sql_insert_blob_query, insert_blob_tuple)
            data = cursor.fetchone()
        finally:
            # 關閉資料庫連線
            db.close()
        return data[0]


    def convert_image_to_byte(self, image):
        is_success, im_buf_arr = cv2.imencode(".jpg", image)
        byte_im = im_buf_arr.tobytes()
        return byte_im
    
    
    def get_series(self):
        try:
            db, cursor = self.connect_DB()
            cursor.execute('''select * from series_data''')
            series_data = cursor.fetchall()
        finally:
            db.close()
        return series_data
        
        
    def save_process(self, gerData):
        try:
            db, cursor = self.connect_DB()
            sql = """INSERT INTO process_record (process_id, series_id, seed_numbers, identify_date, saw_date) 
                                        VALUES(%s, %s, %s, %s, %s);"""
            data = (gerData['process_id'], gerData['series_id'], gerData['seed_numbers'], gerData['identify_date'], gerData['saw_date'])
            cursor.execute(sql, data)
            result = db.commit()
        finally:
            db.close()
        return result
    
        
    def get_raspi_data(self, photo_id):
        try:
            db, cursor = self.connect_DB()
            cursor.execute("SELECT * from raspi_data where photo_id = %s" % repr(photo_id))
            data = cursor.fetchone()
            frame = data[1]
            nparr = np.fromstring(frame, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            previewSize = (int(round(frame.shape[1]/15, 0)), int(round(frame.shape[0]/15, 0)))
            previewImage = cv2.resize(frame, previewSize)
            cv2.imwrite(".\YY\preview.jpg", previewImage)
        finally:
            db.close()
        return frame
    
    
    def save_germination_record(self, germination_record, result_list):
        try:
            db, cursor = self.connect_DB()
            germination_record[3] = self.convert_image_to_byte(germination_record[3])
            sql_germination = """INSERT INTO germination_record (germination_id, process_id, photo_id, image, germination_rate, sponge_cnt) 
                                        VALUES(%s, %s, %s, %s, %s, %s);"""
            cursor.execute(sql_germination, tuple(germination_record))
            sql_sponge = """INSERT INTO sponge_record (germination_id, x_position, y_position, plant_percent, is_germination, image) 
                                        VALUES(%s, %s, %s, %s, %s, %s);"""
            germination_id = germination_record[0]
            for i in result_list:
                i[4] = self.convert_image_to_byte(i[4])
                cursor.execute(sql_sponge, (germination_id, i[0], i[1], float(i[2]), i[3], i[4]))
            result = db.commit()
        finally:
            db.close()
        return result
    
    
    def get_result(self, process_id):
        try:
            db, cursor = self.connect_DB()
            cursor.execute('''select a.process_id, 
                                count(distinct b.germination_id) as germination_cnt, 
                                count(distinct c.sponge_id) as sponge_cnt, 
                                count(if(is_germination = 1, 1, null)) as is_ger, 
                                count(if(is_germination = 0, 1, null)) as no_ger,
                                round((count(if(is_germination = 1, 1, null)) / count(distinct c.sponge_id))*100, 2) as percent
                                from process_record a
                                inner join germination_record b on a.process_id = b.process_id
                                inner join sponge_record c on c.germination_id = b.germination_id
                                where a.process_id = %s
                                group by a.process_id
                                ''' % repr(process_id))
            process_result = cursor.fetchone()
        finally:
            db.close()
        return process_result
    
    def artificial_identify(self, series_id):
        try:
            db, cursor = self.connect_DB()
            cursor.execute('''select d.sponge_id, d.image, a.series_id, a.germination_percent, b.process_id, 
                                     c.germination_id, d.plant_percent, abs(d.plant_percent - a.germination_percent) as `range`
                                from yyostech.series_data a
                                inner join yyostech.process_record b on b.series_id = a.series_id
                                inner join yyostech.germination_record c on b.process_id = c.process_id
                                inner join yyostech.sponge_record d on d.germination_id = c.germination_id
                                left join yyostech.artificial_identify e on d.sponge_id = e.sponge_id
                                where a.series_id = %s
                                and e.sponge_id is null
                                order by 7 
                                limit 1;'''% repr(series_id))
            artificial_result = cursor.fetchone()
        finally:
            db.close()
        return artificial_result
    
    
    def save_artificial_result(self, series_id, line_id, artificial_result):
        try:
            db, cursor = self.connect_DB()
            
            sql_sponge = """INSERT INTO artificial_identify (sponge_id, line_id, is_germination, identify_date) 
                                        VALUES(%s, %s, %s, %s);"""

            artificial_tuple = (artificial_result[0], line_id, artificial_result[1], str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            cursor.execute(sql_sponge, artificial_tuple)
            result = db.commit()
        finally:
            db.close()
        return result
    
    
class par():
    def __init__(self, ip, port, username, password):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        
    def connect_raspi(self, photo_id):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip,self.port,self.username, self.password)  # 網路連線設定
        stdin, stdout, stderr = ssh.exec_command("python3 /home/pi/Desktop/test.py %s" % photo_id)  # 呼叫執行檔並傳送參數
        paramiko_result = stdout.readlines()  # 回傳產出結果
        print(paramiko_result)
        ssh.close()
        return paramiko_result
    

class germination():
    def __init__(self, series_id, thershold, percent):
        self.series_id = series_id  # 手動輸入品種編號
        self.thershold = thershold  # 從SQL抓取二元化參數
        self.percent = percent  # 從SQL抓取判斷閾值
        self.result_list = []  #預設結果儲存物件
        self.xy = (22, 14)
        
        
    def convert_photo(self, slice_img):  # 圖片換(灰階、高斯模糊、二元化)，計算發芽比例
        kernel_size = (3, 3)  # 高斯模糊矩陣大小
        sigma = 3  # 高斯模糊標準差參數(0=自動)
        grayImage = cv2.cvtColor(slice_img, cv2.COLOR_BGR2GRAY)  # gray(0-255) 圖像轉換灰階
        GaussianImage = cv2.GaussianBlur(grayImage, kernel_size, sigma)  # GaussianBlur  圖校進行模糊化(高斯)
        (thresh, blackAndWhiteImage) = cv2.threshold(GaussianImage,  self.thershold, 255, cv2.THRESH_BINARY)  
        # black and white(0, 255)  圖像透過thershold閾值進行二元化 
        caculateImg = blackAndWhiteImage[10:90, 10:90]  # 邊緣10%不計算發芽率
        slice_percent =  round(sum(sum(caculateImg == 0))/64, 2)  # 計算黑色比例(作物占比)
        if slice_percent >= self.percent:  # 判斷是否發芽
            is_germination = 1
        else: 
            is_germination = 0
        result = [slice_percent, is_germination]  
        return result  # 結果回傳(作物比例、是否發芽)
    
    
    def caculate(self):  # 計算整片作物的發芽率
        germination_sum = 0
        for i in self.result_list:
            germination_sum += i[3]
        germination_rate = round((germination_sum / (self.xy[0]*self.xy[1]))*100, 2)
        return germination_rate
    
    
    def resize_photo(self, img):
        img_blank = np.zeros((img.shape[0],img.shape[1],3), np.uint8)
        img_blank.fill(255)
        # 使用縮圖以減少計算量
        img_small = imutils.resize(img, width=640)

        # 轉換至 HSV 色彩空間
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)

        # 取出飽和度
        saturation = hsv[:, :, 1]
        saturation_small = hsv_small[:, :, 1]

        # 取出明度
        value = hsv[:,:,2]
        value_small = hsv_small[:,:,2]

        # 綜合飽和度與明度
        sv_ratio = 0.5
        sv_value = cv2.addWeighted(saturation, sv_ratio, value, 1-sv_ratio, 0)
        sv_value_small = cv2.addWeighted(saturation_small, sv_ratio, value_small, 1-sv_ratio, 0)

        # 使用 Kernel Density Estimator 計算出分佈函數
        density = gaussian_kde(sv_value_small.ravel(), bw_method=0.2)

        # 找出 PDF 中第一個區域最小值（Local Minimum）作為門檻值
        step = 0.5
        xs = np.arange(0, 256, step)
        ys = density(xs)
        cum = 0
        threshold_value = 0
        for i in range(1, 250):
            cum += ys[i-1] * step
            if (cum > 0.02) and (ys[i] < ys[i+1]) and (ys[i] < ys[i-1]):
                threshold_value = xs[i]
                break
        # 以指定的門檻值篩選區域
        _, threshold = cv2.threshold(sv_value, threshold_value, 255.0, cv2.THRESH_BINARY)

        # 去除微小的雜訊
        kernel_radius = int(img.shape[1]/100)
        kernel = np.ones((kernel_radius, kernel_radius), np.uint8)
        threshold = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)
        threshold = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)

        # 產生等高線
        contours, hierarchy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 建立除錯用影像
        img_debug = img.copy()

        # 線條寬度
        line_width = int(img.shape[1]/1000)

        # 以藍色線條畫出所有的等高線
        cv2.drawContours(img_debug, contours, -1, (255, 0, 0), line_width)
        img_group = cv2.drawContours(img_blank, contours, -1, (255, 0, 0), line_width)

        # 處理藍色邊框
        # cv2.rectangle (img_group, Point(0, 0), Point(2729, 3921), Scalar(0, 255, 255), 2, 8, 0);
        img_group = cv2.rectangle(img_group, (0, 0), (img.shape[1], img.shape[0]), (255, 255, 255), 20)

        # 把邊緣圖像重新處理
        edged = cv2.Canny(img_group, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        # 把邊緣圖像重新分層
        contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[1]
        approx = cv2.approxPolyDP(cnt, 30, True).tolist()
        approx = [j for sub in approx for j in sub]
        rect = four_point_transform(img, np.array(approx))
        image_convert = cv2.resize(rect,(100*self.xy[0], 100*self.xy[1]))
        return image_convert
    
    
    def get_photo(self, image_convert):  # 拍攝照片並轉換、計算、裁切
        self.result_list = []  # 重製結果暫存清單
        print('裁切照片')
#         image_convert = self.resize_photo(image_convert)
        if len(image_convert) == 4:
            return 'please retake photo'
        else:
            top = 0  # 最上面(+h)
            left = 0  # 最左邊(+w)
            plus = 100  # 長寬設定 100 * 100
            for i in range(self.xy[1]):  # 等比例裁切每一株的照片
                for j in range(self.xy[0]):
                    slice_img = image_convert[top:top+plus, left:left+plus]
                    ans = self.convert_photo(slice_img)  # 使用convert_photo運算
                    result = [i, j, ans[0], ans[1], slice_img]  # 儲存單個結果
                    self.result_list.append(result)  # 彙整整片結果至暫存清單
                    left = left + plus
                top = top +plus
                left = 0  # 算完一列重製(like a打字機)
            result = self.caculate()  # 使用caculate計算整片發芽率
            return result
       
       
    def __str__(self):
        return "作物編號: %s\n閾值參數: %s\n判斷條件: %s\n結果暫存清單: 共%s筆數據(詳細請看self.result_list)" % (self.series_id, self.thershold, self.percent, len(self.result_list))