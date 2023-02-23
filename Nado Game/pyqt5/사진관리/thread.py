import logging
import threading
import time

# 스레드 실행 함수
def thread_func(name, d):
    logging.info("Sub-Thread: %s starting", name)
    for i in d:
        print(i)# sub thread에서 실행할 작업을 구현해줌   
    logging.info("Sub-Thread: %s finishing", name)


# 메인 영역
if __name__ == "__main__":
    # Loggin format 설정
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, dateformat="%H:%M:%S")
    logging.info("Main-Thread: before creating thread") # 서브 thread가 만들어 지기 전

    # 함수 인자 확인
    x = threading.Thread(target=thread_func, args=('First', range(20000), daemon=True) # 서브 thread 만들어짐 #daemon이라는 옵션을 true로 해주면 daemon thread
    y = threading.Thread(target=thread_func, args=('Second', range(10000), daemon=True) # 서브 thread 만들어짐

    # 생성한 sub thread가 Daemon thread인지 아닌지 확인하려면
    print(x.isDaemon()) 

    logging.info("Main-Thread: before running thread") # 서브 thread가 실행 되기 전

    x.start() # 서브 thread 실행
    y.start()

    logging.info("Main-Thread: wait for the thread to finish") # 서브 thread가 실행 될 때까지 기다림

    logging.info("Main-Thread: all threads are done") # 모든 thread 실행 끝