#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdbool.h> 
// #include <rnn.h>

int message_counter = 0;
int fd, nread;
const char *pipe_file = "esc1_data";

char buf[0x100];
float data[5][6];
int front_pointer = 0;
char *pt;

int data_counter = 0;
bool new_data = 0;

void read_data()
{
    memset(buf, 0, 100);
    nread = read(fd, buf, 0x100-1);
    if (!(nread <= 0))
    {
        pt = strtok (buf,",");
        while (pt != NULL) {
            data[front_pointer][data_counter] = atof(pt);
            data_counter++;
            pt = strtok (NULL, ",");
        }
        data_counter = 0;
        printf("%d ", message_counter);
        for(int i = 0; i < 6; i++)
        {
            printf("%f,", data[front_pointer][i]);
        }
        printf("\n");
        message_counter++;
        front_pointer++;
        if (front_pointer == 5)
        {
            front_pointer = 0;
        }
    }
    new_data = 1;
}


int main(int argc, char **argv)
{
    if ((fd = open(pipe_file, O_RDONLY)) < 0)
    {
        fprintf(stderr, "%s: Failed to open FIFO %s\n", argv[argc-argc], pipe_file);
        return 1;
    }

    while(1) {
        read_data();
        if(new_data)
        {
            rnn(front_pointer, data);
            new_data = 0;
        }
    }
    return 0;
}
