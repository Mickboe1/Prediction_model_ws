#include <rnn.h>
#include <selu.h>
#include <stdio.h>
#include <time.h>

float rnn_states[SIZE_RNN_LAYER] = {0};
float rnn_out[SIZE_RNN_LAYER] = {0};
float out[SIZE_OUT] = {0};

void rnn(int front_pointer, float (*data) [6]) {
  for(int i_rnn_state = 0; i_rnn_state < SIZE_INP; i_rnn_state++)
  {
    rnn_states[i_rnn_state] = 0;
    rnn_out[i_rnn_state] = 0;
  }
  clock_t start, end;
  double cpu_time_used;
  
  start = clock();
  for (int i_states = 0; i_states < SIZE_RNN_LAYER; i_states++)
  {
    rnn_states[i_states] = 0;
  }
  for(int i_sample = 0; i_sample < N_TIME_SAMPLES; i_sample++)
  {
    for(int i_rnn_out = 0; i_rnn_out < SIZE_RNN_LAYER; i_rnn_out++)
    {
      float out_sum = 0;
      // input * input_weights 
      for(int i_inp = 0; i_inp < SIZE_INP; i_inp++)
      {
        int sample_index_shifted = i_sample + front_pointer;
        if (sample_index_shifted > N_TIME_SAMPLES -1)
        {
          sample_index_shifted -= N_TIME_SAMPLES;
        } 
        out_sum += data[sample_index_shifted][i_inp] * iw[i_rnn_out + i_inp*SIZE_RNN_LAYER];
      }

      // state * feedback weights
      for(int i_rnn_state = 0; i_rnn_state < SIZE_RNN_LAYER; i_rnn_state++)
      {
        out_sum += rnn_states[i_rnn_state] * rw[i_rnn_state * SIZE_RNN_LAYER + i_rnn_out];
      }

      //activation function
      rnn_out[i_rnn_out] = selu(out_sum + rb[i_rnn_out]);
    }

    // this if statement minimizes processor useage
    if(!(i_sample == N_TIME_SAMPLES - 1)) 
    {
      // set state -> out 
      for(int i_rnn_state = 0; i_rnn_state < SIZE_RNN_LAYER; i_rnn_state++)
      {
        rnn_states[i_rnn_state] = rnn_out[i_rnn_state];
      }
    }
    else
    {
      for(int i_out = 0; i_out < SIZE_OUT; i_out++)
      {
        float out_sum = 0;
        for(int i_rnn_out = 0; i_rnn_out < SIZE_RNN_LAYER; i_rnn_out++)
        {
          out_sum += rnn_out[i_rnn_out] * ow[i_rnn_out * SIZE_OUT + i_out];
        }
        out[i_out] = out_sum + ob[i_out];
      }
    }
  }

  end = clock();
  cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
  printf("time used: %f\n", cpu_time_used);
}