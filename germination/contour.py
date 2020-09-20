import cv2
import numpy as np
from imutils.perspective import four_point_transform
from matplotlib import pyplot as plt

imgPath="./block/1G4-9.jpg"  # 檔案路徑
img = cv2.imread(imgPath,-1)  # 讀取影像

img_copy = img.copy()  # 複製影像
paper = cv2.GaussianBlur(img_copy, (55, 55), 0)  # 糊化 消除雜訊
ret, thresh_gray = cv2.threshold(
    cv2.cvtColor(paper, cv2.COLOR_BGR2GRAY),  # 轉換灰階
    150, 255, cv2.THRESH_BINARY  # 二元化
)
erosion = cv2.erode(thresh_gray,(39, 39),iterations = 3)  # 腐蝕，排除更多雜訊
image, contours, hier = cv2.findContours(erosion, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)  #　尋找邊界，cv2.RETR_EXTERNAL不找被框住的範圍內（但不知道為什麼還是會抓．．．）

for c in contours:
    rect = cv2.minAreaRect(c)  # 找中心點
    box = cv2.boxPoints(rect)  # 找四頂點
    # convert all coordinates floating point values to int
    box = np.int0(box)  # 資料型態轉換
    x = []  # x軸
    y = []  # y軸
    for i in range(0, 4):
        x.append(box[i][0])  # 抓四頂點的X
        y.append(box[i][1])  # 抓四頂點的Y
    if (max(x)-min(x)) > 2000 and (max(y)-min(y)) > 1000:  # 圖形符合整塊海綿的大小才取用
        global tar
        tar = box
        print(tar)
        # draw a green 'nghien' rectangle
        cv2.drawContours(img_copy, [tar], 0, (0, 255, 0),5)  # 畫出邊界(可以不用)
        M = cv2.moments(c)  # 計算動差函數
        cX = int(M["m10"] / M["m00"])  # 尋找中心點Ｘ軸
        cY = int(M["m01"] / M["m00"])  # 尋找中心點Ｙ軸
        cv2.circle(img_copy, (cX, cY), 10, (1, 227, 254), 50)  # 標示出中心點位置
        break
        
plt.imshow(img_copy)  # 顯示框出來的圖形與中心點  

rect = four_point_transform(img, np.array(tar))  #用目標四頂點拉伸圖片
plt.imshow(rect)  # 顯示用四頂點轉換拉伸後的圖