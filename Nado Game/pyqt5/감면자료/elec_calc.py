import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5 import uic
from datetime import datetime


def resource_path(relative_path):
    base_path = getattr(sys, "_MAIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path("전기감면_mainwindow.ui")
print(form)
form_class = uic.loadUiType(form)[0]

now = datetime.now()
yyyymm = now.strftime("%Y")+now.strftime("%m")+'월'
yyyy = now.strftime("%Y")

LE =  [
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/한전부과자료',
    'D:/과장/1 1 부과자료/'+yyyy+'년/Templates/Elec_Template_File_for_XPERP_upload.xls',
    'D:/과장/1 1 부과자료/'+yyyy+'년/'+yyyymm+'/xperp_감면자료'
    ]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.LE = LE
        # print(len(self.LE), self.LE, LE)
        self.setupUi(self)

        self.lineEdit.setText(LE[0])
        self.lineEdit_2.setText(LE[1])
        self.lineEdit_3.setText(LE[2])
        self.lineEdit_4.setText(LE[3])

        self.pushButton.clicked.connect(self.add_file)
        self.pushButton_2.clicked.connect(self.add_file)
        self.pushButton_3.clicked.connect(self.add_file)
        self.pushButton_4.clicked.connect(self.add_file)
        self.pushButton_5.clicked.connect(self.start)

    @pyqtSlot()
    def add_file(self):

        sname = self.sender().text()

        if sname == '복지할인':
            init_dir = self.LE[0]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit.setText(fname[0])
            else:
                self.lineEdit.setText(LE[0])

        elif sname == '할인종류':
            init_dir = self.LE[1]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit_2.setText(fname[0])
            else:
                self.lineEdit_2.setText(LE[1])
        
        elif sname == 'Template':
            init_dir = self.LE[2]
            fname = QFileDialog.getOpenFileName(self, '엑셀 데이타 파일을 선택하세요', init_dir, 'All Files (*) :: Excel (*.xls *.xlsx)')
            if len(fname[0]) != 0:
                self.lineEdit_3.setText(fname[0]) 
            else: 
                self.lineEdit_3.setText(LE[2])
        
        else:
            init_dir = self.LE[3]
            fname = QFileDialog.getExistingDirectory(self, '저장 Direttory를 선택하새요', init_dir)
            #print(len(fname))
            if len(fname) != 0:
                self.lineEdit_4.setText(fname)
            else:
                self.lineEdit_4.setText(LE[3])

    # 계산 시작
    def start(self):
        # 각 옵션들 값을 확인
        f1 = self.lineEdit.text()
        f2 = self.lineEdit_2.text()
        f3 = self.lineEdit_3.text()
        f4 = self.lineEdit_4.text()

        # 파일 목록 확인
        if '.xls' not in f1 or f1 == 0:
            QMessageBox.about(self, "경고", "한전 복지감면 파일을 추가하세요")
            return
        
        if '.xls' not in f2 or f2 == 0:
            QMessageBox.about(self, "경고", "한전 감면 종류 파일을 추가하세요")
            return

        if '.xls' not in f3 or f3 == 0:
            QMessageBox.about(self, "경고", "Template File을 추가하세요")
            return

        # 저장 경로 확인
        if f4 == 0:
            QMessageBox.about(self, "경고", "저장 경로를 선택하세요")
            return

        df2 = welfare_calc(f1)
        subset_df = kind_calc(f2)
        subset_df_w = subset_df[0]
        subset_df_f = subset_df[1]

        discount = discount_file(f3,df2,subset_df_w,subset_df_f)
        pd_save(discount[0],f4)
        print('Total 사용량 보장공제액  :',discount[1])
        print('Total 대가족 할인 공제액 :',discount[2])
        print('Total 복지 할인 공제액   :',discount[3])
        
        return
    def welfare_calc(self, f1):
        df = pd.read_excel(f1,skiprows=2)#, dtype={'동':int, '호':int}) #,thousands=',')
        df_col_names = df.columns.tolist()

        used_col_names = ['동', '호', '동호명', '가구수', '계약\n종별', '요금적용\n전력', '사용량', '기본요금', '전력량\n요금', 
            '기후환경\n요금', '연료비조정\n요금', '필수사용\n공제', '복지추가\n감액', '할인\n구분', '복지할인', '요금개편\n차액', 
            '절전할인', '자동이체\n/인터넷', '단수', '전기요금', '부가세', '전력\n기금', '전기\n바우처', '정산', '출산가구소급', 
            '당월소계', 'TV수신료', '청구금액']

        print(df_col_names)

        for col in df_col_names:
            temp_length = 0
            used_length = len(used_col_names)
            kind_length = len(df_col_names)
            for used_col in used_col_names:
                if col == used_col:
                    pass
                else:
                    temp_length += 1
                    if temp_length == used_length:
                        try:
                            msgbox.askyesno("고지서 목차 '"+ col + "' 항목이 추가 되었습니다.",  "항목확인 후 프로그램 조정하세요. Really Quit?")
                            if msgbox == 'yes':
                                root.destroy()
                            else:
                                pass
                        except:
                            pass
        print(df)
        df.rename(columns = {'필수사용\n공제':'필수사용공제'},inplace=True)
        df.rename(columns = {'복지추가\n감액':'복지추가 감액' },inplace=True)

        df_col_names = df.columns.tolist()
        print(df_col_names[4])
        '''
        new_col_names = ['동', '호', '동호명', '가구수', '계약종별', '요금적용전력', '사용량', '기본요금', '전력량요금',
        '기후환경요금','연료비조정액', '필수사용공제', '복지추가 감액', '할인구분', '복지할인', '요금개편차액',
        '절전할인', '자동이체인터넷', '단수', '전기요금', '부가세', '전력기금', '전기바우처', '정산',
        '출산가구소급', '당월소계', 'TV수신료','청구금액']


        try:
            df.columns = new_col_names
        except:
            msgbox.showwarning("경고", f1 + "파일 한전 항목이 변경 되었습니다. 항목확인 후 프로그램 조정하세요.")
        '''

        sum_column = df['필수사용공제'] + df['복지추가 감액']
        df['sum'] = sum_column
        df.rename(columns = {'필수사용공제':'O_필수사용공제'},inplace=True)
        df.rename(columns = {'sum':'필수사용공제'},inplace=True)

        df1 = df.dropna(subset=['동','필수사용공제'])
        # Template Columns중에서 필수 Columns만 복사하여 DataFrame 생성용 Columns list 생성
        df2col =['동','호', '필수사용공제']
        # df2 DataFrame columns중에서 dtype float를 int로 바꿀 Columns list 생성
        df2col_f =['동','호', '필수사용공제']
        # SettingWithCopyWarning Error 방지를 위하여 copy() method적용
        df2 = df1[df2col].copy()
        df2[df2col_f] = df2[df2col_f].astype('int')
        return df2




'''
        if kind == 'welfare':
            self.lineEdit.setText(fname[0])
            return self.lineEdit.text()

        elif kind == 'kind':
            txt_kind_welfare_path.delete(0,END)
            txt_kind_welfare_path.insert(0, files)
            return txt_kind_welfare_path

        else:
            txt_template_path.delete(0,END)
            txt_template_path.insert(0, files)
            return txt_template_path   
'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()