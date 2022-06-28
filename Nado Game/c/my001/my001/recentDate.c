#include <stdio.h>

int DateToInt(const char a_date_str[])
{
	int date_num = 0;

	for (int i = 0; a_date_str[i]; i++) {
		if (a_date_str[i] != '-') {
			// '-' ���ڴ� �����ϰ� a_date_str[i] ���ڸ� ���ڷ� �����ؼ� �D���Ѵ�.
			// �׸��� �ջ��ϱ� ���� date_num�� ����� ���� 10�� ���ؼ� �ڸ����� ������Ų��.
			date_num = date_num * 10 + a_date_str[i] - '0';
			printf("index �� %d �̰� ���� %d �Դϴ�. \n", i, date_num);
		}
	}
	return date_num;
}

int main()
{

	// �־��� ��¥�� �迭�� �����Ѵ�.
	char date_list[5][12] = { "2014-05-07", "2015-02-01",
				"2016-09-16", "2013-11-25", "2016-01-07" };
	// �ִ� �׸��� ��ġ�� ����Ѵ�.
	int max_index = 0, temp_num;
	// ù ��¥�� ���ڷ� ��ȯ�ϰ� �ִ����� ����Ѵ�.
	int max = DateToInt(date_list[0]);

	for (int i = 1; i < 5; i++) {
		// ��� ��¥�� ���ڷ� ��ȯ�Ѵ�.
		temp_num = DateToInt(date_list[i]);
		// ��ȯ�� ������ �ִ��� ��� �����Ѵ�.
		if (max < temp_num) {
			max = temp_num;
			max_index = i;
		}
	}

	// �ִ񰪿� �ش��ϴ� ��¥�� �ֱ� ��¥�̴�.
	printf("�ֱٳ�¥ : %s (%d) \n", date_list[max_index], max);
	return 0;
}