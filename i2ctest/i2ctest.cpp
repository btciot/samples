#include <iostream>
#include <errno.h>
#include <wiringPiI2C.h>

using namespace std;

int main()
{
	int fd, result;
	fd = wiringPiI2CSetup(0x60);
	for (int i = 0;i<0xffff;i++)
	{
		result = wiringPiI2CWriteReg16(fd, 0x40, (i & 0xfff) );
		if (result == -1)
		{
			cout << "Error. Errno is: "<< errno << endl;
		}
	}
}
