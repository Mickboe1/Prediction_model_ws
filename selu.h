#include <math.h>

const float alpha = 1.6732632423543772848170429916717;
const float scale = 1.0507009873554804934193349852946;

float selu(float x)
{
  if (x >= 0)
  {
    return scale * x;
  }
  else
  {
    return scale * alpha * (float)(exp(x) - 1);
  }
}