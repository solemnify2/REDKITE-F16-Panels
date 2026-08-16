#include "usb_names.h"

// USB 장치명: "F16 LEFT CONSOLE" (16자)
// 이 이름을 바꾸면 Windows가 장치를 새로 등록하므로
// BMS/DCS의 조이스틱 바인딩을 다시 잡아야 합니다.
#define PRODUCT_NAME    {'F','1','6',' ','L','E','F','T',' ','C','O','N','S','O','L','E'}
#define PRODUCT_NAME_LEN  16

struct usb_string_descriptor_struct usb_string_product_name = {
  2 + PRODUCT_NAME_LEN * 2,
  3,
  PRODUCT_NAME
};
