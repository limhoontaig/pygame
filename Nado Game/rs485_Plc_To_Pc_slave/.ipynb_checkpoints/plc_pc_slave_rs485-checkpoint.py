import time
import datetime
import pandas as pd
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.payload import convert_from_registers 
# payload BinaryPayloadDecoder
from pymodbus.constants import Endian

# --- 설정 (사용자 환경에 맞게 수정) ---
PORT = 'COM3'          # RS485 컨버터가 연결된 포트
PLC_SLAVE_ID = 1       # PLC에서 설정한 국번
BAUDRATE = 9600        # PLC와 동일하게 설정 (9600, 19200 등)
START_ADDR = 300       # 시작 주소 (D300)
DATA_COUNT = 24        # 읽어올 32비트 데이터 개수 (D300~D323)

def read_plc_real_data():
    # RS485 연결 설정
    client = ModbusClient(method='rtu', port=PORT, baudrate=BAUDRATE, 
                          timeout=1, parity='N', stopbits=1, bytesize=8)
    
    if not client.connect():
        print("PLC 연결 실패")
        return None

    # 32비트 데이터는 2개의 레지스터를 차지하므로 COUNT * 2만큼 읽음
    result = client.read_holding_registers(START_ADDR, DATA_COUNT * 2, slave=PLC_SLAVE_ID)
    
    if result.isError():
        print("데이터 읽기 오류")
        client.close()
        return None

    registers = result.registers
    decoded_values = []

    # 2개 워드를 묶어 32비트 Float(실수)로 변환
    for i in range(0, len(registers), 2):
        # LS PLC의 32비트 데이터 정렬 방식에 따라 wordorder(Endian.LITTLE) 조정 필요할 수 있음
        decoder = convert_from_registers.fromRegisters(
            registers[i:i+2], 
            byteorder=Endian.BIG, 
            wordorder=Endian.LITTLE 
        )
        decoded_values.append(decoder.decode_32bit_float())

    client.close()
    return decoded_values

def main():
    print("데이터 수집 시작 (종료: Ctrl+C)")
    raw_db_file = 'plc_raw_data.csv'
    avg_db_file = 'plc_hourly_average.csv'

    while True:
        try:
            now = datetime.datetime.now()
            data = read_plc_real_data()

            if data:
                # 1분 단위 데이터 구성
                row = {'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')}
                for i, val in enumerate(data):
                    row[f'D{300+i}'] = round(val, 3)

                df_current = pd.DataFrame([row])
                
                # 1. 기본 데이터베이스(CSV) 저장
                df_current.to_csv(raw_db_file, mode='a', index=False, 
                                  header=not pd.io.common.file_exists(raw_db_file))
                print(f"[{now.strftime('%H:%M:%S')}] 데이터 저장 완료")

                # 2. 1시간 평균 데이터 처리 (매시 정각 0분일 때)
                if now.minute == 0:
                    df_all = pd.read_csv(raw_db_file)
                    df_all['timestamp'] = pd.to_datetime(df_all['timestamp'])
                    
                    # 최근 1시간 데이터 필터링
                    one_hour_ago = now - datetime.timedelta(hours=1)
                    hourly_df = df_all[df_all['timestamp'] >= one_hour_ago]
                    
                    if not hourly_df.empty:
                        avg_row = hourly_df.mean(numeric_only=True).to_frame().T
                        avg_row.insert(0, 'timestamp', now.strftime('%Y-%m-%d %H:00:00'))
                        
                        avg_row.to_csv(avg_db_file, mode='a', index=False,
                                       header=not pd.io.common.file_exists(avg_db_file))
                        print(f">>> {now.hour}시 평균 데이터 생성 및 저장 완료")

            # 다음 1분까지 대기 (초 단위를 맞춰서 정확히 실행)
            time.sleep(60 - datetime.datetime.now().second)

        except Exception as e:
            print(f"에러 발생: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
