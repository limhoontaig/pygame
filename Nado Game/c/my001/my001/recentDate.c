#include <stdio.h>

int DateToInt(const char a_date_str[])
{
	int date_num = 0;

	for (int i = 0; a_date_str[i]; i++) {
		if (a_date_str[i] != '-') {
			// '-' 문자는 제외하고 a_date_str[i] 문자를 숫자로 변경해서 핪산한다.
			// 그리고 합산하기 전에 date_num에 저장된 값은 10을 곱해서 자릿수를 증가시킨다.
			date_num = date_num * 10 + a_date_str[i] - '0';
			printf("index 는 %d 이고 수는 %d 입니다. \n", i, date_num);
		}
	}
	return date_num;
}

int main()
{

	// 주어진 날짜를 배열에 저장한다.
	char date_list[5][12] = { "2014-05-07", "2015-02-01",
				"2016-09-16", "2013-11-25", "2016-01-07" };
	// 최댓값 항목의 위치를 기억한다.
	int max_index = 0, temp_num;
	// 첫 날짜를 숫자로 변환하고 최댓값으로 기록한다.
	int max = DateToInt(date_list[0]);

	for (int i = 1; i < 5; i++) {
		// 계속 날짜를 숫자로 변환한다.
		temp_num = DateToInt(date_list[i]);
		// 변환된 숫자의 최댓값을 계속 갱신한다.
		if (max < temp_num) {
			max = temp_num;
			max_index = i;
		}
	}

	// 최댓값에 해당하는 날짜가 최근 날짜이다.
	printf("최근날짜 : %s (%d) \n", date_list[max_index], max);
	return 0;
}