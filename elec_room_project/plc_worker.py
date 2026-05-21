import serial
import struct
import time
from db_manager import insert_raw_data, verify_crc

COM_PORT = 'COM3'         
BAUD_RATE = 19200         
MY_SLAVE_ID = 5           
NUM_WORDS = 50            

def serial_receive_thread():
    try:
        ser = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=0.1)
        print(f"통신 엔진 가동 완료: {COM_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print(f"시리얼 포트 개방 실패: {e}")
        return

    buffer = b""
    while True:
        try:
            if ser.in_waiting > 0:
                buffer += ser.read(ser.in_waiting)
                
                while len(buffer) >= 7:
                    if buffer[0] != MY_SLAVE_ID:
                        buffer = buffer[1:]
                        continue
                    
                    func_code = buffer[1]
                    if func_code == 0x10:
                        expected_len = 7 + (NUM_WORDS * 2) + 2 
                        
                        if len(buffer) < expected_len: 
                            break 
                        
                        packet = buffer[:expected_len]
                        
                        if verify_crc(packet):
                            raw_values = packet[7:7+(NUM_WORDS * 2)]
                            
                            # 50개 워드를 각각 안전하게 가져옵니다.
                            raw_words = struct.unpack(f'>{NUM_WORDS}h', raw_values)
                            
                            # KEP_P_mWh 가 위치한 D915, D916 자리 추출
                            word_1 = raw_words[15]   
                            word_2 = raw_words[16]   
                            
                            u_word1 = word_1 if word_1 >= 0 else word_1 + 65536
                            u_word2 = word_2 if word_2 >= 0 else word_2 + 65536
                            
                            # 💡 현장 계측기 값과 상하위 워드 순서 확인용 수식 (반전 필요시 아래 주석 체인지)
                            # dint_mwh = (u_word1 << 16) + u_word2
                            dint_mwh = (u_word2 << 16) + u_word1
                            
                            if dint_mwh & 0x80000000:
                                dint_mwh -= 0x100000000
                                
                            # 2개의 16비트 워드를 1개의 32비트 결합 데이터로 팩킹 후 리스트 재구성
                            values = (
                                list(raw_words[:15]) +    
                                [dint_mwh] +              
                                list(raw_words[17:])      
                            )
                            
                            insert_raw_data(values)
                            buffer = buffer[expected_len:] 
                        else:
                            buffer = buffer[1:]
                    else:
                        buffer = buffer[1:]
            time.sleep(0.01)
        except Exception as e:
            print(f"시리얼 수신 스레드 예외 발생: {e}")
            break