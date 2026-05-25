# database/db_handler.py
import mysql.connector
from config import DB_CONFIG

class DBHandler:
    def __init__(self):
        self.config = DB_CONFIG

    def get_connection(self):
        """MySQL 데이터베이스 커넥션을 생성하여 반환합니다."""
        return mysql.connector.connect(**self.config)

    def select_pictures(self, file_term="", act_term="", check_file_wildcard=False, check_act_wildcard=False):
        """조건에 맞는 사진 데이터를 조회합니다."""
        file_param = f"%{file_term}%" if check_file_wildcard else file_term
        act_param = f"%{act_term}%" if check_act_wildcard else act_term
        
        if not file_term: file_param = '%%'
        if not act_term: act_param = '%%'

        query = """
            SELECT pictureFileName, activityName, fileVolume, makeTime 
            FROM mypicturefiles 
            WHERE pictureFileName LIKE %s AND activityName LIKE %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, (file_param, act_param))
                return cursor.fetchall()

    def insert_picture(self, file_name, activity_name, file_size, make_time):
        """새로운 사진 정보를 DB에 등록합니다. 중복 시 업데이트합니다."""
        query = """
            INSERT INTO mypicturefiles (pictureFileName, activityName, fileVolume, makeTime)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                activityName = VALUES(activityName), 
                fileVolume = VALUES(fileVolume), 
                makeTime = VALUES(makeTime)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (file_name, activity_name, file_size, make_time))
                conn.commit()

    def delete_picture(self, file_name):
        """DB에서 특정 사진 레코드를 삭제합니다."""
        query = "DELETE FROM mypicturefiles WHERE pictureFileName = %s"
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (file_name,))
                conn.commit()

    def search_period(self, start_date, end_date):
        """지정된 기간 내에 촬영된 사진을 조회합니다."""
        query = """
            SELECT pictureFileName, activityName, fileVolume, makeTime 
            FROM mypicturefiles 
            WHERE makeTime BETWEEN %s AND %s
        """
        with self.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, (start_date, end_date))
                return cursor.fetchall()